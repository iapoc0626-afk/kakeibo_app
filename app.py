import streamlit as st
import pandas as pd
import datetime
import os
import io

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

    if type_ == "支出":
        amount = -abs(amount)

    if st.button("保存"):
        new_data = pd.DataFrame([[date.strftime("%Y/%m/%d"), type_, kind, amount]], columns=["日付", "タイプ", "種類", "金額"])
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(FILE_NAME, index=False)
        st.success("保存しました！")

    # --- 直近1週間の表（削除ボタン付き） ---
    st.header("📊 直近1週間の記録（削除可能）")
    if not df.empty:
        df["日付"] = pd.to_datetime(df["日付"], errors='coerce')
        df = df[df["日付"].notna()]
        df["日付"] = df["日付"].dt.strftime("%Y/%m/%d")

        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
        df_last_week = df[pd.to_datetime(df["日付"], errors='coerce') >= pd.to_datetime(one_week_ago)].copy().reset_index(drop=True)

        if not df_last_week.empty:
            for idx, row in df_last_week.iterrows():
                st.write(f"**No.{idx+1}**")
                st.write(f"日付: {row['日付']}｜タイプ: {row['タイプ']}｜種類: {row['種類']}｜金額: {row['金額']}")
                if st.button(f"削除 {idx}"):
                    st.session_state["delete_target"] = idx

            # 削除確認ダイアログ
            if "delete_target" in st.session_state:
                st.warning(f"No.{st.session_state['delete_target']+1} の記録を削除します。よろしいですか？")
                confirm = st.radio("削除確認", ["いいえ", "はい"], horizontal=True)
                if confirm == "はい":
                    target_row = df_last_week.loc[st.session_state["delete_target"]]
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
