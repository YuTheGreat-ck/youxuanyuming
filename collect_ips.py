import requests
import re
import os
import time
import ipaddress

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ========= 配置 =========

URLS = [
    "https://api.uouin.com/cloudflare.html",
    "https://vps789.com/cfip/?remarks=domain"
]

OUTPUT_FILE = "ip.txt"

MAX_IPV4 = 150
MAX_IPV6 = 50
MAX_DOMAIN = 100


# ========= Session =========

session = requests.Session()

retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry)

session.mount("http://", adapter)
session.mount("https://", adapter)

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36"
    )
})


# ========= 正则 =========

IPV4_PATTERN = re.compile(
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
)

IPV6_PATTERN = re.compile(
    r'\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b'
)

DOMAIN_PATTERN = re.compile(
    r'\b(?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\b'
)


# ========= 工具函数 =========

def is_valid_ip(ip):

    try:
        ipaddress.ip_address(ip)
        return True
    except:
        return False


def sort_ips(ip_list):

    return sorted(
        ip_list,
        key=lambda x: ipaddress.ip_address(x)
    )


# ========= 删除旧文件 =========

if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)


# ========= 开始采集 =========

all_ipv4 = set()
all_ipv6 = set()
all_domains = set()

print("开始采集 Cloudflare 数据...\n")

for url in URLS:

    print(f"正在采集: {url}")

    try:

        r = session.get(
            url,
            timeout=20
        )

        if r.status_code != 200:
            print(f"  ✗ 状态码异常: {r.status_code}")
            continue

        text = r.text

        # IPv4
        ipv4s = {
            ip for ip in IPV4_PATTERN.findall(text)
            if is_valid_ip(ip)
        }

        # IPv6
        ipv6s = {
            ip for ip in IPV6_PATTERN.findall(text)
            if is_valid_ip(ip)
        }

        # 域名
        domains = {
            domain.lower().strip()
            for domain in DOMAIN_PATTERN.findall(text)
        }

        all_ipv4.update(ipv4s)
        all_ipv6.update(ipv6s)
        all_domains.update(domains)

        print(
            f"  ✓ IPv4:{len(ipv4s)} "
            f"IPv6:{len(ipv6s)} "
            f"域名:{len(domains)}"
        )

    except Exception as e:

        print(f"  ✗ 采集失败: {e}")

    time.sleep(1)


# ========= 排序 =========

all_ipv4 = sort_ips(all_ipv4)
all_ipv6 = sort_ips(all_ipv6)
all_domains = sorted(all_domains)


# ========= 保存 =========

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    if all_ipv4:

        f.write("# === Cloudflare IPv4 ===\n")

        for ip in all_ipv4[:MAX_IPV4]:
            f.write(ip + "\n")

        f.write("\n")

    if all_ipv6:

        f.write("# === Cloudflare IPv6 ===\n")

        for ip in all_ipv6[:MAX_IPV6]:
            f.write(ip + "\n")

        f.write("\n")

    if all_domains:

        f.write("# === Cloudflare Domain ===\n")

        for domain in all_domains[:MAX_DOMAIN]:
            f.write(domain + "\n")


# ========= 输出 =========

print("\n采集完成")
print(f"IPv4: {len(all_ipv4)}")
print(f"IPv6: {len(all_ipv6)}")
print(f"域名: {len(all_domains)}")
print(f"输出文件: {OUTPUT_FILE}")
