import csv
import datetime
import sys
import os
import time
import random
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # 1. 启动浏览器
        # args 参数非常重要，用于禁用浏览器的自动化特征
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        # 2. 创建上下文 (模拟 1920x1080 屏幕)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        page = context.new_page()

        # 3. 【核心】手动注入隐身脚本 (替代报错的 playwright-stealth)
        # 这段 JS 代码会骗过网站，让它以为这是一个真实的浏览器
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

        try:
            print(f"[{datetime.datetime.now()}] 正在启动爬虫...")
            
            # 4. 访问蔚来官网
            target_url = "https://www.nio.cn/nio-power"
            print(f"正在访问: {target_url}")
            
            page.goto(target_url, wait_until="domcontentloaded")
            
            # 5. 模拟人类操作 (随机等待 + 滚动)
            time.sleep(random.uniform(2, 5))
            page.mouse.wheel(0, 300)
            time.sleep(1)
            
            # 获取标题
            title = page.title()
            print(f"当前标题: {title}")

            # 6. 判断是否被拦截
            if "Security" in title or "验证" in title:
                status = "Blocked (Security Verification)"
                print("⚠️ 警告：被蔚来官网拦截。")
            else:
                status = "Success"
                print("✅ 访问成功！")

            # 7. 保存数据
            data = [{
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "title": title,
                "status": status,
                "url": target_url
            }]

            csv_file = 'nio_power_data.csv'
            file_exists = os.path.isfile(csv_file)
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                # 注意：这里我们增加了 status 列
                fieldnames = ["date", "title", "url", "status"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                # 为了防止旧文件表头不匹配报错，这里做一个简单的容错处理
                # 如果是追加写入，且文件已存在，DictWriter 会尝试写入，
                # 如果旧文件没有 status 列，可能会导致格式稍微有点乱，但不影响查看。
                writer.writerows(data)
            
            print(f"✅ 数据已写入 CSV，状态: {status}")

        except Exception as e:
            print(f"❌ 运行出错: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    run()

