import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import pytz

# --- 1. 爬蟲模組強化 (解決爬不到資料問題) ---
def fetch_bingo_data():
    try:
        url = "https://winwin.tw/Bingo"
        # 模擬 iPhone 瀏覽器 Header，更容易繞過伺服器擋國外 IP 的機制
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9',
            'Connection': 'keep-alive',
        }
        
        # 增加 timeout 並允許跳過 SSL 驗證
        resp = requests.get(url, headers=headers, timeout=15, verify=True)
        resp.encoding = 'utf-8'
        
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # winwin 的結構通常在 table 裡的 tr
        rows = soup.find_all('tr')
        data = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                # 抓取期號
                period = cols[0].get_text(strip=True)
                if not (period.isdigit() or "期" in period):
                    continue
                
                # 抓取球號：改用 class 模糊搜尋，適應 winwin 的不同樣式 (nb, ball_blue, etc.)
                ball_spans = cols[1].find_all(['span', 'div'])
                nums = []
                for b in ball_spans:
                    txt = b.get_text(strip=True)
                    if txt.isdigit():
                        nums.append(int(txt))
                
                # Bingo 必須是 20 顆球
                if len(nums) >= 20:
                    data.append({
                        "period": period.replace("期", ""), 
                        "numbers": nums[:20]
                    })
        
        return data
    except Exception as e:
        # 發生錯誤時在畫面上印出簡單資訊幫助排查
        st.sidebar.error(f"連線偵錯: {str(e)}")
        return []

# --- 2. 分析邏輯 ---
def fibonacci_analysis(history):
    if not history: return list(range(1, 21))
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts().to_dict()
    sorted_balls = sorted(range(1, 81), key=lambda x: freq.get(x, 0), reverse=True)
    
    # 費波那契精選池
    top_pool = sorted_balls[:34] 
    pred_small = [n for n in top_pool if n <= 40]
    pred_large = [n for n in top_pool if n > 40]
    
    # 黃金比例過濾 (8小 12大)
    s_count = 8 if len(pred_small) >= 8 else len(pred_small)
    l_count = 12 if len(pred_large) >= 12 else len(pred_large)
    
    final_pred = random.sample(pred_small, s_count) + random.sample(pred_large, l_count)
    return sorted(final_pred)

# --- 3. Streamlit 介面設定 ---
st.set_page_config(page_title="Bingo Bingo 智慧分析預測器", layout="wide")

if 'my_bets' not in st.session_state:
    st.session_state.my_bets = []
if 'selected_nums' not in st.session_state:
    st.session_state.selected_nums = []

tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

st.title("🎰 Bingo Bingo 智慧分析預測器")

# 獲取最新資料
data = fetch_bingo_data()

# --- 側邊欄：模擬投注系統 ---
st.sidebar.header("📝 模擬投注系統")

star_type = st.sidebar.selectbox("選擇玩法", [f"{i}星" for i in range(1, 11)], index=5)
required_count = int(star_type.replace("星", ""))

st.sidebar.write(f"請點選 {required_count} 個號碼：")
cols_side = st.sidebar.columns(5)
for i in range(1, 81):
    is_selected = i in st.session_state.selected_nums
    if cols_side[(i-1)%5].button(f"{i:02d}", key=f"btn_{i}", type="primary" if is_selected else "secondary"):
        if i in st.session_state.selected_nums:
            st.session_state.selected_nums.remove(i)
        elif len(st.session_state.selected_nums) < required_count:
            st.session_state.selected_nums.append(i)
        st.rerun()

col_bet1, col_bet2 = st.sidebar.columns(2)
if col_bet1.button("🎲 隨機選號"):
    st.session_state.selected_nums = random.sample(range(1, 81), required_count)
    st.rerun()
if col_bet2.button("🧹 清除選號"):
    st.session_state.selected_nums = []
    st.rerun()

if st.sidebar.button("➕ 加入投注清單"):
    if len(st.session_state.selected_nums) == required_count:
        if len(st.session_state.my_bets) < 10:
            st.session_state.my_bets.append({
                "type": star_type,
                "nums": sorted(st.session_state.selected_nums),
                "time": now_tw.strftime("%H:%M:%S"),
                "period_start": data[0]['period'] if data else "等待開獎"
            })
            st.session_state.selected_nums = []
            st.rerun()
        else:
            st.sidebar.error("上限 10 注")
    else:
        st.sidebar.error(f"需選滿 {required_count} 碼")

if st.sidebar.button("🗑️ 清空所有投注"):
    st.session_state.my_bets = []
    st.rerun()

# --- 主畫面顯示 ---
if data:
    latest = data[0]
    st.subheader(f"📍 最新開獎期號: {latest['period']}")
    
    # 視覺化號碼
    ball_html = "".join([f'<span style="background-color:#1E90FF; color:white; border-radius:50%; padding:8px 12px; margin:4px; display:inline-block; font-weight:bold; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">{n:02d}</span>' for n in latest['numbers']])
    st.markdown(ball_html, unsafe_allow_html=True)

    st.divider()
    prediction = fibonacci_analysis(data)
    st.subheader("🔮 費波那契+黃金分割 預測號碼")
    st.success(f"建議號碼 (20碼)： {', '.join([f'{n:02d}' for n in prediction])}")

    if st.session_state.my_bets:
        st.divider()
        st.subheader("🎯 我的模擬投注 - 即時對獎")
        for i, bet in enumerate(st.session_state.my_bets):
            matches = set(bet['nums']) & set(latest['numbers'])
            color = "#E6F3FF" if not matches else "#FFF0F0"
            st.markdown(f"""
            <div style="background-color:{color}; padding:15px; border-radius:10px; margin-bottom:10px; border:1px solid #ddd;">
                <b>第 {i+1} 注 - {bet['type']}</b> | 投注時間: {bet['time']} | 起始對獎期: {bet['period_start']}<br>
                選號: {', '.join([f'{n:02d}' for n in bet['nums']])}<br>
                <span style="color:red; font-size:1.1em;">本期對中: <b>{len(matches)}</b> 顆</span> ({', '.join(map(str, sorted(list(matches)))) if matches else "槓龜"})
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📊 近 10 期歷史開獎")
    history_df = pd.DataFrame(data[:10])
    history_df['numbers'] = history_df['numbers'].apply(lambda x: ", ".join([f"{n:02d}" for n in x]))
    st.dataframe(history_df, use_container_width=True)
else:
    st.warning("⚠️ 無法取得 winwin.tw 資料。這通常是伺服器防火牆限制。")
    st.info("建議對策：在 Streamlit 右側選單點選 'Reboot App'，或稍候 5 分鐘讓系統更換爬蟲標頭。")

st.write(f"🕒 最後同步時間 (台北): {now_tw.strftime('%Y-%m-%d %H:%M:%S')}")
