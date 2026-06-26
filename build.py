import re
import urllib.request

# ============ 配置区 ============
# 原作者的 M3U 链接（保持源头，原作者更新你自动跟）
ORIGINAL_M3U_URL = "https://raw.githubusercontent.com/babylife/China-ShangHai-IPTV-list/master/IPTV_Enhanced_change.m3u"
# 台标库（已改用 jsDelivr 仓库直链，绕开宕掉的 live.fanmingming.cn 域名）
LOGO_BASE = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/tv"
# EPG 节目单地址（同样走 jsDelivr）
EPG_URL = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/e.xml"
# 输出文件名
OUTPUT_FILE = "live_with_logo.m3u"
# 是否开启台标存在性探测（True=自动跳过 404 台标，避免破图；False=不校验，速度更快）
CHECK_LOGO = True

# 频道名 → 台标库实际文件名 的映射表（命中不了的地方台逐个补这里）
LOGO_NAME_MAP = {
    # "都市频道": "上海都市",
    # "新闻综合": "上海新闻综合",
}
# ================================

# 简单缓存，避免对同一个台标 URL 重复探测
_logo_cache = {}

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

    output_lines = []
    hit, miss = 0, 0

    for line in content.splitlines():
        # 1. 头部补上 EPG 节目单地址
        if line.startswith('#EXTM3U'):
            if 'x-tvg-url' not in line:
                line = f'#EXTM3U x-tvg-url="{EPG_URL}"'
        # 2. 给频道行注入 tvg-logo
        elif line.startswith('#EXTINF:') and 'tvg-logo' not in line:
            parts = line.split(',')
            if len(parts) > 1:
                ch_name = parts[-1].strip()
                # 清洗频道名，去掉 4K/HD 等后缀，提升匹配率
                clean_name = re.sub(r'(4K|HD|FHD|50帧)', '', ch_name).strip()
                # 优先查映射表
                logo_key = LOGO_NAME_MAP.get(clean_name, clean_name)
                logo_url = f"{LOGO_BASE}/{logo_key}.png"

                if (not CHECK_LOGO) or logo_exists(logo_url):
                    line = line.replace(
                        '#EXTINF:-1',
                        f'#EXTINF:-1 tvg-name="{clean_name}" tvg-logo="{logo_url}"'
                    )
                    hit += 1
                else:
                    miss += 1  # 台标不存在，保持原行，不塞 404
        output_lines.append(line)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"已生成 {OUTPUT_FILE}：共 {len(output_lines)} 行，台标命中 {hit} 个，未命中跳过 {miss} 个")

if __name__ == '__main__':
    main()
