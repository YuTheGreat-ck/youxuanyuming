import requests
import re
import os

print("开始采集 Cloudflare IP...")

# 直接使用 XIU2 的公开 IP 列表（最稳定）
url = "https://raw.githubusercontent.com/XIU2/CloudflareSpeedTest/master/ip.txt"

try:
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=30)
    print(f"请求状态: {r.status_code}")

    if r.status_code == 200:
        ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', r.text)
        valid_ips = [ip for ip in ips if not ip.endswith(('.0', '.255'))]

        with open('ip.txt', 'w') as f:
            for ip in valid_ips[:180]:
                f.write(ip + '\n')
        
        print(f"✅ 成功保存 {len(valid_ips[:180])} 个IP 到 ip.txt")
    else:
        print("❌ 下载失败")

except Exception as e:
    print(f"❌ 错误: {e}")
    # 备用硬编码几个常用IP
    with open('ip.txt', 'w') as f:
        f.write("104.16.0.0\n104.16.16.0\n172.64.0.0\n141.101.64.0\n188.114.96.0\n")
    print("已写入备用IP")
