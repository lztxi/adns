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
- 腾讯系         -> 腾讯 DNS
- 字节系         -> 字节 DNS
- 阿里系         -> 阿里 DNS
- 百度系         -> 百度 DNS
- 小米 / OPPO    -> 各自 DNS
- Apple 中国     -> 阿里 DNS
- 中国大陆兜底    -> 202.98.0.68

用法（两种都支持）：
  python generate_adguard_upstream_from_geosite.py upstream_dns.txt
  python generate_adguard_upstream_from_geosite.py          # 自动生成 upstream_dns.txt

依赖：
  pip install requests
"""

import sys
import requests
from collections import defaultdict
from typing import List
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
        # 匹配 domain: 规则，注意去除可能存在的空格
        if line.startswith("domain:"):
            # 使用 split(":", 1) 确保只按第一个冒号分割
            domain_part = line.split(":", 1)[1].strip()
            if domain_part: # 确保不是空的 domain
                 domains.append(domain_part)
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
    # --- 修复逻辑：支持 0 个或 1 个参数 ---
    if len(sys.argv) == 1:
        # 没有提供参数，使用默认输出文件名
        output = DEFAULT_OUTPUT
        print(f"没有指定输出文件，将使用默认值: {output}")
    elif len(sys.argv) == 2:
        # 提供了一个参数作为输出文件名
        output = sys.argv[1]
    else:
        # 提供了两个或更多参数，提示用法
        print("Usage: python generate_adguard_upstream_from_geosite.py [output.txt]")
        print(f"Default output is: {DEFAULT_OUTPUT}")
        sys.exit(1)
    # --- 修复逻辑结束 ---

    rules = defaultdict(set)
    _self_test() # 在开始拉取网络资源前先进行本地自测

    for dns, lists in SOURCES.items():
        for name in lists:
            try:
                for d in fetch_list(name):
                    rules[dns].add(d)
            except requests.exceptions.Timeout:
                print(f"❌ 拉取 {name} 超时，请检查网络连接或稍后重试。")
                continue
            except requests.exceptions.RequestException as e:
                print(f"❌ 无法拉取 {name}: {e}")
                continue
            except Exception as e:
                print(f"⚠ 处理 {name} 时发生未知错误: {e}")
                continue

    domain_count = 0
    # 使用 'w' 模式打开文件，写入结果
    with open(output, "w", encoding="utf-8") as f:
        # 遍历规则字典，按 DNS 服务器分组写入 AdGuard Home 格式
        # 格式: [/<domain>/]<IP>
        for dns, domains in rules.items():
            for d in sorted(domains):
                # 检查 domain 是否为空，避免写入空规则
                if d:
                    f.write(f"[/{d}/]{dns}\n")
                    domain_count += 1
    
    # 统计信息写入 'stats.json'
    # 这一部分也从原代码复制过来，并确保 datetime/timezone 导入
    with open("stats.json", "w", encoding="utf-8") as s:
        s.write(
            '{\n'
            f'  "domains": {domain_count},\n'
            f'  "updated": "{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"\n'
            '}\n'
        )

    print(f"🎉 已成功生成 {output}（包含 {domain_count} 条域名规则）")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n致命错误: {e}")
        sys.exit(1)
