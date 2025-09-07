import streamlit as st
import pandas as pd
import datetime
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

# ---- パスワード認証 ----
PASSWORD = "0626"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("ログイン")
    pwd = st.text_input("パスワードを入力", type="password")
    if st.button("ログイン"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.success("ログイン成功！")
        else:
            st.error("パスワードが違います")
else:
    # 保存先
    save_dir = r"C:\Users\iapoc\OneDrive\Desktop"
    FILE_NAME = os.path.join(save_dir, "kakeibo.xlsx")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Excel読み込み
    if os.path.exists(FILE_NAME):
        df = pd.read_excel(FILE_NAME)
    else:
        df = pd.DataFrame(columns=["日付", "タイプ", "種類", "金額"])

    st.set_page_config(page_title="家計簿アプリ", page_icon="💰", layout="centered")
    st.markdown("<h1 style='color:#1E90FF;'>📒 家計簿アプリ</h1>", unsafe_allow_html=True)

    categories = ["食費","交通費","日用品費","娯楽費","美容費","交際費","医療費","給与","その他"]

    # 入力エリア
    st.header("収支を入力")
    date = st.date_input("日付", datetime.date.today())
    type_ = st.radio("タイプ", ["支出", "収入"], horizontal=True)
    kind = st.selectbox("種類", categories)
    amount = st.number_input("金額", step=100, format="%d")

    # 金額を正の値に統一
    amount = abs(amount)

    if st.button("保存"):
        new_data = pd.DataFrame([[date.strftime("%Y/%m/%d"), type_, kind, amount]],
                                columns=["日付", "タイプ", "種類", "金額"])
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(FILE_NAME, index=False)
        st.success("保存しました！")

    # --- 直近1週間の表（編集のみ） ---
    st.header("📊 直近1週間の記録（編集可能）")
    if not df.empty:
        df["日付"] = pd.to_datetime(df["日付"], errors='coerce')
        df = df[df["日付"].notna()]
        df["日付"] = df["日付"].dt.strftime("%Y/%m/%d")

        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
        df_last_week = df[pd.to_datetime(df["日付"], errors='coerce') >= pd.to_datetime(one_week_ago)].copy().reset_index(drop=True)

        if not df_last_week.empty:
            # AgGrid 用 No 列（表示用）
            df_last_week.index = df_last_week.index + 1
            df_last_week.index.name = "No"

            gb = GridOptionsBuilder.from_dataframe(df_last_week)
            gb.configure_default_column(editable=True)

            # 日付カレンダー編集
            gb.configure_column(
                "日付",
                editable=True,
                cellEditor="agDateCellEditor",
                cellEditorParams={"useFormatter": True},
                valueFormatter="""
                function(params) {
                    if (!params.value) return '';
                    let d = new Date(params.value);
                    if (isNaN(d)) return params.value;
                    let yyyy = d.getFullYear();
                    let mm = ('0' + (d.getMonth()+1)).slice(-2);
                    let dd = ('0' + d.getDate()).slice(-2);
                    return yyyy + '/' + mm + '/' + dd;
                }
                """
            )
            gb.configure_column(
                "タイプ",
                editable=True,
                cellEditor='agSelectCellEditor',
                cellEditorParams={"values": ["支出", "収入"]}
            )
            gb.configure_column(
                "種類",
                editable=True,
                cellEditor='agSelectCellEditor',
                cellEditorParams={"values": categories}
            )
            gb.configure_column("金額", editable=True)

            grid_options = gb.build()

            grid_response = AgGrid(
                df_last_week,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.VALUE_CHANGED,
                fit_columns_on_grid_load=True,
                enable_enterprise_modules=False,
                allow_unsafe_jscode=True
            )

            edited_df = pd.DataFrame(grid_response["data"])
            edited_df.index = df_last_week.index

            # 更新ボタン
            if st.button("更新"):
                last_week_indices = df[pd.to_datetime(df["日付"], errors='coerce') >= pd.to_datetime(one_week_ago)].index
                for idx, original_idx in enumerate(last_week_indices):
                    if original_idx < len(df):
                        edited_amount = abs(edited_df.loc[df_last_week.index[idx], "金額"])
                        df.loc[original_idx, ["日付", "タイプ", "種類", "金額"]] = [
                            edited_df.loc[df_last_week.index[idx], "日付"],
                            edited_df.loc[df_last_week.index[idx], "タイプ"],
                            edited_df.loc[df_last_week.index[idx], "種類"],
                            edited_amount
                        ]
                df.to_excel(FILE_NAME, index=False)
                st.success("更新しました！")

    else:
        st.info("まだ記録がありません。")

    # Excel ダウンロード（テーブル形式）
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    download_filename = f"kakeibo_{today_str}.xlsx"

    # 上書き保存
    df.to_excel(FILE_NAME, index=False)

    # openpyxl でテーブル化
    wb = load_workbook(FILE_NAME)
    ws = wb.active

    # テーブル範囲（ヘッダー含む）
    n_rows = ws.max_row
    n_cols = ws.max_column
    table_ref = f"A1:{chr(64+n_cols)}{n_rows}"

    table = Table(displayName="KakeiboTable", ref=table_ref)

    # スタイル設定
    style = TableStyleInfo(
        name="TableStyleMedium9",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False
    )
    table.tableStyleInfo = style
    ws.add_table(table)
    wb.save(FILE_NAME)

    with open(FILE_NAME, "rb") as f:
        st.download_button(
            label="Excel をダウンロード（テーブル形式）",
            data=f,
            file_name=download_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
