import asyncio
from playwright.async_api import async_playwright
import csv
import datetime
import os
import re

# 配置
URL = "https://www.nio.cn/nio-power"
DATA_FILE = "nio_power_data.csv"

async def fetch_nio_data():
    async with async_playwright() as p:
        # 1. 启动浏览器
        browser = await p.chromium.launch(headless=True) # headless=False 可以看到浏览器界面
        page = await browser.new_page()
        
        print(f"[{datetime.datetime.now()}] 正在访问蔚来官网...")
        
        # 2. 访问页面 (设置超时防止卡死)
        try:
            await page.goto(URL, timeout=60000)
            
            # 3. 等待数据加载
            # 注意：这里需要根据网页实际结构调整选择器。
            # 通常换电数字会在一个显著的 class 中，例如包含 'count' 或 'number'
            # 假设我们通过文本特征定位（更通用）
            
            # 等待页面上出现“累计换电”相关的文字，确保数字已渲染
            await page.wait_for_load_state("networkidle") 
            
            # 提取页面全部文本，用正则匹配（这是最稳健的方法，不怕页面改版）
            content = await page.content()
            
            # 4. 数据提取 (正则匹配：寻找“换电”附近的数字)
            # 匹配逻辑：寻找类似 "101,543,828" 这样的长数字
            # 蔚来官网通常显示为：累计换电次数 ... 数字
            # 这里使用一个假设的逻辑，实际运行需根据 F12 审查元素微调
            
            # 方案 A: 尝试获取特定元素 (推荐先用 F12 确认 class)
            # 例如官网可能用 <span class="counter">101,543,828</span>
            # number_element = await page.locator("css_selector_here").inner_text()
            
            # 方案 B: 暴力正则提取（示例用）
            # 查找所有类似 "100,000,000" 格式的数字
            matches = re.findall(r'(\d{1,3}(?:,\d{3})*)', content)
            
            # 过滤掉短数字，找那个最大的（通常就是换电总数）
            candidates = []
            for m in matches:
                clean_num = m.replace(',', '')
                if len(clean_num) > 7: # 换电数肯定是千万/亿级
                    candidates.append(int(clean_num))
            
            if not candidates:
                print("未找到符合格式的数据，请检查选择器或正则。")
                await browser.close()
                return

            swap_count = max(candidates) # 假设最大的数字就是换电总数
            
            # 获取当前时间
            now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"抓取成功！当前换电总数: {swap_count}")
            
            # 5. 保存数据
            save_data(now_time, swap_count)
            
        except Exception as e:
            print(f"抓取出错: {e}")
        finally:
            await browser.close()

def save_data(timestamp, count):
    file_exists = os.path.isfile(DATA_FILE)
    
    with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 如果文件不存在，先写表头
        if not file_exists:
            writer.writerow(["Timestamp", "Total_Swaps"])
        
        writer.writerow([timestamp, count])
        print(f"数据已保存至 {DATA_FILE}")

if __name__ == "__main__":
    asyncio.run(fetch_nio_data())
