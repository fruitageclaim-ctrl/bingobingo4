import requests
from bs4 import BeautifulSoup
import json
import os

def fetch_and_save():
    url = "https://winwin.tw/Bingo"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        data = []
        # 尋找開獎表格的所有列
        rows = soup.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # 確保這一列有期別和號碼
            if len(cols) >= 2:
                period = cols[0].get_text(strip=True)
                # 排除標題列
                if not period.isdigit(): continue
                
                # 抓取球號
                ball_elements = cols[1].find_all(['span', 'div', 'b'])
                balls = []
                for b in ball_elements:
                    txt = b.get_text(strip=True)
                    # 只取前兩個數字，避免抓到連莊次數的小標籤
                    if txt[:2].isdigit():
                        balls.append(int(txt[:2]))
                
                if len(balls) >= 20:
                    data.append({"period": period, "numbers": balls[:20]})
        
        if data:
            with open('bingo_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"✅ 成功抓取 {len(data)} 期資料")
        else:
            print("❌ 抓取不到資料，請檢查網頁結構")
            
    except Exception as e:
        print(f"💥 發生錯誤: {e}")

if __name__ == "__main__":
    fetch_and_save()
