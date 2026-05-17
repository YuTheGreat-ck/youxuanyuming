import requests
import re
import os
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

urls = [
    "https://api.uouin.com/cloudflare.html",      # IP为主
    "https://vps789.com/cfip/?remarks=domain"    # 域名为主
]

if os.path.exists('ip.txt'):
    os.remove('ip.txt')

all_ips = set()
all_domains = set()

print("开始采集 Cloudflare IP & 优质域名...\n")

for url in urls:
    try:
        print(f"正在采集: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200:
            text = r.text.lower()  # 转小写方便处理

            # ==================== 提取IP ====================
            ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text)
            valid_ips = {
                ip for ip in ips 
                if ip.count('.') == 3 
                and not ip.endswith(('.0', '.255'))
                and all(0 <= int(x) <= 255 for x in ip.split('.'))
            }
            all_ips.update(valid_ips)

            # ==================== 提取域名（加强过滤）===================
            # 匹配完整域名（至少一个点，且后缀合理）
            domain_pattern = r'([a-z0-9][-a-z0-9]*\.)+[a-z]{2,}'
            domains = re.findall(domain_pattern, text)
            
            valid_domains = set()
            for d in domains:
                d = d.strip('.- ')
                if (len(d) > 6 and '.' in d 
                    and not d.startswith(('http', 'www.', 'ftp.')) 
                    and not any(x in d for x in ['..', ' ', ',', '"', "'"])):
                    valid_domains.add(d)
            
            all_domains.update(valid_domains)

            print(f"  ✓ IP: {len(valid_ips)} 个 | 域名: {len(valid_domains)} 个")
            
        else:
            print(f"  ✗ 状态码: {r.status_code}")
            
    except Exception as e:
        print(f"  ✗ {url} 失败: {e}")
    
    time.sleep(1.5)

# ====================== 保存 ======================
with open('ip.txt', 'w', encoding='utf-8') as f:
    # IP 部分
    f.write("# === Cloudflare IP ===\n")
    for ip in sorted(all_ips)[:10]:
        f.write(ip + '\n')
    
    f.write("\n# === Cloudflare 域名 ===\n")
    for domain in sorted(all_domains)[:10]:
        f.write(domain + '\n')

print(f"\n✅ 采集完成！")
print(f"   有效IP: {len(all_ips)} 个")
print(f"   有效域名: {len(all_domains)} 个")
print(f"   已保存前 10 个IP + 前 10 个域名 到 ip.txt")
