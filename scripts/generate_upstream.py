import requests
import os
from datetime import datetime

# DoH 配置（优先使用 DoH）
DOH_DNS = {
    'tencent': 'https://doh.pub/dns-query',          # 腾讯公共 DoH
    'bytedance': '180.184.1.1',  # 字节公共 DoH
    'alibaba': 'https://dns.alidns.com/dns-query'     # 阿里公共 DoH
}

CATEGORIES = {
    'tencent': ('腾讯系', DOH_DNS['tencent']),
    'bytedance': ('字节系', DOH_DNS['bytedance']),
    'alibaba': ('阿里系', DOH_DNS['alibaba'])
}

BASE_URL = 'https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/'

def fetch_domains(category):
    url = f'{BASE_URL}{category}'
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"下载 {category} 失败: {e}")
        return set()
    
    domains = set()
    for line in response.text.splitlines():
        line = line.strip()
        if not line or line.startswith(('#', 'include:', 'regexp:', 'keyword:', 'attr:', 'full:')):
            continue  # 严格过滤：跳过 include、regexp、keyword 等，只保留纯域名
        # 兼容 domain: 开头
        if line.startswith('domain:'):
            domain = line[7:].strip()
        else:
            domain = line.strip()
        if domain:
            domains.add(domain.lower())
    return domains

print("开始下载三大公司域名列表...")
company_domains = {}
total_domains = 0
stats = {}

for cat, (name, _) in CATEGORIES.items():
    domains = fetch_domains(cat)
    company_domains[cat] = domains
    count = len(domains)
    total_domains += count
    stats[cat] = count
    print(f"{name} 域名数量: {count}")

update_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

def generate_upstream_lines(domains, dns_server, max_per_line=50):
    lines = []
    domain_list = sorted(domains)
    for i in range(0, len(domain_list), max_per_line):
        group = domain_list[i:i + max_per_line]
        domain_str = '/' + '/'.join(group) + '/'
        lines.append(f'[{domain_str}]{dns_server}')
    return lines

# 生成内容头部
output_lines = [
    "# AdGuardHome Upstream DNS 文件 - 自动生成（仅三大公司 DoH）",
    f"# 更新时间: {update_time}",
    f"# 腾讯系域名: {stats.get('tencent', 0)} → {DOH_DNS['tencent']}",
    f"# 字节系域名: {stats.get('bytedance', 0)} → {DOH_DNS['bytedance']}",
    f"# 阿里系域名: {stats.get('alibaba', 0)} → {DOH_DNS['alibaba']}",
    f"# 总域名数量: {total_domains}",
    f"# 总 upstream 条目: 0（下方计算）",
    ""
]

all_lines_count = 0
for cat, (_, dns) in CATEGORIES.items():
    if company_domains[cat]:
        lines = generate_upstream_lines(company_domains[cat], dns)
        all_lines_count += len(lines)
        output_lines.extend(lines)
        output_lines.append("")  # 分隔

output_lines[6] = f"# 总 upstream 条目: {all_lines_count}"

# 写入文件
output_file = 'upstream_dns.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines) + '\n')

print(f"生成完成！共 {all_lines_count} 条 upstream 规则（仅三大公司 DoH），总覆盖 {total_domains} 个域名")
