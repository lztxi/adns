import requests
import os
from datetime import datetime
import re

# DNS 配置
TENCENT_DNS = 'https://doh.pub/dns-query'
BYTEDANCE_DNS = '180.184.1.1'
ALIBABA_DNS = 'h3://dns.alidns.com/dns-query'
CN_DNS = '202.98.0.68'

BASE_URL = 'https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/'

CATEGORIES = {
    'tencent': ('腾讯系', TENCENT_DNS),
    'bytedance': ('字节系', BYTEDANCE_DNS),
    'alibaba': ('阿里系', ALIBABA_DNS)
}

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
        if not line or line.startswith(('#', 'regexp:', 'keyword:')):
            continue
        if line.startswith('full:'):
            domain = line.split('full:', 1)[1].strip()
        elif line.startswith('domain:'):
            domain = line.split('domain:', 1)[1].strip()
        else:
            domain = line.strip()
        if domain:
            domains.add(domain.lower())  # 统一小写
    return domains

print("开始下载域名列表...")
company_domains = {}
total_company = 0
stats = {}

for cat, (name, _) in CATEGORIES.items():
    domains = fetch_domains(cat)
    company_domains[cat] = domains
    count = len(domains)
    total_company += count
    stats[cat] = count
    print(f"{name} 域名数量: {count}")

cn_domains = fetch_domains('cn')
for domains in company_domains.values():
    cn_domains -= domains  # 去重，避免公司域名重复走 CN DNS
cn_count = len(cn_domains)
stats['cn'] = cn_count
print(f"中国大陆其他域名数量: {cn_count}")

update_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

def generate_upstream_lines(domains, dns_server, max_per_line=50):
    lines = []
    domain_list = sorted(domains)
    for i in range(0, len(domain_list), max_per_line):
        group = domain_list[i:i + max_per_line]
        domain_str = '/' + '/'.join(group) + '/'
        lines.append(f'[{domain_str}]{dns_server}')
    return lines

# 生成 upstream_dns.txt 内容
output_lines = [
    "# AdGuardHome Upstream DNS 文件 - 自动生成",
    f"# 更新时间: {update_time}",
    f"# 腾讯系域名: {stats.get('tencent', 0)}",
    f"# 字节系域名: {stats.get('bytedance', 0)}",
    f"# 阿里系域名: {stats.get('alibaba', 0)}",
    f"# 中国大陆其他域名: {cn_count}",
    f"# 总域名数量: {total_company + cn_count}",
    f"# 总 upstream 条目: 0（下方计算）",
    ""
]

all_lines_count = 0
for cat, (_, dns) in CATEGORIES.items():
    if company_domains[cat]:
        lines = generate_upstream_lines(company_domains[cat], dns)
        all_lines_count += len(lines)
        output_lines.extend(lines)
        output_lines.append("")

if cn_domains:
    lines = generate_upstream_lines(cn_domains, CN_DNS)
    all_lines_count += len(lines)
    output_lines.extend(lines)

output_lines[7] = f"# 总 upstream 条目: {all_lines_count}"

output_file = 'upstream_dns.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines) + '\n')

print(f"生成完成！共 {all_lines_count} 条 upstream 规则")

# 更新 README.md
readme_path = 'README.md'
if not os.path.exists(readme_path):
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("# AdGuardHome Upstream DNS 项目\n\n## 最新统计\n\n（首次生成）\n")

with open(readme_path, 'r', encoding='utf-8') as f:
    readme_content = f.read()

stats_section = f"""## 最新统计

- 更新时间: {update_time}
- 腾讯系域名: {stats.get('tencent', 0)}
- 字节系域名: {stats.get('bytedance', 0)}
- 阿里系域名: {stats.get('alibaba', 0)}
- 中国大陆其他域名: {cn_count}
- 总域名数量: {total_company + cn_count}
- 总 upstream 条目: {all_lines_count}
"""

if re.search(r'## 最新统计', readme_content):
    readme_content = re.sub(r'## 最新统计\n.*?(?=##|$)', stats_section.strip(), readme_content, flags=re.DOTALL)
else:
    readme_content = readme_content.rstrip() + '\n\n' + stats_section

with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_content.strip() + '\n')

print("README.md 已成功更新统计信息！")
