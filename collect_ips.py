import requests
import re
import os
import time

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

urls = [
    "https://raw.githubusercontent.com/XIU2/CloudflareSpeedTest/master/ip.txt",   # 稳定大列表
    "https://api.uouin.com/cloudflare.html",                                     # 你指定的源（表格形式）
    "https://vps789.com/cfip/?remarks=domain",                                  # 你指定的源
    "https://bestcfip.com/",
    "https://ipdb.030101.xyz/api/bestcf.txt",
]

if os.path.exists('ip.txt'):
    os.remove('ip.txt')

all_ips = set()

for url in urls:
    try:
        print(f"正在采集: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            # 提取所有IPv4地址
            ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', r.text)
            # 过滤无效IP
            valid = {ip for ip in ips if not ip.endswith(('.0', '.255'))}
            all_ips.update(valid)
            print(f"  成功获取 {len(valid)} 个有效IP")
        time.sleep(1)
    except Exception as e:
        print(f"  {url} 采集失败: {e}")

# 保存最终结果
with open('ip.txt', 'w') as f:
    for ip in sorted(all_ips)[:200]:
        f.write(ip + '\n')

print(f"✅ 采集完成！共保存 {len(all_ips)} 个IP 到 ip.txt")
