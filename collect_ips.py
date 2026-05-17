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
            # 过滤常见无效/大段IP
            valid_ips = {ip for ip in ips if not ip.endswith('.0') and not ip.endswith('.255')}
            all_ips.update(valid_ips)
            print(f"  找到 {len(ips)} 个IP，有效 {len(valid_ips)} 个")
        time.sleep(1)
    except Exception as e:
        print(f"  {url} 失败: {e}")

# 优先保留常用优质段 + 限制数量
priority = [ip for ip in all_ips if ip.startswith(('104.16.', '104.17.', '172.64.', '172.67.', '141.101.', '162.159.'))]

with open('ip.txt', 'w') as f:
    for ip in sorted(set(priority + list(all_ips)))[:150]:   # 限制150个
        f.write(ip + '\n')

print(f"最终保存 {len(set(priority + list(all_ips))[:150])} 个IP")
