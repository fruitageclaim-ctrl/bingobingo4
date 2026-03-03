import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime
import pytz
import streamlit.components.v1 as components
import time

# --- 1. 數據獲取：讀取 GitHub 產出的 JSON ---
def fetch_bingo_data():
    # 這是您的正確路徑，加入隨機參數防止緩存
    JSON_URL = f"https://raw.githubusercontent.com/fruitageclaim-ctrl/bingobingo4/main/bingo_data.json?t={int(time.time())}"
    try:
        resp = requests.get(JSON_URL, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

# --- 2. 費波那契回測分析功能 ---
def fibonacci_analysis(history):
    if not history: 
        return sorted(random.sample(range(1, 81), 20))
    
    # 統計歷史出現頻率
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts().to_dict()
    
    # 按熱門程度排序，取前 34 名 (費波那契數)
    sorted_balls = sorted(range(1, 81), key=lambda x: freq.get(x, 0), reverse=True)
    top_pool = sorted_balls[:34] 
    
    # 比例分配：小號(01-40)挑選 8 碼，大號(41-80)挑選 12 碼
    pred_small = [n for n in top_pool if n <= 40]
    pred_large = [n for n in top_pool if n > 40]
    
    final_pred = random.sample(pred_small, min(len(pred_small), 8)) + \
                 random.sample(pred_large, min(len(pred_large), 12))
    
    # 若不滿 20 碼則隨機補齊
    if len(final_pred) < 20:
        remaining = list(set(range(1, 81)) - set(final_pred))
        final_pred += random.sample(remaining, 20 - len(final_pred))
        
    return sorted(final_pred)

def get_hot_numbers(history, top_n=10):
    if not history: return []
    all_nums = [n for h in history for n in h['numbers']]
    return pd.Series(all_nums).value_counts().head(top_n).index.tolist()

# --- 3. Streamlit 介面設定 ---
st.set_page_config(page_title="Bingo Bingo 智慧預測器", layout="wide")

# CSS 優化：按鈕極小化
st.markdown("""
    <style>
    section[data-testid="stSidebar"] { width: 260px !important; }
    .stButton > button { 
        width: 100% !important; padding: 0px !important; 
        font-size: 10px !important; height: 22px !important;
        margin-bottom: 1px !important;
    }
    [data-testid="stHorizontalBlock"] { gap: 1px !important; }
    .predict-text { font-size: 11px; color: #333; background: #f0f2f6; padding: 5px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

if 'my_bets' not in st.session_state: st.session_state.my_bets = []
if 'selected_nums' not in st.session_state: st.session_state.selected_nums = []

tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

st.title("🎰 Bingo Bingo 智慧分析預測器")

data = fetch_bingo_data()

# --- 側邊欄：模擬投注 (10 欄佈局) ---
st.sidebar.header("📝 模擬投注")
star_type = st.sidebar.selectbox("玩法", [f"{i}星" for i in range(1, 11)], index=5)
required_count = int(star_type.replace("星", ""))

for row in range(8):
    cols = st.sidebar.columns(10)
    for col in range(10):
        num = row * 10 + col + 1
        is_selected = num in st.session_state.selected_nums
        if cols[col].button(f"{num:02d}", key=f"btn_{num}", type="primary" if is_selected else "secondary"):
            if num in st.session_state.selected_nums:
                st.session_state.selected_nums.remove(num)
            elif len(st.session_state.selected_nums) < required_count:
                st.session_state.selected_nums.append(num)
            st.rerun()

col_bet1, col_bet2 = st.sidebar.columns(2)
if col_bet1.button("🎲 隨機", key="rand"):
    st.session_state.selected_nums = random.sample(range(1, 81), required_count)
    st.rerun()
if col_bet2.button("🧹 清除", key="clear"):
    st.session_state.selected_nums = []
    st.rerun()

if st.sidebar.button("➕ 加入投注清單"):
    if len(st.session_state.selected_nums) == required_count:
        st.session_state.my_bets.append({
            "type": star_type, "nums": sorted(st.session_state.selected_nums),
            "period": data[0]['period'] if data else "追蹤中"
        })
        st.session_state.selected_nums = []
        st.rerun()

# --- 分析摘要區 ---
st.sidebar.divider()
if data:
    st.sidebar.write("🔥 今日熱門碼")
    st.sidebar.markdown(f"<div class='predict-text'>{', '.join([f'{n:02d}' for n in get_hot_numbers(data)])}</div>", unsafe_allow_html=True)
    st.sidebar.write("🔮 費波那契預測")
    st.sidebar.markdown(f"<div class='predict-text'>{', '.join([f'{n:02d}' for n in fibonacci_analysis(data)])}</div>", unsafe_allow_html=True)

# --- 主畫面 ---
t1, t2 = st.tabs(["即時看板", "數據分析對獎"])

with t1:
    # 視覺看板維持 winwin.tw
    components.iframe("https://winwin.tw/Bingo", height=800, scrolling=True)

with t2:
    if data:
        latest = data[0]
        st.success(f"✅ 資料來源：GitHub Actions (同步成功，最新期: {latest['period']})")
        
        prediction = fibonacci_analysis(data)
        st.subheader("🔮 費波那契下期預測 (20碼)")
        st.code(", ".join([f"{n:02d}" for n in prediction]))
        
        if st.session_state.my_bets:
            st.subheader("🎯 模擬對獎 (對比最新期號)")
            for i, bet in enumerate(st.session_state.my_bets):
                matches = set(bet['nums']) & set(latest['numbers'])
                st.write(f"注項{i+1}: {bet['nums']} | **對中 {len(matches)} 顆**")
    else:
        st.error("⚠️ 無法讀取 JSON。請點擊網頁右上角重新整理，或檢查 JSON 連結是否正確。")

st.info(f"最後更新時間: {now_tw.strftime('%Y-%m-%d %H:%M:%S')}")
