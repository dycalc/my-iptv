import re
import urllib.request

# 数据源（auflute 的上海联通内网源）
ORIGINAL_M3U_URL = "https://raw.githubusercontent.com/auflute/IPTV-Unicom-Shanghai/main/unicom-sha-local/unicom.m3u"
# 台标 CDN 前缀（使用 jsdelivr）
LOGO_BASE = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/tv"
OUTPUT_FILE = "live_with_logo.m3u"

# 自定义台标名称映射（覆盖默认匹配规则）
LOGO_NAME_MAP = {
    "新闻综合": "上视新闻",
    "第一财经": "上海第一财经",
    "都市频道": "上海都市",
    "茶频道": "茶",
}

def clean_channel_name(name):
    # 去除清晰度标记
    n = re.sub(r'(4K|HD|FHD|UHD|50帧|高清|标清)', '', name).strip()
    # CCTV 特殊处理（如 CCTV-1 -> CCTV1）
    m = re.match(r'^CCTV-?(\d+\+?)', n)
    if m:
        return 'CCTV' + m.group(1)
    return n

def main():
    req = urllib.request.Request(
        ORIGINAL_M3U_URL,
        headers={'User-Agent': 'Mozilla/5.0'}
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        content = response.read().decode('utf-8', errors='ignore')

    out = []
    count = 0

    for line in content.splitlines():
        # 保留原始 #EXTM3U 行，不做任何 EPG 修改
        if line.startswith('#EXTM3U'):
            # 如果原行本身带有 x-tvg-url，我们直接去掉它（保持干净）
            if 'x-tvg-url' in line:
                # 移除 x-tvg-url="..." 部分
                line = re.sub(r'x-tvg-url="[^"]*"\s*', '', line).strip()
            out.append(line)
            continue

        # 对 #EXTINF 行注入台标
        if line.startswith('#EXTINF:') and 'tvg-logo' not in line:
            parts = line.rsplit(',', 1)
            if len(parts) == 2:
                left, ch_name = parts
                ch_name = ch_name.strip()
                clean = clean_channel_name(ch_name)
                # 如果自定义映射表里有，则用映射值；否则直接用清洗后的名称
                logo_key = LOGO_NAME_MAP.get(clean, clean)
                logo_url = f"{LOGO_BASE}/{logo_key}.png"

                # 构造新行，添加 tvg-name 和 tvg-logo
                line = f'{left} tvg-name="{clean}" tvg-logo="{logo_url}",{ch_name}'
                count += 1

        out.append(line)

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')

    print(f"已生成 {OUTPUT_FILE}，共注入 {count} 个台标字段")

if __name__ == '__main__':
    main()
