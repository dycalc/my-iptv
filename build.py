import re
import urllib.request

ORIGINAL_M3U_URL = "https://raw.githubusercontent.com/babylife/China-ShangHai-IPTV-list/master/IPTV_Enhanced_change.m3u"
LOGO_BASE = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/tv"
EPG_URL = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/e.xml"
OUTPUT_FILE = "live_with_logo.m3u"

LOGO_NAME_MAP = {
    # 后续把匹配不到的地方台补这里
    # "都市频道": "上海都市",
}

def clean_channel_name(name):
    n = re.sub(r'(4K|HD|FHD|UHD|50帧|高清|标清)', '', name).strip()

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
        if line.startswith('#EXTM3U'):
            if 'x-tvg-url' in line:
                line = re.sub(
                    r'x-tvg-url="[^"]*"',
                    f'x-tvg-url="{EPG_URL}"',
                    line
                )
            else:
                line = line.replace(
                    '#EXTM3U',
                    f'#EXTM3U x-tvg-url="{EPG_URL}"',
                    1
                )

        elif line.startswith('#EXTINF:') and 'tvg-logo' not in line:
            parts = line.rsplit(',', 1)
            if len(parts) == 2:
                left, ch_name = parts
                ch_name = ch_name.strip()
                clean = clean_channel_name(ch_name)
                logo_key = LOGO_NAME_MAP.get(clean, clean)
                logo_url = f"{LOGO_BASE}/{logo_key}.png"

                line = f'{left} tvg-name="{clean}" tvg-logo="{logo_url}",{ch_name}'
                count += 1

        out.append(line)

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')

    print(f"已生成 {OUTPUT_FILE}，共注入 {count} 个台标字段")

if __name__ == '__main__':
    main()
