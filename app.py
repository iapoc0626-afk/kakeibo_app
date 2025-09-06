import streamlit as st
import pandas as pd
import datetime
import os
import io
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ---- 簡易パスワード設定 ----
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

    # 入力エリア
    st.header("収支を入力")
    date = st.date_input("日付", datetime.date.today())
    type_ = st.radio("タイプ", ["支出", "収入"], horizontal=True)
    categories = ["食費","交通費","日用品費","娯楽費","美容費","交際費","医療費","その他"] if type_=="支出" else ["給与","その他"]
    usage = st.selectbox("種類", categories)
    amount = st.number_input("金額", step=100, format="%d")
    if type_=="支出":
        amount = -abs(amount)

    if st.button("保存"):
        new_data = pd.DataFrame([[date,type_,usage,amount]], columns=["日付","タイプ","種類","金額"])
        df = pd.concat([df,new_data], ignore_index=True)
        with pd.ExcelWriter(FILE_NAME, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        st.success("保存しました！")

    # --- 直近1週間の表（編集可能） ---
    st.header("📊 直近1週間の記録（編集可能）")
    if not df.empty:
        # 日付列を datetime 型に変換
        df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
        df = df[df['日付'].notna()]

        # 直近1週間のデータのみ
        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
        df['日付'] = df['日付'].dt.date
        df_last_week = df[df['日付'] >= one_week_ago].copy().reset_index(drop=True)

        if not df_last_week.empty:
            # 行番号1スタート
            df_last_week.index = df_last_week.index + 1
            df_last_week.index.name = "No"

            # AgGrid設定
            gb = GridOptionsBuilder.from_dataframe(df_last_week)
            gb.configure_default_column(editable=True)

            # 日付列
            gb.configure_column(
                "日付",
                editable=True,
                cellEditor='agDatePicker',
                valueFormatter="(params.value) ? new Date(params.value).toLocaleDateString('ja-JP') : ''"
            )

            # タイプ列
            gb.configure_column(
                "タイプ",
                editable=True,
                cellEditor='agSelectCellEditor',
                cellEditorParams={"values":["支出","収入"]}
            )

            # 種類列
            gb.configure_column(
                "種類",
                editable=True,
                cellEditor='agSelectCellEditor',
                cellEditorParams={"values":["食費","交通費","日用品費","娯楽費","美容費","交際費","医療費","その他","給与","その他"]}
            )

            # 金額列（カンマ区切り表示）
            gb.configure_column(
                "金額",
                editable=True,
                valueFormatter="(params.value !== undefined) ? params.value.toLocaleString() : ''"
            )

            grid_options = gb.build()

            grid_response = AgGrid(
                df_last_week,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.VALUE_CHANGED,
                fit_columns_on_grid_load=True,
                enable_enterprise_modules=False
            )

            edited_df = pd.DataFrame(grid_response['data'])
            edited_df.index = df_last_week.index  # 元の番号に合わせる

            if st.button("更新"):
                # 元のdfの対応行を更新
                last_week_indices = df[df['日付'] >= one_week_ago].index
                for idx, original_idx in enumerate(last_week_indices):
                    df.loc[original_idx, ['日付','タイプ','種類','金額']] = edited_df.loc[df_last_week.index[idx]]
                with pd.ExcelWriter(FILE_NAME, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False)
                st.success("更新しました！")

            # Excelダウンロード
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            excel_buffer.seek(0)
            st.download_button(
                label="Excel をダウンロード",
                data=excel_buffer,
                file_name="kakeibo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("直近1週間の記録はありません。")
    else:
        st.info("まだ記録がありません。")


