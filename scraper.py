import csv
import datetime
import time
import re
import os
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # 1. 启动浏览器 (Headless模式，适合服务器运行)
        browser = p.chromium.launch(headless=True)
        
        # --- 🛡️ 关键修改：伪装成真实用户 ---
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            # 使用标准的 Windows Chrome User-Agent
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # 设置语言和时区，防止被识别为海外机器人
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )
        
        page = context.new_page()
        
        # 🎭 注入脚本：隐藏 WebDriver 特征 (这是反爬的关键)
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            print(f"[{datetime.datetime.now()}] 正在启动爬虫...")
            target_url = "https://www.nio.cn/nio-power"
            print(f"🔗 正在访问: {target_url}")
            
            page.goto(target_url, wait_until="domcontentloaded")
            
            # 2. 等待数字滚动 (蔚来官网动画较慢，给足 15秒)
            print("⏳ 正在等待数字滚动结束 (15秒)...")
            time.sleep(15)

            # 获取全页文本
            content = page.inner_text("body")
            
            # --- 🎯 抓取逻辑 ---
            
            # A. 抓取【蔚来换电站】
            station_match = re.search(r"([\d,]+)\s+蔚来换电站", content)
            station_count = station_match.group(1) if station_match else "未找到"

            # B. 抓取【实际累计换电次数】(暴力清洗版)
            # 逻辑：找到“实际累计换电次数”，向前抓取 100 个字符，清洗掉非数字
            swap_match = re.search(r"([\s\S]{0,100})\s*实际累计换电次数", content)
            
            swap_count = "未找到"
            if swap_match:
                raw_text = swap_match.group(1)
                # 🧹 清洗：只保留数字
                clean_digits = re.sub(r"\D", "", raw_text)
                
                # 验证：如果提取出的数字长度超过 8 位 (千万级以上)，就是它了
                if len(clean_digits) >= 8:
                    # 格式化成 102,500,917 的样子
                    swap_count = "{:,}".format(int(clean_digits))
            
            # C. 备用方案：如果正则没抓到，找全页最大的纯数字串
            if swap_count == "未找到":
                print("⚠️ 正则未命中，尝试全页搜索最大数字...")
                # 找所有 8 位以上的数字
                all_long_nums = re.findall(r"\d{8,}", content.replace(",", "").replace("\n", ""))
                if all_long_nums:
                    max_num = max([int(x) for x in all_long_nums])
                    swap_count = "{:,}".format(max_num)

            print("-" * 30)
            print(f"✅ 抓取完成")
            print(f"   🔋 累计换电次数: {swap_count}")
            print(f"   🏠 蔚来换电站:   {station_count}")
            print("-" * 30)

            # --- 💾 保存逻辑 (绝对路径修复) ---
            # 获取脚本所在目录，确保在任何环境下都能找到 CSV
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_file = os.path.join(script_dir, 'nio_power_data.csv')
            
            file_exists = os.path.isfile(csv_file)
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ["date", "swap_count", "station_count", "url"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "swap_count": swap_count,
                    "station_count": station_count,
                    "url": target_url
                })
            
            print(f"💾 数据已追加到: {csv_file}")

        except Exception as e:
            print(f"❌ 出错: {e}")
            # 如果在 GitHub Actions 里出错，抛出异常让流程显示红色失败
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
