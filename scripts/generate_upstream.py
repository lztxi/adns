import requests
import os

# Define DNS servers
TENCENT_DNS = 'https://doh.pub/dns-query'
BYTEDANCE_DNS = '180.184.1.1'
ALIBABA_DNS = 'h3://dns.alidns.com/dns-query'
CN_DNS = '202.98.0.68'

# Base URL for domain lists
BASE_URL = 'https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/'

# Categories to fetch
CATEGORIES = {
    'tencent': TENCENT_DNS,
    'bytedance': BYTEDANCE_DNS,
    'alibaba': ALIBABA_DNS
}

# Function to fetch and parse domain list (ignoring comments and attributes)
def fetch_domains(category):
    url = f'{BASE_URL}{category}'
    response = requests.get(url)
    response.raise_for_status()
    domains = set()
    for line in response.text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('regexp:') or line.startswith('keyword:'):
            continue  # Skip comments, regex, keywords; only full domains
        if line.startswith('full:'):
            domain = line.split('full:', 1)[1].strip()
        else:
            domain = line.strip()
        domains.add(domain)
    return domains

# Fetch specific company domains
company_domains = {}
for cat, dns in CATEGORIES.items():
    print(f'Fetching {cat} domains...')
    company_domains[cat] = fetch_domains(cat)

# Fetch CN domains
print('Fetching CN domains...')
cn_domains = fetch_domains('cn')

# Remove company-specific domains from general CN to avoid overlap
for cat_domains in company_domains.values():
    cn_domains -= cat_domains

# Function to generate upstream lines, grouping domains (max 50 per line)
def generate_upstream_lines(domains, dns_server, max_per_line=50):
    lines = []
    domain_list = sorted(domains)
    for i in range(0, len(domain_list), max_per_line):
        group = domain_list[i:i + max_per_line]
        domain_str = '/' + '/'.join(group) + '/'
        lines.append(f'[{domain_str}]{dns_server}')
    return lines

# Generate the file content
output_lines = []

# Add company-specific first (higher priority)
for cat, dns in CATEGORIES.items():
    if company_domains[cat]:
        output_lines.extend(generate_upstream_lines(company_domains[cat], dns))

# Add general CN last
if cn_domains:
    output_lines.extend(generate_upstream_lines(cn_domains, CN_DNS))

# Write to file
output_file = 'upstream_dns.txt'
with open(output_file, 'w') as f:
    f.write('\n'.join(output_lines) + '\n')

print(f'Generated {output_file} with {len(output_lines)} lines.')
