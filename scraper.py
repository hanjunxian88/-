import csv
import datetime
import sys
import os
from playwright.sync_api import sync_playwright

def run():
    # 使用 with 语句自动管理浏览器关闭
    with sync_playwright() as p:
        # 1. 启动浏览器 (Headless 模式，无头模式)
        browser = p.chromium.launch(headless=True)
        
        # 2. 【关键修改】设置 User-Agent 伪装成普通浏览器，防止被反爬虫拦截
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # 3. 【关键修改】设置超时时间为 60秒 (默认是30秒，GitHub Actions 网络有时较慢)
        page.set_default_timeout(60000)

        try:
            print(f"[{datetime.datetime.now()}] 正在访问蔚来官网...")
            
            # 访问页面 (wait_until="domcontentloaded" 比默认的 load 更快)
            # 请确认这是你要抓取的网址
            page.goto("https://www.nio.cn/nio-power", wait_until="domcontentloaded")
            
            # 等待页面稍微加载一下 (防止数据还没渲染出来)
            page.wait_for_timeout(5000) 

            # ---------------------------------------------------------
            # 👇👇👇 在这里编写你的具体抓取逻辑 👇👇👇
            # ---------------------------------------------------------
            
            # [示例逻辑] 获取页面标题 (你可以替换成你原本的抓取代码)
            title = page.title()
            print(f"成功获取标题: {title}")
            
            # [示例数据] 构造要保存的数据
            data = [
                {
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "title": title,
                    "url": page.url
                }
            ]
            # ---------------------------------------------------------
            # 👆👆👆 抓取逻辑结束 👆👆👆
            # ---------------------------------------------------------

            # 4. 保存数据到 CSV
            csv_file = 'nio_power_data.csv'
            file_exists = os.path.isfile(csv_file)
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["date", "title", "url"])
                # 如果是新文件，写入表头
                if not file_exists:
                    writer.writeheader()
                writer.writerows(data)
            
            print(f"✅ 数据已保存到 {csv_file}")

        except Exception as e:
            print(f"❌ 抓取出错: {e}")
            # 【关键修改】如果出错，截图保存，方便在 GitHub Actions 里查看原因
            page.screenshot(path="error_screenshot.png")
            print("已保存错误截图: error_screenshot.png")
            # 抛出异常，让 Workflow 知道这里失败了
            sys.exit(1)
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()
