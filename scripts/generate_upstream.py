import requests
import os
from datetime import datetime

# DNS 配置
TENCENT_DNS = 'https://doh.pub/dns-query'          # 腾讯 DoH
BYTEDANCE_DNS = '180.184.1.1'                      # 字节 IP
ALIBABA_DNS = 'https://dns.alidns.com/dns-query'   # 阿里 DoH
FALLBACK_DNS = '202.98.0.68'                       # 兜底

CATEGORIES = {
    'tencent': ('腾讯系', TENCENT_DNS),
    'bytedance': ('字节系', BYTEDANCE_DNS),
    'alibaba': ('阿里系', ALIBABA_DNS)
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
        original_line = line.strip()
        if not original_line:
            continue
        
        # 彻底跳过所有带 @ 或 include: 的行（@!cn 再见！！！）
        if '@' in original_line or original_line.startswith('include:'):
            continue
        
        # 跳过注释和其它特殊行
        if original_line.startswith(('#', 'regexp:', 'keyword:', 'attr:', 'full:')):
            continue
        
        # 处理 domain: 开头
        if original_line.startswith('domain:'):
            domain = original_line[7:].strip()
        else:
            domain = original_line.strip()
        
        # 只加纯域名（有.且不为空）
        if domain and '.' in domain and not domain.startswith('.'):
            domains.add(domain.lower())
    
    return domains

print("开始下载三大公司域名列表（已彻底过滤 @!cn 和 include）...")
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

output_lines = [
    "# AdGuardHome Upstream DNS 文件 - 自动生成（已彻底清除 @!cn）",
    f"# 更新时间: {update_time}",
    f"# 腾讯系: {stats.get('tencent', 0)} 域名 → DoH {TENCENT_DNS}",
    f"# 字节系: {stats.get('bytedance', 0)} 域名 → IP {BYTEDANCE_DNS}",
    f"# 阿里系: {stats.get('alibaba', 0)} 域名 → DoH {ALIBABA_DNS}",
    f"# 兜底规则: 其他所有域名 → {FALLBACK_DNS}",
    f"# 总域名数量（三大公司）: {total_domains}",
    f"# 总 upstream 条目: 0（下方计算）",
    ""
]

all_lines_count = 0

# 三大公司规则
for cat, (_, dns) in CATEGORIES.items():
    if company_domains[cat]:
        lines = generate_upstream_lines(company_domains[cat], dns)
        all_lines_count += len(lines)
        output_lines.extend(lines)
        output_lines.append("")

# 兜底规则
output_lines.append(f"# 兜底：所有剩余域名")
output_lines.append(f'[//]{FALLBACK_DNS}')
all_lines_count += 1

output_lines[7] = f"# 总 upstream 条目: {all_lines_count}"

with open('upstream_dns.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines) + '\n')

print(f"生成成功！已彻底清除所有 @!cn 和 include，共 {all_lines_count} 条规则")
