import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import pytz
import streamlit.components.v1 as components

# --- 1. 爬蟲與備援模組 ---
def fetch_bingo_data():
    # 嘗試多個資料源，增加穩定性
    urls = ["https://winwin.tw/Bingo", "https://www.nanalotto.com/BINGO_BINGO"]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            rows = soup.select('table tr')
            data = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    period = cols[0].get_text(strip=True)
                    ball_elements = cols[1].find_all(['span', 'div', 'b'])
                    nums = [int(n.get_text(strip=True)) for n in ball_elements if n.get_text(strip=True).isdigit()]
                    if len(nums) >= 20:
                        data.append({"period": period, "numbers": nums[:20]})
            if data: return data
        except:
            continue
    return []

# --- 2. 分析邏輯 ---
def fibonacci_analysis(history):
    if not history: 
        # 若抓不到資料，使用隨機模擬熱門號碼
        return sorted(random.sample(range(1, 81), 20))
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts().to_dict()
    sorted_balls = sorted(range(1, 81), key=lambda x: freq.get(x, 0), reverse=True)
    top_pool = sorted_balls[:34] 
    pred_small = [n for n in top_pool if n <= 40]
    pred_large = [n for n in top_pool if n > 40]
    final_pred = random.sample(pred_small, min(len(pred_small), 8)) + \
                 random.sample(pred_large, min(len(pred_large), 12))
    return sorted(final_pred)

# --- 3. Streamlit 介面設定 ---
st.set_page_config(page_title="Bingo Bingo 智慧預測器", layout="wide")

# 自定義 CSS 縮小 1-80 號按鈕與側邊欄間距
st.markdown("""
    <style>
    div[data-testid="column"] { padding: 0px !important; margin: 0px !important; }
    .stButton > button { 
        width: 100% !important; 
        padding: 2px !important; 
        font-size: 12px !important; 
        height: 28px !important;
        margin-bottom: 2px !important;
    }
    section[data-testid="stSidebar"] { width: 300px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'my_bets' not in st.session_state: st.session_state.my_bets = []
if 'selected_nums' not in st.session_state: st.session_state.selected_nums = []

tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

st.title("🎰 Bingo Bingo 智慧分析預測器")

# 獲取資料
data = fetch_bingo_data()

# --- 側邊欄：縮小型模擬投注 ---
st.sidebar.header("📝 模擬投注")
star_type = st.sidebar.selectbox("選擇玩法", [f"{i}星" for i in range(1, 11)], index=5)
required_count = int(star_type.replace("星", ""))

st.sidebar.write(f"選擇 {required_count} 個號碼：")

# 1-80號 縮小面板 (改為 8 列，每列 10 個)
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
if col_bet1.button("🎲 隨機選號"):
    st.session_state.selected_nums = random.sample(range(1, 81), required_count)
    st.rerun()
if col_bet2.button("🧹 清除"):
    st.session_state.selected_nums = []
    st.rerun()

st.sidebar.info(f"已選: {sorted(st.session_state.selected_nums)}")

if st.sidebar.button("➕ 加入投注清單"):
    if len(st.session_state.selected_nums) == required_count:
        st.session_state.my_bets.append({
            "type": star_type,
            "nums": sorted(st.session_state.selected_nums),
            "time": now_tw.strftime("%H:%M:%S"),
            "period_start": data[0]['period'] if data else "追蹤中"
        })
        st.session_state.selected_nums = []
        st.rerun()

if st.sidebar.button("🗑️ 清空所有投注"):
    st.session_state.my_bets = []
    st.rerun()

# --- 主畫面 ---
t1, t2 = st.tabs(["即時開獎 (同步官方)", "預測分析與對獎"])

with t1:
    st.subheader("🔗 winwin.tw 即時開獎看板")
    # 使用 IFrame 直接加載網頁，解決伺服器抓不到資料的問題
    components.iframe("https://winwin.tw/Bingo", height=600, scrolling=True)

with t2:
    if data:
        latest = data[0]
        st.success(f"✅ 資料已同步：最新期號 {latest['period']}")
        
        # 預測區
        prediction = fibonacci_analysis(data)
        st.subheader("🔮 下期費波那契預測 (20碼)")
        st.code(", ".join([f"{n:02d}" for n in prediction]))
        
        # 對獎
        if st.session_state.my_bets:
            st.subheader("🎯 我的模擬投注對獎")
            for i, bet in enumerate(st.session_state.my_bets):
                matches = set(bet['nums']) & set(latest['numbers'])
                st.write(f"注項{i+1}: {bet['nums']} | **對中 {len(matches)} 顆** ({latest['period']}期)")
    else:
        st.warning("⚠️ 預測器目前無法分析歷史資料（伺服器連線受阻），但您仍可查看上方『即時開獎』標籤。")

st.info(f"最後刷新 (台灣): {now_tw.strftime('%Y-%m-%d %H:%M:%S')}")
