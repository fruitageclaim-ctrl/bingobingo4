import requests
from bs4 import BeautifulSoup
import json
import time

def fetch_bingo():
    url = "https://winwin.tw/Bingo"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # 根據 winwin 結構，抓取所有表格列
        rows = soup.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # 確保欄位數量正確 (期別, 號碼, ...)
            if len(cols) >= 2:
                period = cols[0].get_text(strip=True)
                if not period.isdigit(): continue # 跳過非數字的標題列
                
                # 抓取該列中所有的號碼球
                # winwin 通常使用 span 或 div 包裝號碼
                balls = [int(b.get_text(strip=True)) for b in cols[1].find_all(['span', 'div', 'b']) 
                         if b.get_text(strip=True).isdigit()]
                
                if len(balls) >= 20:
                    results.append({
                        "period": period,
                        "numbers": balls[:20]
                    })
        
        if results:
            with open('bingo_data.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            print(f"成功抓取 {len(results)} 期資料")
        else:
            print("警告：未抓取到任何資料，請檢查網頁選擇器。")
            
    except Exception as e:
        print(f"爬蟲執行出錯: {e}")

if __name__ == "__main__":
    fetch_bingo()
