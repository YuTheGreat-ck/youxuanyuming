import requests
from bs4 import BeautifulSoup
import re
import os
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
}

urls = [
    "https://ipdb.030101.xyz/api/bestcf.txt",     # 常用稳定源
    "https://www.wetest.vip/page/cloudflare/address_v4.html",
    "https://bestcfip.com/",
    "https://cfip.uu.icu/",
    "https://stock.hostmonit.com/CloudFlareYes",
    "https://raw.githubusercontent.com/XIU2/CloudflareSpeedTest/master/ip.txt",  # XIU2备用
]

ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

if os.path.exists('ip.txt'):
    os.remove('ip.txt')

all_ips = set()

for url in urls:
    try:
        print(f"正在采集: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"  状态码: {response.status_code}")
            continue

        text = response.text
        ips = re.findall(ip_pattern, text)
        
        valid_ips = {ip for ip in ips if re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip)}
        all_ips.update(valid_ips)
        
        print(f"  从 {url} 找到 {len(valid_ips)} 个有效IP")
        time.sleep(1.5)
        
    except Exception as e:
        print(f"  {url} 采集失败: {e}")

# 写入 ip.txt（最多保留300个，避免太多）
with open('ip.txt', 'w') as f:
    for ip in sorted(all_ips)[:300]:
        f.write(ip + '\n')

print(f'采集完成！共 {len(all_ips)} 个唯一IP，已保存到 ip.txt')
