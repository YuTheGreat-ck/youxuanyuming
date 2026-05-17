import os
import requests

def get_ip_list(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text.strip().split('\n')

def get_cloudflare_zone(api_token):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get('https://api.cloudflare.com/client/v4/zones', headers=headers)
    response.raise_for_status()
    zones = response.json().get('result', [])
    if not zones:
        raise Exception("No zones found")
    return zones[0]['id'], zones[0]['name']

def delete_existing_dns_records(api_token, zone_id, subdomain, domain):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    while True:
        response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={record_name}', headers=headers)
        response.raise_for_status()
        records = response.json().get('result', [])
        if not records:
            break
        for record in records:
            delete_response = requests.delete(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}', headers=headers)
            delete_response.raise_for_status()
            print(f"Del {subdomain}:{record['id']}")

def update_cloudflare_dns(ip_list, api_token, zone_id, subdomain, domain):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    added_count = 0
    for ip in ip_list[:150]:   # 限制最多150条记录，避免太多
        if not ip or ip.endswith(('.0', '.255')):
            continue
        data = {
            "type": "A",
            "name": record_name,
            "content": ip,
            "ttl": 1,
            "proxied": False
        }
        response = requests.post(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records', json=data, headers=headers)
        if response.status_code == 200:
            print(f"Add {subdomain}.{domain} → {ip}")
            added_count += 1
        else:
            print(f"Failed {subdomain} {ip}: {response.status_code}")
    print(f"子域名 {subdomain} 共添加 {added_count} 条记录")

if __name__ == "__main__":
    api_token = os.getenv('CF_API_TOKEN')
    
    # === 为你的域名 myrrs.dpdns.org 配置的子域名 ===
    subdomain_ip_mapping = {
        'cf': 'https://raw.githubusercontent.com/YuTheGreat-ck/youxuanyuming/refs/heads/main/ip.txt',
        'best': 'https://raw.githubusercontent.com/YuTheGreat-ck/youxuanyuming/refs/heads/main/ip.txt',
        'github': 'https://raw.githubusercontent.com/YuTheGreat-ck/youxuanyuming/refs/heads/main/ip.txt',   # 推荐用于 GitHub
    }
    
    try:
        zone_id, domain = get_cloudflare_zone(api_token)
        print(f"✅ 当前操作域名: {domain}")
        
        for subdomain, url in subdomain_ip_mapping.items():
            print(f"\n🔄 开始更新: {subdomain}.{domain}")
            ip_list = get_ip_list(url)
            delete_existing_dns_records(api_token, zone_id, subdomain, domain)
            update_cloudflare_dns(ip_list, api_token, zone_id, subdomain, domain)
            
        print("\n🎉 所有子域名更新完成！")
            
    except Exception as e:
        print(f"❌ Error: {e}")
