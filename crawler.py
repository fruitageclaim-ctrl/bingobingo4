import requests
from bs4 import BeautifulSoup
import json
import re

def fetch_bingo_data():
    url = "https://winwin.tw/Bingo"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # 找到開獎表格的所有列
        rows = soup.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # 判斷是否為有效的數據列（期別在第一欄）
            if len(cols) >= 2:
                period_text = cols[0].get_text(strip=True)
                # 必須是純數字期別 (例如 115012506)
                if not re.match(r'^\d+$', period_text):
                    continue
                
                # 關鍵修正：從號碼欄位中只提取「大球號碼」
                # 我們不使用 get_text()，改用正規表達式搜尋該 td 內所有的 1-2 位數字
                all_raw_text = str(cols[1])
                # 尋找所有被包在標籤裡的 1-2 位數字
                balls = re.findall(r'>(\d{1,2})<', all_raw_text)
                
                # 轉換為整數並去重 (賓果每期固定 20 個號碼)
                unique_balls = []
                for b in balls:
                    num = int(b)
                    if num not in unique_balls and 1 <= num <= 80:
                        unique_balls.append(num)
                
                # 確保抓到完整的 20 顆球
                if len(unique_balls) >= 20:
                    results.append({
                        "period": period_text,
                        "numbers": unique_balls[:20]
                    })
        
        if results:
            # 寫入檔案
            with open('bingo_data.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
            print(f"成功抓取 {len(results)} 期資料！")
        else:
            print("未能提取有效號碼，請檢查網頁結構。")
            
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    fetch_bingo_data()
