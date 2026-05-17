import os
import requests
import re

# ==================== 核心配置与校验 ====================
CF_API_TOKEN = os.getenv('CF_API_TOKEN')

# 严密的网络协议格式匹配（只允许纯正的格式通过）
IPV4_REGEX = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')
IPV6_REGEX = re.compile(r'^(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}$')
DOMAIN_REGEX = re.compile(r'^(?:[a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}$')

def parse_ip_txt_by_blocks(url):
    """
    智能解析分类块！
    读取按性能指标清洗后的 ip.txt，并根据各区域标签精确定位数据
    """
    print(f"🔄 开始在线拉取和解构你的优选数据源...")
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    lines = [line.strip() for line in response.text.split('\n') if line.strip()]
    
    # 容器初始化
    blocks = {"telecom": [], "unicom": [], "mobile": [], "ipv6": [], "domain": []}
    current_block = None
    
    # 动态状态机：根据你在 ip.txt 中打好的标头进行精准切片
    for line in lines:
        if "TELECOM" in line.upper():
            current_block = "telecom"
            continue
        elif "UNICOM" in line.upper():
            current_block = "unicom"
            continue
        elif "MOBILE" in line.upper():
            current_block = "mobile"
            continue
        elif "IPV6" in line.upper():
            current_block = "ipv6"
            continue
        elif "DOMAIN" in line.upper():
            current_block = "domain"
            continue
        elif line.startswith("#"):
            continue # 跳过其他未定义注释
            
        # 往当前所在的区域灌入经格式校验的数据
        if current_block == "telecom" and IPV4_REGEX.match(line):
            blocks["telecom"].append(line)
        elif current_block == "unicom" and IPV4_REGEX.match(line):
            blocks["unicom"].append(line)
        elif current_block == "mobile" and IPV4_REGEX.match(line):
            blocks["mobile"].append(line)
        elif current_block == "ipv6" and IPV6_REGEX.match(line):
            blocks["ipv6"].append(line)
        elif current_block == "domain" and DOMAIN_REGEX.match(line):
            blocks["domain"].append(line)
            
    return blocks

# ==================== Cloudflare 底层 API 交互 ====================

def get_cloudflare_zone(api_token):
    headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}
    response = requests.get('https://api.cloudflare.com/client/v4/zones', headers=headers)
    response.raise_for_status()
    zones = response.json().get('result', [])
    if not zones:
        raise Exception("未能在你的账户下检测到绑定的域名，请确认 API 令牌权限")
    return zones[0]['id'], zones[0]['name']

def delete_existing_dns_records(api_token, zone_id, subdomain, domain, rtype):
    """清理该线路旧的重叠记录，保持域名解析文件纯净"""
    headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    while True:
        url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type={rtype}&name={record_name}'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        records = response.json().get('result', [])
        if not records:
            break
        for record in records:
            requests.delete(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}', headers=headers)
            print(f"🗑️ 已擦除陈旧的 [{rtype}] 记录: {subdomain} ➔ {record['content']}")

def add_cloudflare_dns_record(api_token, zone_id, subdomain, domain, rtype, content):
    """把最新排名的好节点推送到 Cloudflare 边缘服务器"""
    headers = {'Authorization': f'Bearer {api_token}', 'Content-Type': 'application/json'}
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    
    # 网络安全性强制过滤网，阻止潜在无效解析
    if rtype == "A" and content.endswith(('.0', '.255')):
        return

    data = {
        "type": rtype,
        "name": record_name,
        "content": content,
        "ttl": 1,          # 1 代表由 Cloudflare 自动管理生存周期 (Auto)
        "proxied": False  # 优选加速核心：必须关闭云朵代理，走直连模式
    }
    response = requests.post(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records', json=data, headers=headers)
    if response.status_code == 200:
        print(f"✅ 成功上架 [{rtype}] 线路: {subdomain}.{domain} ➔ {content}")
    else:
        print(f"❌ 上架失败 {subdomain} -> {content}: 错误码 {response.status_code}")

# ==================== 控制中枢 ====================
if __name__ == "__main__":
    if not CF_API_TOKEN:
        print("❌ 核心中断: 环境参量 'CF_API_TOKEN' 处于空白状态，请先在 Settings->Secrets 里添加。")
        exit(1)
        
    RAW_DATA_URL = 'https://raw.githubusercontent.com/YuTheGreat-ck/youxuanyuming/refs/heads/main/ip.txt'
    
    try:
        # 1. 自动握手并确认你的主控制域名 (如 myrrs.dpdns.org)
        zone_id, domain = get_cloudflare_zone(CF_API_TOKEN)
        print(f"🚀 成功对接 Cloudflare 顶层域名网: {domain}\n" + "="*60)
        
        # 2. 从你已经跑绿的 ip.txt 里把分类提取出来
        data_matrix = parse_ip_txt_by_blocks(RAW_DATA_URL)
        
        # 3. 规划二级域名矩阵
        # 针对不同网络环境定制的前 5 / 前 10 精准子域名分布：
        subdomain_tasks = [
            {"sub": "cf-telecom", "type": "A", "list": data_matrix["telecom"]},  # 电信最快前5个IPv4
            {"sub": "cf-unicom", "type": "A", "list": data_matrix["unicom"]},    # 联通最快前5个IPv4
            {"sub": "cf-mobile", "type": "A", "list": data_matrix["mobile"]},    # 移动最快前5个IPv4
            {"sub": "cf-v6", "type": "AAAA", "list": data_matrix["ipv6"]},       # 高速IPv6前5个 (用AAAA记录)
            {"sub": "best-domain", "type": "CNAME", "list": data_matrix["domain"]} # 速度前10域名 (用CNAME记录)
        ]
        
        # 4. 循环迭代清洗，同步发布
        for task in subdomain_tasks:
            if not task["list"]:
                print(f"⏩ 目标池 [{task['sub']}] 在 ip.txt 里未发现可用有效数据，安全跳过。")
                continue
                
            print(f"\n⚡ 正在洗牌并覆写子域名解析轨道: {task['sub']}.{domain}")
            # 先干掉这根轨道上以前残存的对应类型解析，防止记录重叠打架
            delete_existing_dns_records(CF_API_TOKEN, zone_id, task["sub"], domain, task["type"])
            
            # 将清洗出来最快的前几个节点注入
            for entry in task["list"]:
                add_cloudflare_dns_record(CF_API_TOKEN, zone_id, task["sub"], domain, task["type"], entry)
                
        print("\n🎉 酷！所有运营商分流及优选域名已全部按性能阶梯配置完毕。")
        
    except Exception as e:
        print(f"💥 极速流水线执行遭遇硬故障: {e}")
