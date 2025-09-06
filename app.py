import streamlit as st
import pandas as pd
import datetime
import os

FILE_NAME = "household_budget.xlsx"

# 初期化
if "delete_target" not in st.session_state:
    st.session_state["delete_target"] = None

# ファイル読み込み
if os.path.exists(FILE_NAME):
    df = pd.read_excel(FILE_NAME)
else:
    df = pd.DataFrame(columns=["日付", "タイプ", "種類", "金額"])

st.title("💰 家計簿アプリ")

# 新規入力フォーム
with st.form("entry_form"):
    st.subheader("📝 新しい記録を追加")
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("日付", value=datetime.date.today())
        expense_type = st.selectbox("タイプ", ["支出", "収入"])
    with col2:
        category = st.text_input("種類")
        amount = st.number_input("金額", min_value=0, step=100)

    submitted = st.form_submit_button("追加")
    if submitted:
        new_data = pd.DataFrame([{
            "日付": date.strftime("%Y/%m/%d"),
            "タイプ": expense_type,
            "種類": category,
            "金額": amount
        }])
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(FILE_NAME, index=False)
        st.success("記録を追加しました。")

# 直近1週間の表示と削除
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
        if st.session_state["delete_target"] is not None:
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
                st.session_state["delete_target"] = None
            elif confirm == "いいえ":
                st.info("削除をキャンセルしました。")
                st.session_state["delete_target"] = None
    else:
        st.info("直近1週間の記録はありません。")
else:
    st.info("記録がまだありません。")

# 全データ表示（オプション）
with st.expander("📂 全データを表示"):
    st.dataframe(df)
