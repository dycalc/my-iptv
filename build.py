import re
import sys
import traceback
import urllib.request

ORIGINAL_M3U_URL = "https://raw.githubusercontent.com/babylife/China-ShangHai-IPTV-list/master/IPTV_Enhanced_change.m3u"
LOGO_BASE = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/tv"
EPG_URL = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/e.xml"
OUTPUT_FILE = "live_with_logo.m3u"
CHECK_LOGO = True

LOGO_NAME_MAP = {
    # "都市频道": "上海都市",
}

_logo_cache = {}

def clean_channel_name(name):
    n = re.sub(r'(4K|HD|FHD|UHD|50帧|高清|标清)', '', name).strip()
    m = re.match(r'^CCTV-?(\d+\+?)', n)
    if m:
        n = 'CCTV' + m.group(1)
    return n

def logo_exists(url):
    if url in _logo_cache:
        return _logo_cache[url]
    ok = False
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            ok = (r.status == 200)
    except Exception as e:
        # 单个台标探测失败不影响整体，仅记录
        print(f"  [logo探测失败] {url} -> {e}")
        ok = False
    _logo_cache[url] = ok
    return ok

def fetch_source():
    # 带重试的抓取，避免单次网络抖动直接崩溃
    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(ORIGINAL_M3U_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            last_err = e
            print(f"第 {attempt+1} 次抓取失败：{e}")
    raise RuntimeError(f"抓取原始 m3u 连续失败：{last_err}")

def main():
    content = fetch_source()
    out, hit, miss = [], 0, 0
    for line in content.splitlines():
        try:
            if line.startswith('#EXTM3U'):
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
        except Exception as e:
            print(f"  [处理行失败，已跳过] {line[:40]} -> {e}")
        out.append(line)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f"完成：{len(out)} 行，命中 {hit}，跳过 {miss}")

if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
