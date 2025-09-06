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

    # Excel読み込み
    if os.path.exists(FILE_NAME):
        df = pd.read_excel(FILE_NAME)
    else:
        df = pd.DataFrame(columns=["日付", "タイプ", "種類", "金額"])

    st.set_page_config(page_title="家計簿アプリ", page_icon="💰", layout="centered")
    st.markdown("<h1 style='color:#1E90FF;'>📒 家計簿アプリ</h1>", unsafe_allow_html=True)

    categories = ["食費","交通費","日用品費","娯楽費","美容費","交際費","医療費","給与","その他"]

    # 入力エリア（変更なし）
    st.header("収支を入力")
    date = st.date_input("日付", datetime.date.today())
    type_ = st.radio("タイプ", ["支出", "収入"], horizontal=True)
    kind = st.selectbox("種類", categories)
    amount = st.number_input("金額", step=100, format="%d")

    if type_ == "支出":
        amount = -abs(amount)

    if st.button("保存"):
        new_data = pd.DataFrame([[date.strftime("%Y/%m/%d"), type_, kind, amount]], columns=["日付", "タイプ", "種類", "金額"])
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(FILE_NAME, index=False)
        st.success("保存しました！")

    # --- 直近1週間の表（AgGrid 表形式＋削除ボタン） ---
    st.header("📊 直近1週間の記録（編集・削除可能）")
    if not df.empty:
        df["日付"] = pd.to_datetime(df["日付"], errors='coerce')
        df = df[df["日付"].notna()]
        df["日付"] = df["日付"].dt.strftime("%Y/%m/%d")

        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
        df_last_week = df[pd.to_datetime(df["日付"], errors='coerce') >= pd.to_datetime(one_week_ago)].copy().reset_index(drop=True)

        if not df_last_week.empty:
            df_last_week.index = df_last_week.index + 1
            df_last_week.index.name = "No"

            gb = GridOptionsBuilder.from_dataframe(df_last_week)
            gb.configure_default_column(editable=True)

            gb.configure_column(
                "日付",
                editable=True,
                cellEditor='agTextCellEditor',
                valueFormatter="""
                function(params) {
                    try {
                        let d = new Date(params.value);
                        if (isNaN(d)) return params.value;
                        let yyyy = d.getFullYear();
                        let mm = ('0' + (d.getMonth()+1)).slice(-2);
                        let dd = ('0' + d.getDate()).slice(-2);
                        return yyyy + '/' + mm + '/' + dd;
                    } catch {
                        return params.value;
                    }
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
                    df.loc[original_idx, ["日付", "タイプ", "種類", "金額"]] = edited_df.loc[df_last_week.index[idx], ["日付", "タイプ", "種類", "金額"]]
                df.to_excel(FILE_NAME, index=False)
                st.success("更新しました！")

            # 各行に削除ボタンを表示
            st.subheader("🗑️ 行ごとの削除")
            for idx, row in edited_df.iterrows():
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.write(f"**No.{idx}** 日付: {row['日付']}｜タイプ: {row['タイプ']}｜種類: {row['種類']}｜金額: {row['金額']}")
                with col2:
                    if st.button(f"削除 {idx}"):
                        st.session_state["delete_target"] = idx

            # 削除確認ダイアログ
            if "delete_target" in st.session_state:
                st.warning(f"No.{st.session_state['delete_target']} の記録を削除します。よろしいですか？")
                confirm = st.radio("削除確認", ["いいえ", "はい"], horizontal=True)
                if confirm == "はい":
                    target_row = edited_df.loc[st.session_state["delete_target"]]
                    mask = (
                        (df["日付"] == target_row["日付"]) &
                        (df["タイプ"] == target_row["タイプ"]) &
                        (df["種類"] == target_row["種類"]) &
                        (df["金額"] == target_row["金額"])
                    )
                    df = df[~mask]
                    df.to_excel(FILE_NAME, index=False)
                    st.success("削除しました。")
                    del st.session_state["delete_target"]
                elif confirm == "いいえ":
                    st.info("削除をキャンセルしました。")
                    del st.session_state["delete_target"]
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
