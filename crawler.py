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
        table = soup.find('table') # 抓取開獎表格
        if not table:
            return
            
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                period = cols[0].get_text(strip=True)
                # 提取球號，過濾掉連莊次數的小數字
                balls = [int(b.get_text(strip=True)[:2]) for b in cols[1].find_all(['div', 'span']) if b.get_text(strip=True)[:2].isdigit()]
                if len(balls) >= 20:
                    data.append({"period": period, "numbers": balls[:20]})
        
        if data:
            with open('bingo_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"成功更新 {len(data)} 期資料")
    except Exception as e:
        print(f"爬取失敗: {e}")

if __name__ == "__main__":
    fetch_and_save()