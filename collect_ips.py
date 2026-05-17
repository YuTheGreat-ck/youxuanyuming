import requests
import re
import ipaddress
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========= 1. 全局标准配置 =========
OUTPUT_FILE = "ip.txt"

# 增加输出数量：从原本的 5 改为 10
LIMIT_COUNT = 10 

IPV4_REGEX = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
IPV6_REGEX = re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

session = requests.Session()
retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))
session.headers.update(HEADERS)

def is_valid_ipv4(ip):
    try:
        parsed = ipaddress.ip_address(ip)
        return parsed.version == 4 and not parsed.is_private and not ip.endswith(('.0', '.255'))
    except:
        return False

def is_valid_ipv6(ip):
    try:
        parsed = ipaddress.ip_address(ip)
        return parsed.version == 6 and not parsed.is_private
    except:
        return False

# ========= 2. 新的多源聚合采集（极大提升准确度） =========
def fetch_ips_from_public_pools():
    """从全网维护最频繁的 Cloudflare 优选公共源拉取最新真实测速数据"""
    print("🔄 正在从全网多节点聚合真实的优选 IP 数据...")
    
    # 准备高可用的优选公开源（这些源由全天候高性能服务器测速并几分钟更新一次）
    sources = [
        "https://vps789.com/api/cfip/getIpList",
        "https://ip.164746.xyz/ip.txt",
        "https://cf.090227.xyz/ip.txt"
    ]
    
    pool = {"telecom": [], "unicom": [], "mobile": [], "ipv6": []}
    
    # 策略 1: 优先尝试高精度分类接口
    try:
        r = session.get("https://vps789.com/api/cfip/getIpList", timeout=10)
        if r.status_code == 200:
            raw_list = r.json().get("data", [])
            # 严格根据公开测速源的真实下载速度重排
            raw_list = sorted(raw_list, key=lambda k: float(k.get("download_speed", 0)), reverse=True)
            
            for item in raw_list:
                ip = str(item.get("ip", "")).strip()
                line = str(item.get("line", ""))
                if "电信" in line and is_valid_ipv4(ip): pool["telecom"].append(ip)
                elif "联通" in line and is_valid_ipv4(ip): pool["unicom"].append(ip)
                elif "移动" in line and is_valid_ipv4(ip): pool["mobile"].append(ip)
                elif is_valid_ipv6(ip): pool["ipv6"].append(ip)
                
            if pool["telecom"]: 
                print("✓ 成功从高级测速矩阵获取分流数据")
                return pool
    except Exception as e:
        print(f"⚠️ 高级接口暂时不可用: {e}，正在切换到备用文本行扫描...")

    # 策略 2: 文本行兜底扫描（如果上一步空了，从其他公开测速榜单实时提取）
    for url in sources[1:]:
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                lines = r.text.split('\n')
                for line in lines:
                    line = line.strip()
                    # 借助原项目的多源数据特征提取
                    if is_valid_ipv4(line):
                        # 如果没有详细分流，暂时均匀分配或作为基础池
                        pool["telecom"].append(line)
                        pool["unicom"].append(line)
                        pool["mobile"].append(line)
                    elif is_valid_ipv6(line):
                        pool["ipv6"].append(line)
                if pool["telecom"]:
                    break
        except:
            continue
            
    return pool

def get_vps789_domains():
    print("🔄 正在拉取最新的优质边缘 CNAME 域名...")
    domain_pool = []
    try:
        session.headers.update({"Referer": "https://vps789.com/cfip/?remarks=domain"})
        r = session.get("https://vps789.com/api/cfip/getDomainList", timeout=10)
        if r.status_code == 200:
            raw_list = r.json().get("data", [])
            sorted_domains = sorted(raw_list, key=lambda d: float(d.get("download_speed", 0)), reverse=True)
            domain_pool = [str(item["domain"]).strip().lower() for item in sorted_domains if item.get("domain")]
    except Exception as e:
        print(f"⚠️ 域名池拉取受阻: {e}")
    return domain_pool

# ========= 3. 主控流程 =========
if __name__ == "__main__":
    raw_ips = fetch_ips_from_public_pools()
    domains = get_vps789_domains()
    
    # 终极硬兜底（只在全网所有测速站全部宕机时生效，更新为较新的 Anycast 节点）
    if not raw_ips["telecom"]:
        raw_ips["telecom"] = ["141.101.115.1", "141.101.121.2", "141.101.123.3", "190.93.244.4", "190.93.246.5"]
        raw_ips["unicom"] = ["108.162.192.1", "108.162.193.2", "108.162.194.3", "162.159.200.4", "162.159.204.5"]
        raw_ips["mobile"] = ["172.64.32.1", "172.64.36.2", "162.159.210.4", "162.159.211.5", "162.159.208.1"]
        raw_ips["ipv6"] = ["2a06:98c1:3120::1", "2a06:98c1:3121::2"]
    if not domains:
        domains = ["cf.090227.xyz", "bestcf.cfcs.us.kg", "cdn.cloudflare.top"]

    # 规范化写入，切片大小直接使用 LIMIT_COUNT (10个)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# === TELECOM TOP {LIMIT_COUNT} ===\n")
        for ip in raw_ips["telecom"][:LIMIT_COUNT]: f.write(ip + "\n")
        
        f.write(f"\n# === UNICOM TOP {LIMIT_COUNT} ===\n")
        for ip in raw_ips["unicom"][:LIMIT_COUNT]: f.write(ip + "\n")
        
        f.write(f"\n# === MOBILE TOP {LIMIT_COUNT} ===\n")
        for ip in raw_ips["mobile"][:LIMIT_COUNT]: f.write(ip + "\n")
        
        f.write(f"\n# === IPV6 TOP {LIMIT_COUNT} ===\n")
        for ip in raw_ips["ipv6"][:LIMIT_COUNT]: f.write(ip + "\n")
        
        f.write(f"\n# === DOMAIN TOP {LIMIT_COUNT} ===\n")
        for dm in domains[:LIMIT_COUNT]: f.write(dm + "\n")

    print(f"🎉 完美的性能指标清洗已全部结束！规范格式已成功写入：{OUTPUT_FILE}")
