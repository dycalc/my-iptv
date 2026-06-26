import re
import urllib.request

ORIGINAL_M3U_URL = "https://raw.githubusercontent.com/babylife/China-ShangHai-IPTV-list/master/IPTV_Enhanced_change.m3u"
LOGO_BASE = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/tv"
EPG_URL = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/e.xml"
OUTPUT_FILE = "live_with_logo.m3u"
CHECK_LOGO = True

# 上海地方台映射表：你的频道名 → 范明明库真实文件名（核对后逐个补全）
LOGO_NAME_MAP = {
    # "都市频道": "上海都市",
    # "东方影视": "东方影视",
    # "欢笑剧场": "SiTV欢笑剧场",
}

_logo_cache = {}

def clean_channel_name(name):
    # 1. 去掉清晰度后缀
    n = re.sub(r'(4K|HD|FHD|UHD|50帧|高清|标清)', '', name).strip()
    # 2. CCTV-1 / CCTV-5+ → CCTV1 / CCTV5+（范明明库无横杠）
    m = re.match(r'^CCTV-?(\d+\+?)', n)
    if m:
        n = 'CCTV' + m.group(1)
    return n

def logo_exists(url):
    if url in _logo_cache:
        return _logo_cache[url]
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            ok = (r.status == 200)
    except Exception:
        ok = False
    _logo_cache[url] = ok
    return ok

def main():
    req = urllib.request.Request(ORIGINAL_M3U_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        content = response.read().decode('utf-8')

    out, hit, miss = [], 0, 0
    for line in content.splitlines():
        if line.startswith('#EXTM3U'):
            # 替换/补上 EPG 地址，保留原有 catchup 参数
            if 'x-tvg-url' in line:
                line = re.sub(r'x-tvg-url="[^"]*"', f'x-tvg-url="{EPG_URL}"', line)
            else:
                line = line.replace('#EXTM3U', f'#EXTM3U x-tvg-url="{EPG_URL}"', 1)
        elif line.startswith('#EXTINF:') and 'tvg-logo' not in line:
            parts = line.split(',')
            if len(parts) > 1:
                ch_name = parts[-1].strip()
                clean = clean_channel_name(ch_name)
                key = LOGO_NAME_MAP.get(clean, clean)
                logo_url = f"{LOGO_BASE}/{key}.png"
                if (not CHECK_LOGO) or logo_exists(logo_url):
                    line = line.replace('#EXTINF:-1',
                        f'#EXTINF:-1 tvg-name="{clean}" tvg-logo="{logo_url}"', 1)
                    hit += 1
                else:
                    miss += 1
        out.append(line)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('
'.join(out))
    print(f"完成：{len(out)} 行，命中 {hit}，跳过 {miss}")

if __name__ == '__main__':
    main()
