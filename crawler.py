import requests
import json
from datetime import datetime

def fetch_taiwan_lottery_api():
    # 這是台彩賓果賓果的官方 API 連結
    url = "https://api.taiwanlottery.com/TLCAPI_v10/Lottery/BingoBingoResult"
    
    # 設定查詢參數 (今天)
    params = {
        "Date": datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        # 執行請求
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            print(f"API 連線失敗: {response.status_code}")
            return

        raw_data = response.json()
        all_draws = raw_data.get('content', {}).get('bingoBingoResubValue', [])
        
        results = []
        for draw in all_draws:
            period = draw.get('drawTerm') # 期別
            # 台彩 API 提供的號碼是以逗號分隔的字串
            numbers_str = draw.get('winningNumbers', '')
            if numbers_str:
                numbers = [int(n) for n in numbers_str.split(',')]
                results.append({
                    "period": period,
                    "numbers": sorted(numbers)
                })
        
        if results:
            # 依期別排序 (最新在前面)
            results.sort(key=lambda x: x['period'], reverse=True)
            
            with open('bingo_data.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            print(f"✅ 成功抓取今天共 {len(results)} 期資料！")
        else:
            print("❌ API 回傳內容中沒有開獎資料。")
            
    except Exception as e:
        print(f"💥 發生錯誤: {e}")

if __name__ == "__main__":
    fetch_taiwan_lottery_api()
