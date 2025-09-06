import streamlit as st
import pandas as pd
import datetime
import os
import io  # ← 追加（Excelバッファ用）

# ---- 簡易パスワード設定 ----
PASSWORD = "0626"  # 好きなパスワードに変更
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
    # 保存先
    save_dir = r"C:\Users\iapoc\OneDrive\Desktop"
    FILE_NAME = os.path.join(save_dir, "kakeibo.xlsx")
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Excelファイル読み込み
    if os.path.exists(FILE_NAME):
        df = pd.read_excel(FILE_NAME)
    else:
        df = pd.DataFrame(columns=["日付", "タイプ", "用途", "金額"])

    # ページ設定
    st.set_page_config(page_title="家計簿アプリ", page_icon="💰", layout="centered")

    # CSSボタン
    st.markdown("""
    <style>
    .stButton>button {
        background-color: #1E90FF;
        color: white;
        font-weight: bold;
        height: 40px;
        width: 100%;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    # タイトル
    st.markdown("<h1 style='color:#1E90FF;'>📒 家計簿アプリ</h1>", unsafe_allow_html=True)

    # 入力エリア
    st.header("収支を入力")
    date = st.date_input("日付", datetime.date.today())
    type_ = st.radio("タイプ", ["支出", "収入"], horizontal=True)

    # 用途切替
    if type_ == "支出":
        categories = ["食費", "交通費", "日用品費", "娯楽費", "美容費", "交際費", "医療費", "その他"]
    else:
        categories = ["給与", "その他"]
    usage = st.selectbox("用途", categories)

    # 金額
    amount = st.number_input("金額", step=100, format="%d")
    if type_ == "支出":
        amount = -abs(amount)

    # 保存
    if st.button("保存"):
        new_data = pd.DataFrame([[date, type_, usage, amount]],
                                columns=["日付", "タイプ", "用途", "金額"])
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(FILE_NAME, index=False)
        st.success("保存しました！")

    # --- 直近1週間の記録を表示 ---
    if not df.empty:
        df['日付'] = pd.to_datetime(df['日付'])
        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
        df_last_week = df[df['日付'] >= pd.Timestamp(one_week_ago)]

        st.header("📊 直近1週間の記録")
        st.dataframe(df_last_week)
    else:
        st.info("まだ記録がありません。")

    # --- Excel ダウンロードボタン ---
    if not df.empty:
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
