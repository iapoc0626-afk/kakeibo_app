import streamlit as st
import pandas as pd
import datetime
import os
import io  # Excelバッファ用

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
    # -------- 家計簿アプリ本体 --------
    save_dir = r"C:\Users\iapoc\OneDrive\Desktop"
    FILE_NAME = os.path.join(save_dir, "kakeibo.xlsx")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Excel読み込み
    if os.path.exists(FILE_NAME):
        df = pd.read_excel(FILE_NAME)
    else:
        df = pd.DataFrame(columns=["日付", "タイプ", "用途", "金額"])

    st.set_page_config(page_title="家計簿アプリ", page_icon="💰", layout="centered")

    # タイトル
    st.markdown("<h1 style='color:#1E90FF;'>📒 家計簿アプリ</h1>", unsafe_allow_html=True)

    # 入力エリア
    st.header("収支を入力")
    date = st.date_input("日付", datetime.date.today())
    type_ = st.radio("タイプ", ["支出", "収入"], horizontal=True)
    categories = ["食費", "交通費", "日用品費", "娯楽費", "美容費", "交際費", "医療費", "その他"] if type_=="支出" else ["給与", "その他"]
    usage = st.selectbox("用途", categories)
    amount = st.number_input("金額", step=100, format="%d")
    if type_=="支出":
        amount = -abs(amount)

    if st.button("保存"):
        new_data = pd.DataFrame([[date, type_, usage, amount]], columns=["日付","タイプ","用途","金額"])
        df = pd.concat([df, new_data], ignore_index=True)
        with pd.ExcelWriter(FILE_NAME, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        st.success("保存しました！")

    # --- 直近1週間の編集可能表 ---
    st.header("📊 直近1週間の記録（編集可能）")
    if not df.empty:
        df['日付'] = pd.to_datetime(df['日付']).dt.date  # 日付のみ表示
        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
        df_last_week = df[df['日付'] >= one_week_ago].copy()

        # 編集用に行番号を1スタートに
        df_last_week.reset_index(drop=True, inplace=True)

        # タイプ・用途・金額を編集可能にする
        edited_rows = []
        for i, row in df_last_week.iterrows():
            st.markdown(f"### 行 {i+1}")
            edit_date = st.date_input("日付", row['日付'], key=f"date_{i}")
            edit_type = st.selectbox("タイプ", ["支出","収入"], index=0 if row['タイプ']=="支出" else 1, key=f"type_{i}")
            edit_usage_list = ["食費", "交通費", "日用品費", "娯楽費", "美容費", "交際費", "医療費", "その他"] if edit_type=="支出" else ["給与","その他"]
            edit_usage = st.selectbox("用途", edit_usage_list, index=edit_usage_list.index(row['用途']), key=f"usage_{i}")
            edit_amount = st.number_input("金額", value=int(abs(row['金額'])), step=100, key=f"amount_{i}")
            if edit_type=="支出":
                edit_amount = -abs(edit_amount)
            edited_rows.append([edit_date, edit_type, edit_usage, edit_amount])

        # 保存ボタン
        if st.button("更新"):
            for idx, values in enumerate(edited_rows):
                df_last_week.loc[idx, ['日付','タイプ','用途','金額']] = values
            # 元のdfの対応行を更新
            for idx, original_idx in enumerate(df[df['日付'] >= one_week_ago].index):
                df.loc[original_idx, ['日付','タイプ','用途','金額']] = df_last_week.loc[idx]
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
        st.info("まだ記録がありません。")
