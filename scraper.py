import csv
import datetime
import sys
import os
import time
import random
from playwright.sync_api import sync_playwright
# 👇 引入隐身插件
from playwright_stealth import stealth_sync

def run():
    with sync_playwright() as p:
        # 1. 启动浏览器
        browser = p.chromium.launch(headless=True)
        
        # 2. 创建上下文 (模拟正常的屏幕大小)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        # 3. 创建页面并开启隐身模式 (关键步骤!)
        page = context.new_page()
        stealth_sync(page) 
        
        try:
            print(f"[{datetime.datetime.now()}] 正在启动隐身爬虫...")
            
            # 4. 访问蔚来官网 (尝试换一个页面，地图页通常包含数据接口)
            # 如果 nio-power 还是被拦，我们试试 official-map
            target_url = "https://www.nio.cn/nio-power"
            print(f"正在访问: {target_url}")
            
            page.goto(target_url, wait_until="domcontentloaded")
            
            # 5. 模拟人类行为：随机等待和滚动
            # 很多防火墙会检测你是不是进页面立刻就抓数据
            time.sleep(random.uniform(3, 5)) 
            page.mouse.wheel(0, 500)
            time.sleep(random.uniform(2, 4))
            
            # 获取页面标题
            title = page.title()
            print(f"当前标题: {title}")
            
            # 🚨 再次检查是否被拦截
            if "Security" in title or "验证" in title or "403" in title:
                print("⚠️ 依然被拦截。尝试截图保存现场...")
                page.screenshot(path="blocked_debug.png")
                # 即使被拦截，我们也不要报错退出，而是记录下来，方便你查看 CSV 确认状态
                final_status = "Blocked (Security Verification)"
            else:
                final_status = "Success"
                # 这里未来可以加入提取具体数字的代码
                # count = page.locator("...").text_content()

            # 6. 构造数据
            data = [{
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "title": title,
                "status": final_status, # 新增一列状态，方便你看
                "url": target_url
            }]

            # 7. 保存数据
            csv_file = 'nio_power_data.csv'
            file_exists = os.path.isfile(csv_file)
            
            # 读取现有文件，避免重复写入完全相同的错误信息 (可选优化)
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                # 更新表头，增加 status
                fieldnames = ["date", "title", "url", "status"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # 如果是新文件，写表头
                if not file_exists:
                    writer.writeheader()
                # 如果是旧文件但没有 status 列，可能会报错，建议你先手动删掉 GitHub 上的 csv 文件，让它重新生成
                # 或者这里简单处理，直接写
                writer.writerows(data)
            
            print(f"✅ 数据写入完成，状态: {final_status}")

        except Exception as e:
            print(f"❌ 运行出错: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
