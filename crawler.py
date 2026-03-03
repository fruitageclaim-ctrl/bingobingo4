import requests
from bs4 import BeautifulSoup
import json
import os

def fetch_and_save():
    # 使用與您圖片顯示一致的數據源
    url = "https://winwin.tw/Bingo"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        data = []
        # 根據 winwin.tw 結構抓取表格
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                period = cols[0].get_text(strip=True)
                if not period.isdigit(): continue
                # 抓取球號數字
                balls = [int(b.get_text(strip=True)[:2]) for b in cols[1].find_all(['div', 'span']) if b.get_text(strip=True)[:2].isdigit()]
                if len(balls) >= 20:
                    data.append({"period": period, "numbers": balls[:20]})
        
        if data:
            # 強制寫入目前目錄
            with open('bingo_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"成功更新 {len(data)} 期資料")
        else:
            print("未能抓取到任何資料，請檢查網頁結構")
            # 建立一個空檔案防止 Actions 報錯
            with open('bingo_data.json', 'w') as f: f.write("[]")
            
    except Exception as e:
        print(f"發生錯誤: {e}")
        with open('bingo_data.json', 'w') as f: f.write("[]")

if __name__ == "__main__":
    fetch_and_save()
