import requests
from bs4 import BeautifulSoup
import json
import re

def fetch_bingo():
    # winwin 網站網址
    url = "https://winwin.tw/Bingo"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://winwin.tw/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # 定位開獎表格的所有列
        rows = soup.select('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # 確保欄位包含期別 (通常第一欄是期別，第二欄是號碼)
            if len(cols) >= 2:
                period_text = cols[0].get_text(strip=True)
                # 判斷是否為期別數字 (例如 115012506)
                period_match = re.search(r'\d{9}', period_text)
                if not period_match:
                    continue
                
                period = period_match.group()
                
                # 關鍵修正：精準抓取 20 個號碼
                # winwin 的號碼通常在 td 內的 span 裡面，我們只取前兩位純數字
                balls = []
                # 尋找所有可能是號碼球的標籤
                potential_balls = cols[1].find_all(['span', 'b', 'div'])
                for b in potential_balls:
                    txt = b.get_text(strip=True)
                    # 使用正規表達式只抓取開頭的兩位數字，忽略上標的連莊次數
                    num_match = re.match(r'^(\d{1,2})', txt)
                    if num_match:
                        balls.append(int(num_match.group(1)))
                
                # 賓果賓果每期固定 20 個號碼
                # 使用 set 去重後取前 20 個，確保資料純淨
                unique_balls = []
                for n in balls:
                    if n not in unique_balls:
                        unique_balls.append(n)
                
                if len(unique_balls) >= 20:
                    results.append({
                        "period": period,
                        "numbers": unique_balls[:20]
                    })
        
        if results:
            # 成功抓取後覆蓋 bingo_data.json
            with open('bingo_data.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            print(f"✅ 成功抓取 {len(results)} 期開獎資料！")
        else:
            print("❌ 依然抓不到資料，可能網頁有防爬蟲機制或結構大改。")
            
    except Exception as e:
        print(f"💥 爬蟲發生錯誤: {e}")

if __name__ == "__main__":
    fetch_bingo()
