import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import pytz

# --- 1. 爬蟲模組優化 ---
def fetch_bingo_data():
    try:
        url = "https://winwin.tw/Bingo"
        # 模擬更真實的瀏覽器標頭，避免被封鎖
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/'
        }
        
        # 加入 verify=False (若遇到 SSL 憑證問題) 並縮短超時
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 修正：精準定位表格行數
        rows = soup.find_all('tr')
        data = []
        
        for row in rows:
            cols = row.find_all('td')
            # 確保欄位包含期號與號碼區塊
            if len(cols) >= 2:
                period = cols[0].get_text(strip=True)
                # 排除標題列或非期號字串
                if not period.isdigit() and "期" not in period:
                    continue
                
                # 抓取所有數字標籤，winwin 目前多用 class="nb" 或 "ball_blue"
                balls = cols[1].find_all(['span', 'div'])
                nums = []
                for b in balls:
                    txt = b.get_text(strip=True)
                    if txt.isdigit():
                        nums.append(int(txt))
                
                # Bingo Bingo 固定 20 個號碼
                if len(nums) >= 20:
                    data.append({"period": period, "numbers": nums[:20]})
                    
        return data
    except Exception as e:
        print(f"DEBUG: 爬蟲發生錯誤: {e}") # 僅供後台查看
        return []

# --- 2. 分析邏輯 ---
def fibonacci_analysis(history):
    if not history: return list(range(1, 21))
    all_nums = [n for h in history for n in h['numbers']]
    freq = pd.Series(all_nums).value_counts().to_dict()
    sorted_balls = sorted(range(1, 81), key=lambda x: freq.get(x, 0), reverse=True)
    top_pool = sorted_balls[:34] 
    pred_small = [n for n in top_pool if n <= 40]
    pred_large = [n for n in top_pool if n > 40]
    # 黃金比例：約 8 顆小號, 12 顆大號
    final_pred = random.sample(pred_small, min(len(pred_small), 8)) + \
                 random.sample(pred_large, min(len(pred_large), 12))
    return sorted(final_pred)

# --- 3. Streamlit 介面設定 ---
st.set_page_config(page_title="Bingo Bingo 智慧分析預測器", layout="wide")

# 初始化 Session State
if 'my_bets' not in st.session_state:
    st.session_state.my_bets = []
if 'selected_nums' not in st.session_state:
    st.session_state.selected_nums = []

# 時區設定
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

st.title("🎰 Bingo Bingo 智慧分析預測器")

# 獲取最新資料
data = fetch_bingo_data()

# --- 側邊欄：模擬投注系統 ---
st.sidebar.header("📝 模擬投注系統")

# A. 選擇玩法
star_type = st.sidebar.selectbox("選擇玩法", [f"{i}星" for i in range(1, 11)], index=5)
required_count = int(star_type.replace("星", ""))

# B. 號碼選擇面板
st.sidebar.write(f"請選擇 {required_count} 個號碼：")
cols = st.sidebar.columns(5)
for i in range(1, 81):
    btn_label = f"{i:02d}"
    is_selected = i in st.session_state.selected_nums
    if cols[(i-1)%5].button(btn_label, key=f"btn_{i}", type="primary" if is_selected else "secondary"):
        if i in st.session_state.selected_nums:
            st.session_state.selected_nums.remove(i)
        elif len(st.session_state.selected_nums) < required_count:
            st.session_state.selected_nums.append(i)
        st.rerun()

# C. 操作按鈕
col_bet1, col_bet2 = st.sidebar.columns(2)
if col_bet1.button("🎲 隨機選號"):
    st.session_state.selected_nums = random.sample(range(1, 81), required_count)
    st.rerun()
if col_bet2.button("🧹 清除選號"):
    st.session_state.selected_nums = []
    st.rerun()

st.sidebar.write(f"已選號碼: {sorted(st.session_state.selected_nums)}")

if st.sidebar.button("➕ 加入投注"):
    if len(st.session_state.selected_nums) == required_count:
        if len(st.session_state.my_bets) < 10:
            st.session_state.my_bets.append({
                "type": star_type,
                "nums": sorted(st.session_state.selected_nums),
                "time": now_tw.strftime("%H:%M:%S"),
                "period_start": data[0]['period'] if data else "未知"
            })
            st.session_state.selected_nums = [] # 加入後清空
            st.sidebar.success("已成功加入投注清單！")
            st.rerun()
        else:
            st.sidebar.error("最多只能下 10 注！")
    else:
        st.sidebar.error(f"請選滿 {required_count} 個號碼")

if st.sidebar.button("🗑️ 清除所有已加入投注"):
    st.session_state.my_bets = []
    st.rerun()

# --- 主畫面顯示 ---
if data:
    latest = data[0]
    
    # 1. 最新開獎
    st.subheader(f"📍 最新開獎期號: {latest['period']}")
    ball_html = "".join([f'<span style="background-color:#1E90FF; color:white; border-radius:50%; padding:8px 12px; margin:4px; display:inline-block; font-weight:bold;">{n:02d}</span>' for n in latest['numbers']])
    st.markdown(ball_html, unsafe_allow_html=True)

    # 2. 預測區
    st.divider()
    prediction = fibonacci_analysis(data)
    st.subheader("🔮 費波那契+黃金分割 預測下一期")
    st.info(f"建議號碼： {', '.join([f'{n:02d}' for n in prediction])}")

    # 3. 模擬投注核對 (顯示已加入的號碼與對獎結果)
    if st.session_state.my_bets:
        st.divider()
        st.subheader("🎯 模擬投注核對 (追蹤中)")
        for i, bet in enumerate(st.session_state.my_bets):
            # 核對最新一期
            matches = set(bet['nums']) & set(latest['numbers'])
            bg_color = "#f0f2f6" if len(matches) == 0 else "#fff4f4"
            with st.container():
                st.markdown(f"""
                <div style="background-color:{bg_color}; padding:15px; border-radius:10px; border-left:5px solid #FF4B4B; margin-bottom:10px;">
                    <strong>注項 {i+1} ({bet['type']})</strong> | 投注時間: {bet['time']} | 起始對獎期號: {bet['period_start']}<br>
                    投注號碼: {' , '.join([f'{n:02d}' for n in bet['nums']])}<br>
                    目前最新期 ({latest['period']}) 對中： <span style="color:red; font-size:1.2em;">{len(matches)}</span> 顆 
                    ({', '.join(map(str, sorted(list(matches)))) if matches else "無"})
                </div>
                """, unsafe_allow_html=True)

    # 4. 近 10 期開獎記錄 (回答問題 3)
    st.divider()
    st.subheader("📊 近 10 期歷史開獎記錄")
    df = pd.DataFrame(data[:10])
    df['numbers'] = df['numbers'].apply(lambda x: ", ".join([f"{n:02d}" for n in x]))
    st.dataframe(df, use_container_width=True)

else:
    st.error("⚠️ 無法獲取開獎資料，請檢查網路連線或稍後再試。")

st.info(f"最後更新時間 (台灣): {now_tw.strftime('%Y-%m-%d %H:%M:%S')} (每 5 分鐘自動刷新)")

