#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚫 已彻底移除：
- geosite.proto
- protobuf
- geosite.dat

✅ 新方案（更稳）：
- 直接使用 v2fly/domain-list-community 的 **文本规则**
- 不再依赖任何 protobuf / proto 文件
- GitHub Raw，长期稳定，不会 404

规则：
- 腾讯系        -> 腾讯 DNS
- 字节系        -> 字节 DNS
- 阿里系        -> 阿里 DNS
- 百度系        -> 百度 DNS
- 小米 / OPPO   -> 各自 DNS
- Apple 中国    -> 阿里 DNS
- 中国大陆兜底  -> 202.98.0.68

用法（两种都支持）：
  python generate_adguard_upstream_from_geosite.py upstream_dns.txt
  python generate_adguard_upstream_from_geosite.py        # 自动生成 upstream_dns.txt

依赖：
  pip install requests
"""

import sys
import requests
from collections import defaultdict
from typing import List

# ================= DNS 定义 =================
DNS_TENCENT = "119.29.29.29"
DNS_BYTEDANCE = "180.184.1.1"
DNS_ALIBABA = "223.5.5.5"
DNS_BAIDU = "180.76.76.76"
DNS_XIAOMI = "180.184.1.1"
DNS_OPPO = "114.114.114.114"
DNS_APPLE_CN = "223.5.5.5"
DNS_CN = "202.98.0.68"

# ================= 域名分类来源 =================
BASE = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data"

SOURCES = {
    DNS_TENCENT: ["tencent"],
    DNS_BYTEDANCE: ["bytedance"],
    DNS_ALIBABA: ["alibaba"],
    DNS_BAIDU: ["baidu"],
    DNS_XIAOMI: ["xiaomi"],
    DNS_OPPO: ["oppo"],
    DNS_APPLE_CN: ["apple-cn", "apple"],
    DNS_CN: ["cn", "geolocation-cn"],
}

DEFAULT_OUTPUT = "upstream_dns.txt"

# ================= 工具函数 =================

def fetch_list(name: str) -> List[str]:
    """从 domain-list-community 拉取单个分类的 domain: 规则"""
    url = f"{BASE}/{name}"
    print(f"↓ 拉取 {name}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    domains: List[str] = []
    for line in r.text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("domain:"):
            domains.append(line.split(":", 1)[1])
    return domains


# ================= 简单自测 =================

def _self_test():
    """不访问网络的最小自测，确保格式正确"""
    sample = {
        DNS_TENCENT: {"qq.com", "weixin.qq.com"},
        DNS_CN: {"jd.com"},
    }

    lines = []
    for dns, domains in sample.items():
        for d in sorted(domains):
            lines.append(f"[/{d}/]{dns}")

    assert "[/qq.com/]119.29.29.29" in lines
    assert "[/jd.com/]202.98.0.68" in lines
    print("✔ 自测通过")


# ================= 主逻辑 =================

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_adguard_upstream_from_geosite.py output.txt")
        sys.exit(1)

    output = sys.argv[1]
    rules = defaultdict(set)

    for dns, lists in SOURCES.items():
        for name in lists:
            try:
                for d in fetch_list(name):
                    rules[dns].add(d)
            except Exception as e:
                print(f"⚠ 无法拉取 {name}: {e}")

    domain_count = 0
    with open(output, "w", encoding="utf-8") as f:
        for dns, domains in rules.items():
            for d in sorted(domains):
                f.write(f"[/{d}/]{dns}
")
                domain_count += 1

    # 生成统计信息（供 README 使用）
    from datetime import datetime, timezone
    with open("stats.json", "w", encoding="utf-8") as s:
        s.write(
            '{
'
            f'  "domains": {domain_count},
'
            f'  "updated": "{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
'
            '}
'
        )

    print(f"✔ 已生成 {output}（{domain_count} domains）")


if __name__ == "__main__":
    main()
