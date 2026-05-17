import requests
import re
import os
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

urls = [
    "https://api.uouin.com/cloudflare.html",      # IP来源
    "https://vps789.com/cfip/?remarks=domain"    # 域名来源
]

if os.path.exists('ip.txt'):
    os.remove('ip.txt')

all_ips = set()
all_domains = set()

print("开始采集 Cloudflare IP & 域名...\n")

for url in urls:
    try:
        print(f"正在采集: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200:
            text = r.text

            # 提取IPv4地址
            ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text)
            valid_ips = {ip for ip in ips 
                        if ip.count('.') == 3 
                        and not ip.endswith(('.0', '.255'))}
            
            # 提取域名（简单匹配）
            domains = re.findall(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}', text)
            valid_domains = {d.strip() for d in domains if len(d) > 5}

            all_ips.update(valid_ips)
            all_domains.update(valid_domains)

            print(f"  ✓ IP: {len(valid_ips)} 个 | 域名: {len(valid_domains)} 个")
            
        else:
            print(f"  ✗ 状态码异常: {r.status_code}")
            
    except Exception as e:
        print(f"  ✗ {url} 采集失败: {e}")
    
    time.sleep(1)

# 保存结果
with open('ip.txt', 'w', encoding='utf-8') as f:
    # 先写IP
    if all_ips:
        f.write("# === Cloudflare IP ===\n")
        for ip in sorted(all_ips)[:10]:
            f.write(ip + '\n')
    
    # 再写域名
    if all_domains:
        f.write("\n# === Cloudflare 域名 ===\n")
        for domain in sorted(all_domains)[:10]:
            f.write(domain + '\n')

total = len(all_ips) + len(all_domains)
print(f"\n✅ 采集完成！")
print(f"   IP数量: {len(all_ips)} 个")
print(f"   域名数量: {len(all_domains)} 个")
print(f"   已保存到 ip.txt（前10个IP + 前10个域名）")
