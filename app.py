import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import pytz
import streamlit.components.v1 as components

# --- 1. 爬蟲與備援模組 (改用更穩定的 Auzo 來源) ---
def fetch_bingo_data():
    # 改用更穩定的數據源，避開 winwin 對伺服器的封鎖
    urls = [
        "https://lotto.auzo.tw/bingobingo.php",
        "https://www.nanalotto.com/BINGO_BINGO"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            data = []

            # 針對 Auzo 網站的解析邏輯
            if "auzo.tw" in url:
                rows = soup.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        period = cols[0].get_text(strip=True)
                        if not period.isdigit(): continue
                        # 抓取包含號碼的球
                        nums = [int(n.get_text(strip=True)) for n in cols[1].find_all(['span', 'div', 'b']) if n.get_text(strip=True).isdigit()]
                        if len(nums) >= 20:
                            data.append({"period": period, "numbers": nums[:20]})
            
            # 備援網站解析
            else:
                rows = soup.select('table tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        period = cols[0].get_text(strip=True)
                        nums = [int(n.get_text(strip=True)) for n in cols[1].find_all(['span', 'div', 'b']) if n.get_text(strip=True).isdigit()]
                        if len(nums) >= 20:
                            data.append({"period": period, "numbers": nums[:20]})
            
            if data: return data
        except:
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
st.set_page_config(page_title="Bingo Bingo 智慧預測器", layout="wide")

# 選號面板極小化 CSS 優化
st.markdown("""
    <style>
    /* 側邊欄寬度與間距壓縮 */
    section[data-testid="stSidebar"] { width: 260px !important; }
    div[data-testid="column"] { padding: 0px !important; margin: 0px !important; }
    
    /* 按鈕極小化：縮小至 1/3 大小 */
    .stButton > button { 
        width: 100% !important; 
        padding: 0px !important; 
        font-size: 10px !important; 
        height: 22px !important;
        line-height: 22px !important;
        margin-bottom: 1px !important;
        min-height: 22px !important;
    }
    
    /* 移除 Streamlit 預設的多餘間距 */
    [data-testid="stHorizontalBlock"] { gap: 1px !important; }
    
    .predict-text { font-size: 11px; color: #555; background: #f0f2f6; padding: 5px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

if 'my_bets' not in st.session_state: st.session_state.my_bets = []
if 'selected_nums' not in st.session_state: st.session_state.selected_nums = []

tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

st.title("🎰 Bingo Bingo 智慧分析預測器")

data = fetch_bingo_data()

# --- 側邊欄：模擬投注 (極小化佈局) ---
st.sidebar.header("📝 模擬投注")
star_type = st.sidebar.selectbox("玩法", [f"{i}星" for i in range(1, 11)], index=5)
required_count = int(star_type.replace("星", ""))

# 10 欄佈局以極大化節省空間
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

st.sidebar.caption(f"已選: {sorted(st.session_state.selected_nums)}")

if st.sidebar.button("➕ 加入投注"):
    if len(st.session_state.selected_nums) == required_count:
        st.session_state.my_bets.append({
            "type": star_type,
            "nums": sorted(st.session_state.selected_nums),
            "time": now_tw.strftime("%H:%M:%S"),
            "period": data[0]['period'] if data else "追蹤中"
        })
        st.session_state.selected_nums = []
        st.rerun()

if st.sidebar.button("🗑️ 全部清空"):
    st.session_state.my_bets = []
    st.rerun()

# --- 功能分析區 (側邊欄底部) ---
st.sidebar.divider()
if data:
    hot_nums = get_hot_numbers(data, top_n=10)
    st.sidebar.write("🔥 熱門號碼")
    st.sidebar.markdown(f"<div class='predict-text'>{', '.join([f'{n:02d}' for n in hot_nums])}</div>", unsafe_allow_html=True)
    
    pred_nums = fibonacci_analysis(data)
    st.sidebar.write("🔮 預測號碼")
    st.sidebar.markdown(f"<div class='predict-text'>{', '.join([f'{n:02d}' for n in pred_nums])}</div>", unsafe_allow_html=True)
else:
    st.sidebar.warning("伺服器端連線受限，請稍後重試")

# --- 主畫面 ---
t1, t2 = st.tabs(["即時看板", "數據分析對獎"])

with t1:
    st.subheader("🔗 實時開獎資訊")
    # Iframe 保留 winwin 供視覺查看，但數據抓取避開它
    components.iframe("https://winwin.tw/Bingo", height=600, scrolling=True)

with t2:
    if data:
        latest = data[0]
        st.success(f"✅ 數據源已對接 (Auzo)：第 {latest['period']} 期")
        
        prediction = fibonacci_analysis(data)
        st.subheader("🔮 下期預測 (20碼)")
        st.code(", ".join([f"{n:02d}" for n in prediction]))
        
        if st.session_state.my_bets:
            st.subheader("🎯 投注對獎")
            for i, bet in enumerate(st.session_state.my_bets):
                matches = set(bet['nums']) & set(latest['numbers'])
                st.write(f"注項{i+1}: {bet['nums']} | **中 {len(matches)} 顆** ({latest['period']}期)")
    else:
        st.error("⚠️ 無法獲取歷史數據進行預測分析。")

st.info(f"最後刷新: {now_tw.strftime('%Y-%m-%d %H:%M:%S')}")
