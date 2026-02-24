import csv
import datetime
import sys
import os
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # 1. 启动浏览器，添加参数隐藏 "自动化" 特征
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled', # 关键：移除自动化特征
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        # 2. 模拟真实设备
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        # 3. 注入 JavaScript 进一步隐藏 WebDriver 属性
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page.set_default_timeout(60000)

        try:
            print(f"[{datetime.datetime.now()}] 正在访问蔚来官网...")
            page.goto("https://www.nio.cn/nio-power", wait_until="domcontentloaded")
            
            # 等待长一点时间，模拟人类浏览
            time.sleep(5)
            
            # 尝试滚动页面，触发懒加载
            page.mouse.wheel(0, 500)
            time.sleep(2)

            # 获取标题
            title = page.title()
            print(f"当前页面标题: {title}")

            # 🚨 检查是否被拦截
            if "Security" in title or "验证" in title:
                print("⚠️ 警告：被蔚来官网拦截 (Security Verification)。")
                # 截图留证
                page.screenshot(path="blocked_screenshot.png")
                # 这里我们不退出，而是尝试保存一下，看看能不能拿到部分数据
            
            # ---------------------------------------------------------
            # 这里需要根据你要抓的具体内容写选择器
            # 假设我们要抓取页面上的某个特定文本，比如换电站数量
            # 如果你只是测试，下面的代码会保存标题
            # ---------------------------------------------------------
            
            data = [{
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "title": title,
                "url": page.url
            }]

            # 保存数据
            csv_file = 'nio_power_data.csv'
            file_exists = os.path.isfile(csv_file)
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["date", "title", "url"])
                if not file_exists:
                    writer.writeheader()
                writer.writerows(data)
            
            print(f"✅ 数据已保存")

        except Exception as e:
            print(f"❌ 出错: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
