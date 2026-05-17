import requests
import re
import os
import time

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

urls = [
    "https://ipdb.030101.xyz/api/bestcf.txt",
    "https://bestcfip.com/",
    "https://cfip.uu.icu/",
    "https://raw.githubusercontent.com/XIU2/CloudflareSpeedTest/master/ip.txt",
    "https://stock.hostmonit.com/CloudFlareYes",
]

if os.path.exists('ip.txt'):
    os.remove('ip.txt')

all_ips = set()

for url in urls:
    try:
        print(f"采集: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', r.text)
            valid = {ip for ip in ips if not ip.endswith(('.0', '.255'))}
            all_ips.update(valid)
            print(f"  有效IP: {len(valid)}")
        time.sleep(1)
    except Exception as e:
        print(f"  {url} 失败")

with open('ip.txt', 'w') as f:
    for ip in sorted(all_ips)[:180]:
        f.write(ip + '\n')

print(f"最终保存 {len(all_ips)} 个IP")
