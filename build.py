import re
import urllib.request

# 原始数据源（直连 GitHub，不用 gh-proxy）
ORIGINAL_M3U_URL = "https://raw.githubusercontent.com/auflute/IPTV-Unicom-Shanghai/main/unicom-sha-local/unicom.m3u"
# 台标 CDN 基础路径（最终域名是 cdn.jsdelivr.net）
LOGO_CDN_BASE = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/tv"
# 输出文件 —— 必须和 workflow 里的 git add 一致
OUTPUT_FILE = "live_with_logo.m3u"

# 频道名 → 台标文件名的映射（按范明明仓库的实际文件名）
LOGO_NAME_MAP = {
    "新闻综合": "上视新闻",
    "上海新闻综合": "上视新闻",
    "都市频道": "上海都市",
    "上海都市": "上海都市",
    "第一财经": "上海第一财经",
    "上海第一财经": "上海第一财经",
    "哈哈炫动": "哈哈炫动",
    "上海哈哈炫动": "哈哈炫动",
    "东方卫视": "东方卫视",
    "上海教育": "上海教育",
    "金色频道": "金色频道",
    "法治天地": "法治天地",
    "七彩戏剧": "七彩戏剧",
    "游戏风云": "游戏风云",
    "动漫秀场": "动漫秀场",
    "生活时尚": "生活时尚",
    "东方购物": "东方购物",
    "茶频道": "茶",
}

def clean_channel_name(raw_name: str) -> str:
    """去掉清晰度/制式后缀，标准化 CCTV 写法"""
    n = raw_name.strip()
    n = re.sub(r'\b(4K|8K|HD|FHD|UHD|SD|50帧|60帧|高清|标清|超清)\b', '', n, flags=re.IGNORECASE).strip()
    m = re.match(r'^CCTV-?(\d+[\+]?).*', n, re.IGNORECASE)
    if m:
        return 'CCTV' + m.group(1)
    return n

def get_logo_url(channel_name: str) -> str:
    """生成 cdn.jsdelivr.net 的台标链接"""
    clean = clean_channel_name(channel_name)
    logo_key = LOGO_NAME_MAP.get(clean, clean)
    return f"{LOGO_CDN_BASE}/{logo_key}.png"

def main():
    req = urllib.request.Request(
        ORIGINAL_M3U_URL,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8', errors='ignore')

    out_lines = []
    modified = 0

    for line in content.splitlines():
        if line.startswith('#EXTINF:'):
            if ',' not in line:
                out_lines.append(line)
                continue

            attrs_part, display_name = line.split(',', 1)
            display_name = display_name.strip()
            new_logo_url = get_logo_url(display_name)

            # 同时支持单引号和双引号的 tvg-logo
            if re.search(r"""tvg-logo\s*=\s*['"][^'"]*['"]""", attrs_part):
                # 替换已有的 tvg-logo（保留原有引号类型）
                def replacer(m):
                    quote = m.group(2)   # ' 或 "
                    return f'tvg-logo={quote}{new_logo_url}{quote}'
                new_attrs = re.sub(
                    r"""(tvg-logo\s*=\s*)(['"])([^'"]*)(\2)""",
                    replacer,
                    attrs_part
                )
                line = new_attrs + ',' + display_name
            else:
                # 没有 tvg-logo，则在属性末尾追加（使用双引号）
                line = attrs_part.rstrip() + f' tvg-logo="{new_logo_url}",' + display_name

            modified += 1

        out_lines.append(line)

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out_lines) + '\n')

    print(f"已生成 {OUTPUT_FILE}，共更新 {modified} 个频道的台标。")

if __name__ == '__main__':
    main()
