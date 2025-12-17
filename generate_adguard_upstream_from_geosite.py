#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从官方 geosite.dat 生成 AdGuard Home upstream_dns_file
稳定 / 可 CI / 无 raw GitHub 依赖
"""

import sys
import struct
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

# geosite 分类 → DNS
SOURCES = {
    "tencent": DNS_TENCENT,
    "bytedance": DNS_BYTEDANCE,
    "alibaba": DNS_ALIBABA,
    "baidu": DNS_BAIDU,
    "xiaomi": DNS_XIAOMI,
    "oppo": DNS_OPPO,
    "apple-cn": DNS_APPLE_CN,
    "apple": DNS_APPLE_CN,
    "geolocation-cn": DNS_CN,
    "cn": DNS_CN,
}


def read_varint(data: bytes, offset: int):
    """读取 protobuf varint（最小实现）"""
    result = 0
    shift = 0
    while True:
        b = data[offset]
        offset += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, offset
        shift += 7


def parse_geosite(path: str) -> dict[str, set[str]]:
    """解析 geosite.dat（无 proto 依赖）"""
    with open(path, "rb") as f:
        data = f.read()

    rules: dict[str, set[str]] = defaultdict(set)
    i = 0
    current_tag = None

    while i < len(data):
        key = data[i]
        i += 1
        field = key >> 3
        wire = key & 7

        if wire == 2:  # length-delimited
            length, i = read_varint(data, i)
            chunk = data[i:i + length]
            i += length

            # tag name
            if field == 1:
                current_tag = chunk.decode("utf-8", errors="ignore")
            # domain
            elif field == 2 and current_tag in SOURCES:
                # domain message 内部：跳过 type，只取字符串
                try:
                    _, pos = read_varint(chunk, 0)
                    _, pos = read_varint(chunk, pos)
                    domain = chunk[pos:].decode("utf-8", errors="ignore")
                    rules[SOURCES[current_tag]].add(domain)
                except Exception:
                    pass
        else:
            # skip other wire types
            if wire == 0:
                _, i = read_varint(data, i)
            elif wire == 1:
                i += 8
            elif wire == 5:
                i += 4
            else:
                break

    return rules


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python generate_adguard_upstream_from_geosite.py geosite.dat output.txt")
        sys.exit(1)

    geosite_path = sys.argv[1]
    output = sys.argv[2]

    rules = parse_geosite(geosite_path)

    domain_count = 0
    with open(output, "w", encoding="utf-8") as f:
        for dns, domains in rules.items():
            for d in sorted(domains):
                f.write(f"[/{d}/]{dns}\n")
                domain_count += 1

    if domain_count == 0:
        print("❌ geosite.dat 解析失败：未生成任何域名")
        sys.exit(2)

    with open("stats.json", "w", encoding="utf-8") as s:
        s.write(
            "{\n"
            f"  \"domains\": {domain_count},\n"
            f"  \"updated\": \"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\"\n"
            "}\n"
        )

    print(f"✔ 已生成 {output}（{domain_count} domains）")


if __name__ == "__main__":
    main()
