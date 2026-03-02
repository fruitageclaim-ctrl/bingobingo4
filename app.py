import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import pytz

# 設定台灣時區
tw_tz = pytz.timezone('Asia/Taipei')

# --- 1. 爬蟲模組 ---
def fetch_bingo_data():
    try:
        url = "https://winwin.tw/Bingo"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 修正後的抓取邏輯：針對 winwin.tw 結構
        rows = soup.select('tr')
        data = []
        for row in rows:
            tds = row.find_all('td')
            if len(tds) >= 2:
                period = tds[0].get_text(strip=True)
                # 抓取包含開獎球號的 span
                balls = [int(s.text) for s in tds[1].select('span.ball_orange, span.ball_blue') if s.text.isdigit()]
                if len(balls) >= 20:
                    data.append({"period": period, "numbers": balls[:20]})
        return data
    except Exception as e:
        return None

# --- 2. 費波那契預測邏輯 ---
def predict_next(history):
    if not history: return random.sample(range(1, 81), 20)
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts().to_dict()
    sorted_balls = sorted(range(1, 81), key=lambda x: freq.get(x, 0), reverse=True)
    
    # 黃金比例過濾 (大號 12, 小號 8)
    top_pool = sorted_balls[:34] 
    pred_small = [n for n in top_pool if n <= 40]
    pred_large = [n for n in top_pool if n > 40]
    
    final_pred = random.sample(pred_small, min(len(pred_small), 8)) + \
                 random.sample(pred_large, min(len(pred_large), 12))
    return sorted(final_pred)

# --- 3. Streamlit 介面 ---
st.set_page_config(page_title="Bingo Pro 智慧預測", layout="wide")

# 初始化 Session State
if 'my_bets' not in st.session_state: st.session_state.my_bets = []
if 'selected_nums' not in st.session_state: st.session_state.selected_nums = []

st.title("🎰 BINGO BINGO 智慧分析預測器")

# 獲取資料
data = fetch_bingo_data()
now_tw = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')

# 左側側邊欄：投注設定
with st.sidebar:
    st.header("📝 模擬投注設定")
    star_type = st.selectbox("選擇星等", options=range(1, 11), index=5, help="決定你需要選幾個號碼")
    
    st.write(f"已選擇 ({len(st.session_state.selected_nums)}/{star_type})")
    
    # 號碼選擇小面板 (1-80)
    cols = st.columns(8)
    for i in range(1, 81):
        btn_type = "primary" if i in st.session_state.selected_nums else "secondary"
        if cols[(i-1)%8].button(f"{i:02}", key=f"btn_{i}"):
            if i in st.session_state.selected_nums:
                st.session_state.selected_nums.remove(i)
            elif len(st.session_state.selected_nums) < star_type:
                st.session_state.selected_nums.append(i)
            st.rerun()

    if st.button("🎲 隨機產生", use_container_width=True):
        st.session_state.selected_nums = random.sample(range(1, 81), star_type)
        st.rerun()

    if st.button("➕ 加入投注清單", variant="primary", use_container_width=True):
        if len(st.session_state.selected_nums) == star_type:
            if len(st.session_state.my_bets) < 10:
                st.session_state.my_bets.append({"star": star_type, "nums": sorted(st.session_state.selected_nums)})
                st.session_state.selected_nums = []
                st.success("成功加入！")
                st.rerun()
            else: st.error("最多 10 注！")
        else: st.error(f"請選滿 {star_type} 個號碼")

    if st.button("🗑️ 清空所有投注", use_container_width=True):
        st.session_state.my_bets = []
        st.rerun()

# 主畫面內容
if data:
    latest = data[0]
    st.success(f"✅ 資料已同步 | 最新期號: {latest['period']} | 台灣時間: {now_tw}")
    
    # 顯示最新號碼
    ball_html = "".join([f'<span style="background-color:#1E90FF; color:white; border-radius:50%; width:35px; height:35px; display:inline-flex; align-items:center; justify-content:center; margin:3px; font-weight:bold;">{n:02d}</span>' for n in latest['numbers']])
    st.markdown(ball_html, unsafe_allow_html=True)

    # 顯示預測
    pred_nums = predict_next(data)
    st.info(f"🔮 智慧預測下一期建議號碼：{', '.join([f'{n:02d}' for n in pred_nums])}")

    # 顯示投注清單 (解決你看不到投注號碼的問題)
    if st.session_state.my_bets:
        st.subheader("📋 我的模擬投注清單")
        for i, b in enumerate(st.session_state.my_bets):
            matches = set(b['nums']) & set(latest['numbers'])
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"第 {i+1} 注 ({b['star']}星): {' '.join([f'{n:02d}' for n in b['nums']])}")
            with col2:
                st.markdown(f"**中 {len(matches)} 顆**" if len(matches)>0 else "未中獎")
    
    # 歷史紀錄表格
    st.divider()
    st.subheader("📊 最近十期開獎紀錄")
    df_history = pd.DataFrame(data[:10])
    st.table(df_history)

else:
    st.warning("⚠️ 無法連線至開獎來源，請檢查網路或稍後再試。")
    if st.button("重新嘗試連接"): st.rerun()
