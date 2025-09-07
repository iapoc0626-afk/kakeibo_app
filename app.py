import streamlit as st
import pandas as pd
import datetime
import os
import io
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ---- パスワード認証 ----
PASSWORD = "0626"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 非表示行管理
if "hidden_rows" not in st.session_state:
    st.session_state.hidden_rows = []

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

    if type_ == "支出":
        amount = -abs(amount)

    if st.button("保存"):
        new_data = pd.DataFrame([[date.strftime("%Y/%m/%d"), type_, kind, amount]],
                                columns=["日付", "タイプ", "種類", "金額"])
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(FILE_NAME, index=False)
        st.success("保存しました！")

    # --- 直近1週間の表（編集＋非表示可能） ---
    st.header("📊 直近1週間の記録（編集・非表示可能）")
    if not df.empty:
        df["日付"] = pd.to_datetime(df["日付"], errors='coerce')
        df = df[df["日付"].notna()]
        df["日付"] = df["日付"].dt.strftime("%Y/%m/%d")

        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
        df_last_week = df[pd.to_datetime(df["日付"], errors='coerce') >= pd.to_datetime(one_week_ago)].copy().reset_index(drop=True)

        # 非表示行を除外
        if st.session_state.hidden_rows:
            df_last_week = df_last_week.drop(index=[i for i in st.session_state.hidden_rows if i < len(df_last_week)]).reset_index(drop=True)

        if not df_last_week.empty:
            # AgGrid 用 No 列
            df_last_week.index = df_last_week.index
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

            # 行選択用チェックボックス
            gb.configure_selection("multiple", use_checkbox=True)
            grid_options = gb.build()

            grid_response = AgGrid(
                df_last_week,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=True,
                enable_enterprise_modules=False,
                allow_unsafe_jscode=True
            )

            edited_df = pd.DataFrame(grid_response["data"])
            edited_df.index = df_last_week.index
            selected_rows = grid_response["selected_rows"]

            # 更新ボタン
            if st.button("更新"):
                last_week_indices = df[pd.to_datetime(df["日付"], errors='coerce') >= pd.to_datetime(one_week_ago)].index
                for idx, original_idx in enumerate(last_week_indices):
                    if original_idx < len(df):
                        df.loc[original_idx, ["日付", "タイプ", "種類", "金額"]] = edited_df.loc[df_last_week.index[idx], ["日付", "タイプ", "種類", "金額"]]
                df.to_excel(FILE_NAME, index=False)
                st.success("更新しました！")
                st.experimental_rerun()

            # 非表示ボタン
            if st.button("非表示"):
                if selected_rows is not None and len(selected_rows) > 0:
                    for row in selected_rows:
                        node_id = int(row["_selectedRowNodeInfo"]["nodeId"])
                        if node_id not in st.session_state.hidden_rows:
                            st.session_state.hidden_rows.append(node_id)
                    st.experimental_rerun()
                else:
                    st.info("非表示にする行を選択してください。")
        else:
            st.info("直近1週間の記録はありません。")
    else:
        st.info("まだ記録がありません。")

    # Excel ダウンロード（非表示行を除く）
    df_to_download = df.copy()
    if st.session_state.hidden_rows:
        last_week_indices = df[pd.to_datetime(df["日付"], errors='coerce') >= pd.to_datetime(one_week_ago)].index
        drop_idx = [last_week_indices[i] for i in st.session_state.hidden_rows if i < len(last_week_indices)]
        df_to_download = df_to_download.drop(drop_idx)

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df_to_download.to_excel(writer, index=False)
    excel_buffer.seek(0)
    st.download_button(
        label="Excel をダウンロード",
        data=excel_buffer,
        file_name="kakeibo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
