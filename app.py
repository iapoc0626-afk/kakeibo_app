import streamlit as st
import pandas as pd
import datetime
import os
import io

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
    if type_ == "支出":_
import streamlit as st
import pandas as pd
import datetime
import os
import io

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

    # Excelファイル読み込み
    if os.path.exists(FILE_NAME):
        df = pd.read_excel(FILE_NAME)
    else:
        df = pd.DataFrame(columns=["日付", "タイプ", "用途", "金額"])

    st.set_page_config(page_title="家計簿アプリ", page_icon="💰", layout="centered")

    st.markdown("""
    <style>
    .stButton>button {ba

