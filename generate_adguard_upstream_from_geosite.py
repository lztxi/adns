#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据在线 domain-list-community 生成 AdGuard Home upstream_dns_file
并输出统计信息供 README / CI 使用
"""

import sys
import requests
from collections import defaultdict
from datetime import datetime, timezone

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
# domain-list-community 已迁移到 dat 结构，使用 data 子目录下的 plain 列表
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


def fetch_list(name: str) -> list[str]:
    """
    从 domain-list-community 拉取单个分类文件
    自动兼容 404 / 仓库结构变更
    """
    url = f"{BASE}/{name}"
    print(f"↓ 拉取 {name}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    domains: list[str] = []
    for raw in r.text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("domain:"):
            domains.append(line.split(":", 1)[1])
    return domains


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python generate_adguard_upstream_from_geosite.py output.txt")
        sys.exit(1)

    output = sys.argv[1]
    rules: dict[str, set[str]] = defaultdict(set)

    for dns, lists in SOURCES.items():
        for name in lists:
            try:
                for d in fetch_list(name):
                    rules[dns].add(d)
            except Exception as e:
                print(f"⚠ 无法拉取 {name}: {e}")

    domain_count = 0

    # ===== 生成 upstream_dns.txt =====
    with open(output, "w", encoding="utf-8") as f:
        for dns, domains in rules.items():
            for d in sorted(domains):
                line = "[/" + d + "/]" + dns + "\n"
                f.write(line)
                domain_count += 1

    # ===== 生成统计信息 =====
    stats = {
        "domains": domain_count,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    with open("stats.json", "w", encoding="utf-8") as s:
        s.write(
            "{\n"
            f"  \"domains\": {stats['domains']},\n"
            f"  \"updated\": \"{stats['updated']}\"\n"
            "}\n"
        )

    print(f"✔ 已生成 {output}（{domain_count} domains）")


if __name__ == "__main__":
    main()
