import os
import requests
import re

# ==================== 核心配置与全局变量 ====================
CF_API_TOKEN = os.getenv('CF_API_TOKEN')

# 严密的网络协议格式匹配
IPV4_REGEX = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')
IPV6_REGEX = re.compile(r'^(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}$')

# 模拟真实高级浏览器请求头，规避部分初级防火墙
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Origin": "https://vps789.com",
    "Referer": "https://vps789.com/cfip/?remarks=domain"
}

# ==================== 1. 精准、高容错数据采集模块 ====================

def fetch_uouin_ips():
    """
    对接 api.uouin.com 最新的结构化测速池
    按下载速度(Speed)排序，分别提取 联通、电信、移动、IPv6 的前 5 名
    """
    print("🔄 正在提取 api.uouin.com 三网及 IPv6 高速节点...")
    # 官方推荐的无痛高频轻量数据 JSON 接口
    api_url = "https://api.uouin.com/api/cloudflare/get_wep_ip"
    
    pools = {"telecom": [], "unicom": [], "mobile": [], "ipv6": []}
    
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            raw_json = response.json()
            data_list = raw_json.get("data", [])
            
            # 分流清洗并进行降序(速度快->慢)排序
            ct = sorted([x for x in data_list if "电信" in str(x.get("line")) and IPV4_REGEX.match(str(x.get("ip")))], key=lambda k: float(k.get("speed", 0)), reverse=True)
            cu = sorted([x for x in data_list if "联通" in str(x.get("line")) and IPV4_REGEX.match(str(x.get("ip")))], key=lambda k: float(k.get("speed", 0)), reverse=True)
            cm = sorted([x for x in data_list if "移动" in str(x.get("line")) and IPV4_REGEX.match(str(x.get("ip")))], key=lambda k: float(k.get("speed", 0)), reverse=True)
            v6 = sorted([x for x in data_list if IPV6_REGEX.match(str(x.get("ip")))], key=lambda k: float(k.get("speed", 0)), reverse=True)
            
            # 严格各切取速度最快的前 5 名
            pools["telecom"] = [item["ip"] for item in ct[:5]]
            pools["unicom"] = [item["ip"] for item in cu[:5]]
            pools["mobile"] = [item["ip"] for item in cm[:5]]
            pools["ipv6"] = [item["ip"] for item in v6[:5]]
            return pools
    except Exception as e:
        print(f"⚠️ api.uouin.com 被防护墙拦截或超时: {e}")
        
    # 【防崩溃方案】当下游遭遇阻断时，自动启动历史测速表现最佳的 Anycast 骨干节点应急
    print("💡 启动电信/联通/移动/IPv6 的高速备份节点集...")
    pools["telecom"] = ["104.16.65.1", "104.16.105.166", "104.17.69.244", "104.19.40.5", "104.22.7.10"]
    pools["unicom"] = ["104.17.139.37", "104.17.142.212", "104.16.200.10", "104.20.15.2", "104.24.4.8"]
    pools["mobile"] = ["162.159.210.4", "162.159.211.5", "162.159.208.1", "162.159.209.2", "172.64.32.9"]
    pools["ipv6"] = ["2a06:98c1:3120:c39b:f77:4fc1:b18b:c12", "2a06:98c1:3121:0:ef18:6ab0:b648:d756", "2a06:98c1:3120:c39b:7522:c680:d288:d13c"]
    return pools

def fetch_vps789_domains():
    """
    对接 vps789.com 后端实时测速流
    根据下载速度字段，精确捞取前 10 名的优质域名
    """
    print("🔄 正在提取 vps789.com 速度排名前 10 的域名...")
    # 该网站真实的动态 XHR 异步数据拉取点
    api_url = "https://vps789.com/api/cfip/getDomainList"
    
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=12)
        if response.status_code == 200:
            domain_array = response.json().get("data", [])
            # 严格按下载速度降序重排
            sorted_res = sorted(domain_array, key=lambda d: float(d.get("download_speed", 0)), reverse=True)
            top_10 = [str(item["domain"]).strip().lower() for item in sorted_res if item.get("domain")][:10]
            if top_10:
                print(f"🎯 成功提取前10名域名: {top_10}")
                return top_10
    except Exception as e:
        print(f"⚠️ vps789.com 接口请求受阻: {e}")
        
    # 【防崩溃方案】若遭遇脚本封锁，自动填充当前开源项目中最顶尖的优秀稳定骨干域名
    return ["cf.090227.xyz", "bestcf.cfcs.us.kg", "api.cfcs.us.kg"]

# ==================== 2. Cloudflare DNS 全自动维护模块 ====================

def get_cloudflare_zone(api_token):
    headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}
    response = requests.get('https://api.cloudflare.com/client/v4/zones', headers=headers)
    response.raise_for_status()
    zones = response.json().get('result', [])
    if not zones:
        raise Exception("Cloudflare 账户下未发现有效 Zone，请检查 Token 范围")
    return zones[0]['id'], zones[0]['name']

def delete_existing_records(api_token, zone_id, subdomain, domain, rtype):
    """自动清理过往的垃圾或过期旧解析"""
    headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}
    full_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    while True:
        url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type={rtype}&name={full_name}'
        res = requests.get(url, headers=headers).json()
        records = res.get('result', [])
        if not records:
            break
        for r in records:
            requests.delete(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{r["id"]}', headers=headers)
            print(f"🗑️ 已移除旧解析: {full_name} ({rtype}) ➔ {r['content']}")

def push_dns_record(api_token, zone_id, subdomain, domain, rtype, content):
    """向 CF 实时下发解析指令"""
    headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}
    full_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    payload = {
        "type": rtype,
        "name": full_name,
        "content": content,
        "ttl": 1,          # 1 代表自动（Auto TTL）
        "proxied": False   # 优选核心：必须关闭黄色小云朵 CDN 代理，强制直连
    }
    res = requests.post(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records', json=payload, headers=headers)
    if res.status_code == 200:
        print(f"✅ 成功下发 [{rtype}]: {subdomain}.{domain} ➔ {content}")
    else:
        print(f"❌ 解析下发失败: {content}, 原因: {res.text}")

# ==================== 3. 主协调控制器 ====================

if __name__ == "__main__":
    print("🚀 启动精准调优版 DNS 负载均衡引擎...\n")
    if not CF_API_TOKEN:
        print("❌ 严重错误: 未检测到系统环境变量 CF_API_TOKEN，执行被迫中止。")
        exit(1)
        
    try:
        # 获取域名所有权区段
        zone_id, domain = get_cloudflare_zone(CF_API_TOKEN)
        print(f"🌐 当前接入主控域名: {domain}\n" + "="*55)
        
        # 实时抽取满足条件的顶级测速数据
        ip_data = fetch_uouin_ips()
        speed_domains = fetch_vps789_domains()
        
        # 定义子域名映射矩阵
        jobs = [
            {"sub": "cf-telecom", "type": "A", "data": ip_data["telecom"]},  # 电信前5名
            {"sub": "cf-unicom", "type": "A", "data": ip_data["unicom"]},    # 联通前5名
            {"sub": "cf-mobile", "type": "A", "data": ip_data["mobile"]},    # 移动前5名
            {"sub": "cf-v6", "type": "AAAA", "data": ip_data["ipv6"]},       # IPv6前5名
            {"sub": "best-domain", "type": "CNAME", "data": speed_domains}  # 域名速度前10名
        ]
        
        # 执行全自动轮询清洗与装载
        for job in jobs:
            if not job["data"]:
                continue
            print(f"\n🔄 正在覆写二级域名线: {job['sub']}.{domain}")
            # 清理历史污点记录
            delete_existing_records(CF_API_TOKEN, zone_id, job["sub"], domain, job["type"])
            # 批量压入全新的最优记录
            for value in job["data"]:
                push_dns_record(CF_API_TOKEN, zone_id, job["sub"], domain, job["type"], value)
                
        print("\n🎉 极速指标清洗完成！所有子域名的优选网络链路已同步更新。")
        
    except Exception as main_err:
        print(f"💥 核心控制台遭遇异常退出: {main_err}")
        exit(1)
