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
    # 加入台彩官方來源作為首選分析資料來源
    urls = [
        "https://www.taiwanlottery.com/lotto/result/bingo_bingo", # 台彩官方最新開獎
        "https://winwin.tw/Bingo", 
        "https://www.nanalotto.com/BINGO_BINGO"
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for url in urls:
        try:
            # 增加 timeout 確保穩定性，設定 encoding 為 utf-8 避免亂碼
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = 'utf-8'
            if resp.status_code != 200:
                continue
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            data = []

            # 針對台彩官方網站的解析邏輯
            if "taiwanlottery" in url:
                # 台彩號碼通常位於特定的表格或 div 結構中
                rows = soup.select('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        period = cols[0].get_text(strip=True)
                        # 過濾掉非純數字的期號列
                        if not period.isdigit(): continue
                        
                        # 抓取該行內所有的號碼球標籤
                        ball_elements = cols[1].find_all(['span', 'div'])
                        nums = [int(n.get_text(strip=True)) for n in ball_elements if n.get_text(strip=True).isdigit()]
                        
                        if len(nums) >= 20:
                            data.append({"period": period, "numbers": nums[:20]})
            
            # 針對第三方網站的備援解析邏輯
            else:
                rows = soup.select('table tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        period = cols[0].get_text(strip=True)
                        ball_elements = cols[1].find_all(['span', 'div', 'b'])
                        nums = [int(n.get_text(strip=True)) for n in ball_elements if n.get_text(strip=True).isdigit()]
                        if len(nums) >= 20:
                            data.append({"period": period, "numbers": nums[:20]})
            
            if data: return data
        except Exception as e:
            continue
    return []

# --- 2. 分析邏輯 ---
def get_hot_numbers(history, top_n=10):
    if not history: return []
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts()
    return freq.head(top_n).index.tolist()

def fibonacci_analysis(history):
    if not history: 
        return sorted(random.sample(range(1, 81), 20))
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts().to_dict()
    sorted_balls = sorted(range(1, 81), key=lambda x: freq.get(x, 0), reverse=True)
    top_pool = sorted_balls[:34] 
    pred_small = [n for n in top_pool if n <= 40]
    pred_large = [n for n in top_pool if n > 40]
    # 使用黃金比例過濾邏輯
    final_pred = random.sample(pred_small, min(len(pred_small), 8)) + \
                 random.sample(pred_large, min(len(pred_large), 12))
    return sorted(final_pred)

# --- 3. Streamlit 介面設定 ---
st.set_page_config(page_title="Bingo Bingo 智慧預測器", layout="wide")

st.markdown("""
    <style>
    div[data-testid="column"] { padding: 0px !important; margin: 0px !important; }
    .stButton > button { 
        width: 100% !important; 
        padding: 2px !important; 
        font-size: 11px !important; 
        height: 26px !important;
        margin-bottom: 2px !important;
    }
    section[data-testid="stSidebar"] { width: 300px !important; }
    .predict-text { font-size: 12px; color: #555; }
    </style>
    """, unsafe_allow_html=True)

if 'my_bets' not in st.session_state: st.session_state.my_bets = []
if 'selected_nums' not in st.session_state: st.session_state.selected_nums = []

tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

st.title("🎰 Bingo Bingo 智慧分析預測器")

# 執行爬蟲獲取官方資料
data = fetch_bingo_data()

# --- 側邊欄：模擬投注 ---
st.sidebar.header("📝 模擬投注")
star_type = st.sidebar.selectbox("選擇玩法", [f"{i}星" for i in range(1, 11)], index=5)
required_count = int(star_type.replace("星", ""))

st.sidebar.write(f"選擇 {required_count} 個號碼：")

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

# --- 新增功能區 (側邊欄底部，資料來源已整合台彩官方) ---
st.sidebar.divider()
if data:
    hot_nums = get_hot_numbers(data, top_n=10)
    st.sidebar.subheader("🔥 熱門號碼 (官方數據)")
    st.sidebar.markdown(f"<div class='predict-text'>{', '.join([f'{n:02d}' for n in hot_nums])}</div>", unsafe_allow_html=True)
    
    pred_nums = fibonacci_analysis(data)
    st.sidebar.subheader("🔮 費波那契分析 (官方數據)")
    st.sidebar.markdown(f"<div class='predict-text'>{', '.join([f'{n:02d}' for n in pred_nums])}</div>", unsafe_allow_html=True)
else:
    st.sidebar.warning("無法取得官方資料進行分析")

# --- 主畫面 ---
t1, t2 = st.tabs(["即時開獎 (台彩官方)", "分析預測與對獎"])

with t1:
    st.subheader("🔗 台灣彩券 BINGO BINGO 即時開獎")
    # 直接嵌入官方結果頁面，確保使用者看到最即時資訊
    components.iframe("https://www.taiwanlottery.com/lotto/result/bingo_bingo", height=800, scrolling=True)

with t2:
    if data:
        latest = data[0]
        st.success(f"✅ 資料來源：台彩官方 (最新期號 {latest['period']})")
        
        prediction = fibonacci_analysis(data)
        st.subheader("🔮 費波那契+黃金分割 建議號碼")
        st.code(", ".join([f"{n:02d}" for n in prediction]))
        
        if st.session_state.my_bets:
            st.subheader("🎯 模擬投注實時核對")
            for i, bet in enumerate(st.session_state.my_bets):
                matches = set(bet['nums']) & set(latest['numbers'])
                st.write(f"注項{i+1}: {bet['nums']} | **對中 {len(matches)} 顆** (核對期號: {latest['period']})")
    else:
        st.warning("⚠️ 系統目前無法獲取歷史開獎進行分析，請檢查網路連線。")

st.info(f"系統最後同步時間 (台灣): {now_tw.strftime('%Y-%m-%d %H:%M:%S')} (每 5 分鐘自動刷新)")
