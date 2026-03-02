import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import pytz
import streamlit.components.v1 as components

# --- 1. 核心：台彩官網爬蟲模組 (參考 TaiwanLotteryCrawler 邏輯) ---
@st.cache_data(ttl=300) # 每 5 分鐘才真正抓一次，避免被台彩封鎖
def fetch_official_bingo():
    try:
        # 台彩 Bingo Bingo 開獎結果頁面
        url = "https://www.taiwanlottery.com.tw/lotto/BINGOBINGO/drawing.aspx"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 尋找開獎資料表格
        data = []
        # 台彩 Bingo 號碼通常位於 class 為 'table_org' 或 'table_gre' 的 tr 內
        rows = soup.select('tr')
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                period = cols[0].get_text(strip=True)
                # 排除非期號的行
                if not period.isdigit(): continue
                
                # 抓取所有球號 (通常在 span 內)
                ball_elements = cols[1].find_all('span')
                nums = [int(n.get_text(strip=True)) for n in ball_elements if n.get_text(strip=True).isdigit()]
                
                if len(nums) >= 20:
                    data.append({"period": period, "numbers": nums[:20]})
        
        return data
    except Exception as e:
        st.sidebar.error(f"台彩連線失敗: {e}")
        return []

# --- 2. 分析邏輯 ---
def get_hot_numbers(history, top_n=10):
    if not history: return []
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts()
    return freq.head(top_n).index.tolist()

def fibonacci_analysis(history):
    if not history: return sorted(random.sample(range(1, 81), 20))
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

# CSS 優化
st.markdown("""
    <style>
    .stButton > button { width: 100% !important; padding: 2px !important; font-size: 11px !important; height: 26px !important; margin-bottom: 1px !important; }
    section[data-testid="stSidebar"] { width: 320px !important; }
    .predict-box { background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'my_bets' not in st.session_state: st.session_state.my_bets = []
if 'selected_nums' not in st.session_state: st.session_state.selected_nums = []

tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

st.title("🎰 Bingo Bingo 智慧分析預測器")

# 優先獲取官方資料
data = fetch_official_bingo()

# --- 側邊欄：模擬投注 ---
st.sidebar.header("📝 模擬投注")
star_type = st.sidebar.selectbox("選擇玩法", [f"{i}星" for i in range(1, 11)], index=5)
required_count = int(star_type.replace("星", ""))

# 1-80號 面板
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

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("🎲 隨機選號"):
    st.session_state.selected_nums = random.sample(range(1, 81), required_count)
    st.rerun()
if col_btn2.button("🧹 清除選號"):
    st.session_state.selected_nums = []
    st.rerun()

if st.sidebar.button("➕ 加入投注清單"):
    if len(st.session_state.selected_nums) == required_count:
        st.session_state.my_bets.append({
            "type": star_type, "nums": sorted(st.session_state.selected_nums),
            "time": now_tw.strftime("%H:%M:%S"),
            "period": data[0]['period'] if data else "追蹤中"
        })
        st.session_state.selected_nums = []
        st.rerun()

if st.sidebar.button("🗑️ 清空所有投注"):
    st.session_state.my_bets = []
    st.rerun()

# --- 新增功能區：統計與預測 (側邊欄底部) ---
st.sidebar.divider()
if data:
    st.sidebar.subheader("🔥 熱門號碼 (前10名)")
    st.sidebar.write(", ".join([f"{n:02d}" for n in get_hot_numbers(data)]))
    
    st.sidebar.subheader("🔮 下期費波那契預測")
    st.sidebar.info(", ".join([f"{n:02d}" for n in fibonacci_analysis(data)]))

# --- 主畫面 ---
t1, t2 = st.tabs(["即時開獎 (官方同步)", "預測分析與對獎"])

with t1:
    st.subheader("🔗 台灣彩券官方即時看板")
    # 內嵌官方開獎網頁，確保資訊絕對正確
    components.iframe("https://www.taiwanlottery.com.tw/lotto/BINGOBINGO/drawing.aspx", height=700, scrolling=True)

with t2:
    if data:
        latest = data[0]
        st.success(f"✅ 已成功串接台彩資料：第 {latest['period']} 期")
        
        if st.session_state.my_bets:
            st.subheader("🎯 模擬投注對獎 (核對最新期號)")
            for i, bet in enumerate(st.session_state.my_bets):
                matches = set(bet['nums']) & set(latest['numbers'])
                st.write(f"注項{i+1} ({bet['type']}): {bet['nums']} | **對中 {len(matches)} 顆**")
        
        st.divider()
        st.subheader("📊 近期開獎數據統計")
        st.dataframe(pd.DataFrame(data).head(10), use_container_width=True)
    else:
        st.warning("⚠️ 無法獲取台彩官方數據，請檢查伺服器連線。")

st.caption(f"最後同步時間 (台灣): {now_tw.strftime('%Y-%m-%d %H:%M:%S')}")
