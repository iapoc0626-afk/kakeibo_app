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

    # DataFrame をセッションに保持
    if "df" not in st.session_state:
        if os.path.exists(FILE_NAME):
            st.session_state.df = pd.read_excel(FILE_NAME)
        else:
            st.session_state.df = pd.DataFrame(columns=["日付", "タイプ", "種類", "金額"])

    df = st.session_state.df

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
        new_data = pd.DataFrame(
            [[date.strftime("%Y/%m/%d"), type_, kind, amount]],
            columns=["日付", "タイプ", "種類", "金額"]
        )
        df = pd.concat([df, new_data], ignore_index=True)
        st.session_state.df = df
        df.to_excel(FILE_NAME, index=False)
        st.success("保存しました！")
        st.rerun()  # 即時反映

    # --- 直近1週間の表（編集 & 削除対応） ---
    st.header("📊 直近1週間の記録（編集・削除可能）")
    if not df.empty:
        df["日付"] = pd.to_datetime(df["日付"], errors='coerce')
        df = df[df["日付"].notna()]
        df["日付"] = df["日付"].dt.strftime("%Y/%m/%d")
        st.session_state.df = df

        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
        df_last_week = df[pd.to_datetime(df["日付"], errors='coerce') >= pd.to_datetime(one_week_ago)].copy().reset_index(drop=True)

        if not df_last_week.empty:
            df_last_week.index = df_last_week.index + 1
            df_last_week.index.name = "No"

            gb = GridOptionsBuilder.from_dataframe(df_last_week)
            gb.configure_default_column(editable=True)

            # --- 日付をカレンダー入力に ---
            gb.configure_column(
                "日付",
                editable=True,
                cellEditor="agDateCellEditor",
                cellEditorParams={
                    "useFormatter": True,
                    "dateFormat": "yyyy/MM/dd"
                }
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

            # --- チェックボックス選択列を追加 ---
            gb.configure_selection("multiple", use_checkbox=True)

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
                    df.loc[original_idx, ["日付", "タイプ", "種類", "金額"]] = edited_df.loc[df_last_week.index[idx], ["日付", "タイプ", "種類", "金額"]]
                st.session_state.df = df
                df.to_excel(FILE_NAME, index=False)
                st.success("更新しました！")
                st.rerun()  # 即時反映

            # --- 削除機能 ---
            selected_rows = grid_response["selected_rows"]
            if selected_rows:
                st.warning(f"選択された {len(selected_rows)} 件を削除しますか？")
                confirm = st.radio("本当に削除しますか？", ["いいえ", "はい"], horizontal=True)

                if confirm == "はい":
                    delete_nos = [row["No"] for row in selected_rows]
                    df_last_week = df_last_week.drop(delete_nos, errors="ignore")

                    # インデックスを対応付けて削除
                    last_week_indices = df[pd.to_datetime(df["日付"], errors='coerce') >= pd.to_datetime(one_week_ago)].index
                    drop_idx = [last_week_indices[i-1] for i in delete_nos if i-1 < len(last_week_indices)]
                    df = df.drop(drop_idx)

                    st.session_state.df = df
                    df.to_excel(FILE_NAME, index=False)
                    st.success("削除しました！")
                    st.rerun()  # 即時反映
        else:
            st.info("直近1週間の記録はありません。")
    else:
        st.info("まだ記録がありません。")

    # Excel ダウンロード（全記録）
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
