import streamlit as st
import pandas as pd
import datetime
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

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

# --- カテゴリ設定 ---
expense_categories = ["食費", "交通費", "日用品費", "娯楽費", "美容費", "交際費", "医療費", "投資", "その他"]
income_categories = ["給与", "その他"]

# 入力エ
