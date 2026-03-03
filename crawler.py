import requests
from bs4 import BeautifulSoup
import json
import re

def fetch_taiwan_lottery():
    # 台灣彩券賓果賓果開獎結果網址
    url = "https://www.taiwanlottery.com/lotto/result/bingo_bingo"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # 台灣彩券的結構通常是由多個開獎區塊組成
        # 尋找所有開獎期別區塊
        items = soup.select('.lotto_result_table')
        
        for item in items:
            # 提取期別 (例如：115012506)
            period_tag = item.select_one('.lotto_result_title .period')
            if not period_tag:
                continue
            period = re.sub(r'\D', '', period_tag.get_text())
            
            # 提取 20 個開獎號碼
            # 官方通常使用特定 class 如 'ball_orange' 或 'ball_yellow'
            ball_tags = item.select('.ball_tx .ball_orange')
            balls = [int(b.get_text(strip=True)) for b in ball_tags if b.get_text(strip=True).isdigit()]
            
            # 確保抓到完整 20 顆球
            if len(balls) >= 20:
                results.append({
                    "period": period,
                    "numbers": sorted(balls[:20]) # 排序後存入
                })
        
        if results:
            with open('bingo_data.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            print(f"✅ 成功從台灣彩券抓取 {len(results)} 期資料！")
        else:
            print("❌ 官方網頁解析失敗，請檢查 Selector。")
            
    except Exception as e:
        print(f"💥 發生錯誤: {e}")

if __name__ == "__main__":
    fetch_taiwan_lottery()
