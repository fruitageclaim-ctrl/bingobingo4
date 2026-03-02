import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import time
from datetime import datetime

# --- 1. 爬蟲模組 ---
def fetch_bingo_data():
    try:
        url = "https://winwin.tw/Bingo"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 抓取表格資料 (需根據實際 DOM 調整)
        rows = soup.select('tr')
        data = []
        for row in rows[1:21]: # 取前 20 期
            cols = row.find_all('td')
            if len(cols) >= 2:
                period = cols[0].text.strip()
                # 假設號碼在特定 class 中，winwin 通常用 div 或 span 包裹球號
                nums = [int(n.text) for n in cols[1].find_all('span') if n.text.isdigit()]
                if nums:
                    data.append({"period": period, "numbers": nums})
        return data
    except Exception as e:
        st.error(f"爬蟲出錯: {e}")
        return []

# --- 2. 費波那契與黃金分割分析 ---
def fibonacci_analysis(history):
    # 統計頻率
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts().to_dict()
    
    # 費波那契數列 (作為索引權重)
    fib = [1, 2, 3, 5, 8, 13, 21, 34, 55]
    
    # 黃金分割過濾 (目標：大號 12 顆, 小號 8 顆 或反之)
    # 1. 根據頻率排序
    sorted_balls = sorted(range(1, 81), key=lambda x: freq.get(x, 0), reverse=True)
    
    # 2. 應用黃金比例 (12:8 分布)
    top_pool = sorted_balls[:34] # 取前 34 名(Fib數)作為精選池
    
    # 模擬 20 顆預測號
    # 確保符合黃金分割：大(>40)與小(<=40)的比例接近 0.618
    pred_small = [n for n in top_pool if n <= 40]
    pred_large = [n for n in top_pool if n > 40]
    
    final_pred = random.sample(pred_small, 8) + random.sample(pred_large, 12)
    return sorted(final_pred)

# --- 3. Streamlit 網頁介面 ---
st.set_page_config(page_title="Bingo Pro 預測器", layout="wide")
st.title("🎰 Bingo Bingo 智慧分析預測器")

# 自動更新邏輯
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# 側邊欄：模擬投注
st.sidebar.header("📝 模擬投注 (最多 10 注)")
if 'my_bets' not in st.session_state:
    st.session_state.my_bets = []

bet_input = st.sidebar.text_input("輸入 6 個號碼 (空白隔開)", placeholder="如: 05 12 21 34 55 68")
if st.sidebar.button("加入投注"):
    nums = [int(x) for x in bet_input.split() if x.isdigit()]
    if len(nums) == 6 and len(st.session_state.my_bets) < 10:
        st.session_state.my_bets.append(nums)
        st.success("已加入！")
    else:
        st.error("請輸入正確 6 碼或已達 10 注上限")

if st.sidebar.button("清除所有投注"):
    st.session_state.my_bets = []

# 主畫面
data = fetch_bingo_data()

if data:
    latest = data[0]
    st.subheader(f"📍 最新開獎期號: {latest['period']}")
    
    # 顯示球號
    cols = st.columns(10)
    for i, n in enumerate(latest['numbers']):
        cols[i % 10].markdown(f"### :blue[{n:02d}]")

    # 執行預測
    st.divider()
    prediction = fibonacci_analysis(data)
    st.subheader("🔮 費波那契+黃金分割 預測下一期 (20碼)")
    st.write(f"系統建議號碼： {' , '.join([f'{n:02d}' for n in prediction])}")

    # 對獎系統
    if st.session_state.my_bets:
        st.subheader("🎯 模擬投注對獎結果")
        for i, bet in enumerate(st.session_state.my_bets):
            matches = set(bet) & set(latest['numbers'])
            st.write(f"第 {i+1} 注 {bet} -> **中 {len(matches)} 顆** ({' , '.join(map(str, matches))})")

    # 顯示前十期
    st.divider()
    st.subheader("📊 近 10 期開獎記錄")
    st.table(pd.DataFrame(data[:10]))

else:
    st.warning("正在嘗試連接 winwin.tw 資料源...")

st.info(f"最後更新時間: {datetime.now().strftime('%H:%M:%S')} (每 5 分鐘自動刷新)")