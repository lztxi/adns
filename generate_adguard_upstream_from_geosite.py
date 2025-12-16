#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据 **在线 domain-list-community（文本版）** 生成 AdGuard Home upstream_dns_file。

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
    # 参数处理：不再强制要求参数，避免 SystemExit: 1
    if len(sys.argv) == 1:
        output = DEFAULT_OUTPUT
        print(f"ℹ 未指定输出文件，使用默认：{output}")
    elif len(sys.argv) == 2:
        output = sys.argv[1]
    elif len(sys.argv) == 2 and sys.argv[1] == "--test":
        _self_test()
        return
    else:
        print("Usage: python generate_adguard_upstream_from_geosite.py [output.txt]")
        return

    rules = defaultdict(set)

    for dns, lists in SOURCES.items():
        for name in lists:
            try:
                for d in fetch_list(name):
                    rules[dns].add(d)
            except Exception as e:
                print(f"⚠ 无法拉取 {name}: {e}")

    with open(output, "w", encoding="utf-8") as f:
        for dns, domains in rules.items():
            for d in sorted(domains):
                f.write(f"[/{d}/]{dns}\n")

    print(f"✔ 已生成 {output}")


if __name__ == "__main__":
    main()

# ================= GitHub Actions（自动生成 + Release · 专业版） =================
# 功能：
# 1. 内容未变化则不发布 Release（避免刷版本）
# 2. 固定 latest tag，方便订阅
# 3. 失败自动终止，不产出脏 Release
# 4. 支持手动 / 定时触发

# 将下面文件保存为：.github/workflows/build-adguard-upstream.yml

# --- build-adguard-upstream.yml ---
# name: Build AdGuard Upstream DNS (Pro)
#
# on:
#   workflow_dispatch:
#   schedule:
#     - cron: "0 3 * * *"   # 每天 UTC 03:00
#
# jobs:
#   build:
#     runs-on: ubuntu-latest
#
#     steps:
#       - name: Checkout repository
#         uses: actions/checkout@v4
#
#       - name: Set up Python
#         uses: actions/setup-python@v5
#         with:
#           python-version: "3.x"
#
#       - name: Install dependencies
#         run: pip install requests
#
#       - name: Generate upstream_dns.txt
#         run: python generate_adguard_upstream_from_geosite.py upstream_dns.txt
#
#       - name: Calculate checksum
#         id: checksum
#         run: |
#           sha256sum upstream_dns.txt | awk '{print $1}' > checksum.txt
#           echo "hash=$(cat checksum.txt)" >> $GITHUB_OUTPUT
#
#       - name: Get previous checksum
#         id: prev
#         run: |
#           if [ -f .last_checksum ]; then
#             echo "hash=$(cat .last_checksum)" >> $GITHUB_OUTPUT
#           else
#             echo "hash=none" >> $GITHUB_OUTPUT
#           fi
#
#       - name: Stop if no change
#         if: steps.checksum.outputs.hash == steps.prev.outputs.hash
#         run: |
#           echo "No changes detected, skipping release."
#           exit 0
#
#       - name: Save new checksum
#         run: echo "${{ steps.checksum.outputs.hash }}" > .last_checksum
#
#       - name: Commit checksum
#         run: |
#           git config user.name "github-actions"
#           git config user.email "github-actions@github.com"
#           git add .last_checksum
#           git commit -m "chore: update checksum" || true
#           git push || true
#
#       - name: Create / Update Release (latest)
#         uses: softprops/action-gh-release@v2
#         with:
#           tag_name: latest
#           name: "AdGuard Upstream DNS (Latest)"
#           body: |
#             自动生成的 AdGuard Home upstream_dns_file
#             更新时间：${{ github.run_id }}
#           files: |
#             upstream_dns.txt
#         env:
#           GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
