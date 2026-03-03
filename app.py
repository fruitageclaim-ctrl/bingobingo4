import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime
import pytz
import streamlit.components.v1 as components

# --- 1. 數據連結設定 ---
# 根據您的截圖資訊自動帶入
RAW_JSON_URL = "https://raw.githubusercontent.com/fruitageclaim-ctrl/bingobingo4/main/bingo_data.json"

def fetch_data():
    try:
        resp = requests.get(RAW_JSON_URL, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

# --- 2. 費波那契分析邏輯 (預測下一期 20 碼) ---
def fibonacci_prediction(history):
    if not history:
        return sorted(random.sample(range(1, 81), 20))
    
    # 統計歷史出現頻率
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts().to_dict()
    
    # 根據費波那契權重邏輯選出熱門池 (前 34 名)
    sorted_balls = sorted(range(1, 81), key=lambda x: freq.get(x, 0), reverse=True)
    hot_pool = sorted_balls[:34] 
    
    # 從熱門池中進行分布選碼 (小號 8 個, 大號 12 個)
    pred_small = [n for n in hot_pool if n <= 40]
    pred_large = [n for n in hot_pool if n > 40]
    
    # 確保不會因為資料不足報錯
    s_count = min(len(pred_small), 8)
    l_count = min(len(pred_large), 12)
    
    final_pred = random.sample(pred_small, s_count) + random.sample(pred_large, l_count)
    
    # 若不足 20 碼則補足
    if len(final_pred) < 20:
        remaining = list(set(range(1, 81)) - set(final_pred))
        final_pred += random.sample(remaining, 20 - len(final_pred))
        
    return sorted(final_pred)

# --- 3. 介面與 CSS ---
st.set_page_config(page_title="Bingo Bingo 費波那契預測", layout="wide")

st.markdown("""
    <style>
    section[data-testid="stSidebar"] { width: 220px !important; }
    .stButton > button { 
        height: 20px !important; font-size: 10px !important; 
        padding: 0px !important; margin-bottom: 1px !important;
    }
    [data-testid="stHorizontalBlock"] { gap: 1px !important; }
    .predict-box { background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# 狀態初始化
if 'my_bets' not in st.session_state: st.session_state.my_bets = []
if 'selected_nums' not in st.session_state: st.session_state.selected_nums = []

data = fetch_data()

# --- 側邊欄 ---
st.sidebar.header("📝 模擬投注")
star_type = st.sidebar.selectbox("玩法", [f"{i}星" for i in range(1, 11)], index=5)
required = int(star_type.replace("星", ""))

# 選號面板 (10欄)
for r in range(8):
    cols = st.sidebar.columns(10)
    for c in range(10):
        n = r * 10 + c + 1
        is_sel = n in st.session_state.selected_nums
        if cols[c].button(f"{n:02d}", key=f"b_{n}", type="primary" if is_sel else "secondary"):
            if is_sel: st.session_state.selected_nums.remove(n)
            elif len(st.session_state.selected_nums) < required: st.session_state.selected_nums.append(n)
            st.rerun()

if st.sidebar.button("➕ 加入投注清單"):
    if len(st.session_state.selected_nums) == required:
        st.session_state.my_bets.append({"nums": sorted(st.session_state.selected_nums), "type": star_type})
        st.session_state.selected_nums = []
        st.rerun()

# --- 主畫面 ---
t1, t2 = st.tabs(["數據分析預測", "即時看板瀏覽"])

with t1:
    if data:
        latest = data[0]
        st.subheader(f"📊 歷史數據分析 (最新期號: {latest['period']})")
        
        # 費波那契預測 20 碼
        pred_20 = fibonacci_prediction(data)
        st.markdown("### 🔮 費波那契下一期預測 (20碼建議)")
        st.markdown(f"<div class='predict-box'><b>{' , '.join([f'{n:02d}' for n in pred_20])}</b></div>", unsafe_allow_html=True)
        
        # 對獎邏輯
        if st.session_state.my_bets:
            st.divider()
            st.subheader("🎯 我的投注對獎")
            for i, bet in enumerate(st.session_state.my_bets):
                match = set(bet['nums']) & set(latest['numbers'])
                st.write(f"注項 {i+1} [{bet['type']}]: {bet['nums']} -> **中 {len(match)} 顆**")
    else:
        st.warning("⚠️ 正在等待 GitHub Actions 產生資料檔，請確保 crawler.py 已正確執行。")

with t2:
    components.iframe("https://winwin.tw/Bingo", height=800, scrolling=True)
