import requests
import re
import os
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

urls = [
    "https://api.uouin.com/cloudflare.html",
    "https://vps789.com/cfip/?remarks=domain"
]

def ping_ip(ip: str, count=2) -> float:
    """测试IP延迟，返回平均延迟（毫秒），失败返回9999"""
    try:
        output = subprocess.check_output(
            f"ping -n {count} {ip}", 
            shell=True, 
            stderr=subprocess.STDOUT,
            timeout=8
        ).decode('gbk', errors='ignore')
        
        # 提取平均时间
        if "平均" in output or "Average" in output:
            times = re.findall(r'(\d+)ms', output)
            if times:
                return float(sum(int(t) for t in times) / len(times))
    except:
        pass
    return 9999.0

def test_domain(domain: str) -> float:
    """测试域名延迟"""
    try:
        start = time.time()
        r = requests.get(f"http://{domain}", headers=headers, timeout=6)
        latency = (time.time() - start) * 1000
        return latency if r.status_code < 400 else 9999.0
    except:
        return 9999.0

# ====================== 主程序 ======================
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

all_ips = set()
all_domains = set()

print("正在采集 IP 和域名...\n")

for url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            text = r.text.lower()

            # 提取IP
            ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text)
            valid_ips = {ip for ip in ips if ip.count('.') == 3 and not ip.endswith(('.0', '.255'))}
            all_ips.update(valid_ips)

            # 提取域名
            domains = re.findall(r'([a-z0-9][-a-z0-9]*\.)+[a-z]{2,}', text)
            valid_domains = {d.strip('.- ') for d in domains if len(d) > 6 and '.' in d}
            all_domains.update(valid_domains)
            
            print(f"✓ {url} 采集成功")
    except:
        print(f"✗ {url} 采集失败")

print(f"\n共采集到 IP: {len(all_ips)} 个 | 域名: {len(all_domains)} 个")
print("开始测速（请耐心等待）...\n")

# ====================== 测速 ======================
print("正在测试 IP 延迟...")
with ThreadPoolExecutor(max_workers=30) as executor:
    future_to_ip = {executor.submit(ping_ip, ip): ip for ip in list(all_ips)[:80]}  # 限制测速数量
    
    ip_results = []
    for future in as_completed(future_to_ip):
        ip = future_to_ip[future]
        latency = future.result()
        if latency < 9999:
            ip_results.append((ip, latency))
        print(f"  IP: {ip:15}  延迟: {latency:6.1f} ms")

# 域名测速
print("\n正在测试 域名 延迟...")
with ThreadPoolExecutor(max_workers=20) as executor:
    future_to_domain = {executor.submit(test_domain, domain): domain for domain in list(all_domains)[:60]}
    
    domain_results = []
    for future in as_completed(future_to_domain):
        domain = future_to_domain[future]
        latency = future.result()
        if latency < 9999:
            domain_results.append((domain, latency))
        print(f"  域名: {domain:25}  延迟: {latency:6.1f} ms")

# ====================== 保存前10个 ======================
ip_results.sort(key=lambda x: x[1])      # 按延迟排序
domain_results.sort(key=lambda x: x[1])

with open('ip.txt', 'w', encoding='utf-8') as f:
    f.write("# === Cloudflare 低延迟 IP (前10) ===\n")
    for ip, latency in ip_results[:10]:
        f.write(f"{ip}   # {latency:.1f}ms\n")
    
    f.write("\n# === Cloudflare 低延迟 域名 (前10) ===\n")
    for domain, latency in domain_results[:10]:
        f.write(f"{domain}   # {latency:.1f}ms\n")

print("\n" + "="*50)
print("✅ 完成！已保存**延迟最低的前10个IP**和**前10个域名** 到 ip.txt")
print("="*50)
