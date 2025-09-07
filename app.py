import streamlit as st
import pandas as pd
import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# --- 設定 ---
FILE_NAME = "kakeibo.xlsx"
COLUMNS = ["日付", "タイプ", "種類", "金額"]

# --- 初期化 ---
if "df" not in st.session_state:
    try:
        df = pd.read_excel(FILE_NAME)
        st.session_state.df = df
    except FileNotFoundError:
        df = pd.DataFrame(columns=COLUMNS)
        df.to_excel(FILE_NAME, index=False)
        st.session_state.df = df

df = st.session_state.df

# --- 入力フォーム ---
st.header("家計簿アプリ")

with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("日付", datetime.date.today())
    with col2:
        income_expense = st.selectbox("タイプ", ["収入", "支出"])

    category = st.selectbox("種類", ["食費", "日用品", "交通", "娯楽", "給与", "その他"])
    amount = st.number_input("金額", min_value=0, step=100)

    submitted = st.form_submit_button("追加")

if submitted:
    new_row = pd.DataFrame([[date, income_expense, category, amount]], columns=COLUMNS)
    df = pd.concat([df, new_row], ignore_index=True)
    st.session_state.df = df
    df.to_excel(FILE_NAME, index=False)
    st.success("追加しました！")
    st.rerun()

# --- 直近1週間の表示 ---
st.subheader("直近1週間の記録")
one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
df_last_week = df[pd.to_datetime(df["日付"], errors="coerce") >= pd.to_datetime(one_week_ago)].copy()

# 行番号 No を振る
df_last_week = df_last_week.reset_index(drop=True)
df_last_week.index = df_last_week.index + 1
df_last_week.insert(0, "No", df_last_week.index)

# --- 表の表示 ---
gb = GridOptionsBuilder.from_dataframe(df_last_week)
gb.configure_selection("multiple", use_checkbox=True)
grid_options = gb.build()

grid_response = AgGrid(
    df_last_week,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="alpine",
    fit_columns_on_grid_load=True
)

selected_rows = grid_response["selected_rows"]

# --- 削除機能 ---
if st.button("削除"):
    if selected_rows is not None and len(selected_rows) > 0:
        st.warning(f"選択された {len(selected_rows)} 件を削除しますか？")
        confirm = st.radio(
            "本当に削除しますか？", ["いいえ", "はい"],
            horizontal=True, key="delete_confirm"
        )

        if confirm == "はい":
            # 削除対象の No を抽出
            delete_nos = [int(row["No"]) for row in selected_rows]

            # df_last_week のインデックスを df にマッピング
            last_week_indices = df[
                pd.to_datetime(df["日付"], errors="coerce") >= pd.to_datetime(one_week_ago)
            ].index

            drop_idx = [last_week_indices[no - 1] for no in delete_nos if (no - 1) < len(last_week_indices)]

            # 削除実行
            df = df.drop(drop_idx)

            st.session_state.df = df
            df.to_excel(FILE_NAME, index=False)
            st.success("削除しました！")
            st.rerun()
    else:
        st.info("削除する行を選択してください。")

# --- 合計の表示 ---
st.subheader("直近1週間の集計")
if not df_last_week.empty:
    total_income = df_last_week[df_last_week["タイプ"] == "収入"]["金額"].sum()
    total_expense = df_last_week[df_last_week["タイプ"] == "支出"]["金額"].sum()
    st.metric("収入合計", f"{total_income} 円")
    st.metric("支出合計", f"{total_expense} 円")
else:
    st.write("直近1週間の記録はありません。")
