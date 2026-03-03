import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import pytz
import streamlit.components.v1 as components

# --- 1. 爬蟲模組優化 ---
def fetch_bingo_data():
    urls = ["https://winwin.tw/Bingo", "https://www.nanalotto.com/BINGO_BINGO"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # winwin.tw 的結構通常在 table 的 tr 裡
            rows = soup.find_all('tr')
            extracted_data = []
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    period = cols[0].get_text(strip=True)
                    # 抓取包含號碼的標籤 (winwin 常用 span class='nb' 或 'ball_blue')
                    balls = cols[1].find_all(['span', 'div'])
                    nums = [int(b.get_text(strip=True)) for b in balls if b.get_text(strip=True).isdigit()]
                    
                    if len(nums) >= 20:
                        extracted_data.append({"period": period, "numbers": nums[:20]})
            
            if extracted_data:
                return extracted_data
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
    final_pred = random.sample(pred_small, min(len(pred_small), 8)) + \
                 random.sample(pred_large, min(len(pred_large), 12))
    return sorted(final_pred)

# --- 3. Streamlit 介面設定 ---
st.set_page_config(page_title="Bingo Bingo 智慧分析預測器", layout="wide")

# 強化的 CSS：美化選號按鈕
st.markdown("""
    <style>
    /* 側邊欄容器調整 */
    section[data-testid="stSidebar"] > div:first-child {
        width: 350px !important;
        padding-top: 20px;
    }
    
    /* 選號按鈕樣式 */
    .stButton > button {
        width: 100% !important;
        height: 45px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        margin-bottom: 5px !important;
        border: 1px solid #ddd !important;
    }
    
    /* 已選擇按鈕的顏色 (深藍色) */
    div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background-color: #1E3A8A !important;
        color: white !important;
        border: none !important;
    }

    /* 預測區文字 */
    .predict-text { font-size: 14px; color: #1f2937; background: #f3f4f6; padding: 10px; border-radius: 8px; border-left: 5px solid #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

if 'my_bets' not in st.session_state: st.session_state.my_bets = []
if 'selected_nums' not in st.session_state: st.session_state.selected_nums = []

tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

st.title("🎰 Bingo Bingo 智慧分析預測器")

# 獲取資料
data = fetch_bingo_data()

# --- 側邊欄：美化選號系統 ---
st.sidebar.header("📝 模擬投注")
star_type = st.sidebar.selectbox("選擇玩法", [f"{i}星" for i in range(1, 11)], index=5)
required_count = int(star_type.replace("星", ""))

st.sidebar.markdown(f"**請點擊下方號碼選擇 {required_count} 個：**")

# 改成 5 列顯示，按鈕更大更好按
for row in range(16): # 16列 * 5個 = 80個
    cols = st.sidebar.columns(5)
    for col in range(5):
        num = row * 5 + col + 1
        if num <= 80:
            is_selected = num in st.session_state.selected_nums
            btn_type = "primary" if is_selected else "secondary"
            if cols[col].button(f"{num:02d}", key=f"num_{num}", type=btn_type):
                if num in st.session_state.selected_nums:
                    st.session_state.selected_nums.remove(num)
                elif len(st.session_state.selected_nums) < required_count:
                    st.session_state.selected_nums.append(num)
                st.rerun()

st.sidebar.markdown("---")
col_bet1, col_bet2 = st.sidebar.columns(2)
if col_bet1.button("🎲 隨機選號"):
    st.session_state.selected_nums = random.sample(range(1, 81), required_count)
    st.rerun()
if col_bet2.button("🧹 清除重選"):
    st.session_state.selected_nums = []
    st.rerun()

st.sidebar.info(f"📍 已選擇: {sorted(st.session_state.selected_nums)}")

if st.sidebar.button("➕ 加入投注清單"):
    if len(st.session_state.selected_nums) == required_count:
        st.session_state.my_bets.append({
            "type": star_type,
            "nums": sorted(st.session_state.selected_nums),
            "time": now_tw.strftime("%H:%M:%S"),
            "period": data[0]['period'] if data else "待同步"
        })
        st.session_state.selected_nums = []
        st.sidebar.success("成功加入！")
        st.rerun()
    else:
        st.sidebar.error(f"需選滿 {required_count} 個")

if st.sidebar.button("🗑️ 清空所有投注"):
    st.session_state.my_bets = []
    st.rerun()

# 側邊欄分析區
st.sidebar.divider()
if data:
    st.sidebar.subheader("🔥 熱門號碼")
    st.sidebar.markdown(f"<div class='predict-text'>{', '.join([f'{n:02d}' for n in get_hot_numbers(data)])}</div>", unsafe_allow_html=True)
    st.sidebar.subheader("🔮 費波那契預測")
    st.sidebar.markdown(f"<div class='predict-text'>{', '.join([f'{n:02d}' for n in fibonacci_analysis(data)])}</div>", unsafe_allow_html=True)

# --- 主畫面 ---
t1, t2 = st.tabs(["即時開獎 (同步官方)", "預測分析與對獎"])

with t1:
    st.subheader("🔗 winwin.tw 即時開獎看板")
    components.iframe("https://winwin.tw/Bingo", height=700, scrolling=True)

with t2:
    if data:
        latest = data[0]
        st.success(f"✅ 資料已同步：最新期號 {latest['period']}")
        
        # 顯示最新號碼球
        st.write("最新開獎號碼：")
        ball_html = "".join([f'<span style="background-color:#1E3A8A; color:white; border-radius:50%; padding:5px 10px; margin:2px; display:inline-block; font-weight:bold;">{n:02d}</span>' for n in latest['numbers']])
        st.markdown(ball_html, unsafe_allow_html=True)

        if st.session_state.my_bets:
            st.divider()
            st.subheader("🎯 我的模擬投注核對")
            for i, bet in enumerate(st.session_state.my_bets):
                matches = set(bet['nums']) & set(latest['numbers'])
                st.info(f"注項{i+1} ({bet['type']}): {bet['nums']} | 對中 **{len(matches)}** 顆")
    else:
        st.error("⚠️ 無法讀取歷史資料。請確認 GitHub 專案中已有 requirements.txt 並包含 beautifulsoup4。")

st.info(f"最後刷新 (台灣): {now_tw.strftime('%H:%M:%S')}")
