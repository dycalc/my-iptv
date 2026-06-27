import re
import urllib.request

# 原始 m3u 数据源（直连，不使用 gh-proxy）
ORIGINAL_M3U_URL = "https://raw.githubusercontent.com/auflute/IPTV-Unicom-Shanghai/main/unicom-sha-local/unicom.m3u"
# 台标 CDN 基础路径
LOGO_BASE = "https://cdn.jsdelivr.net/gh/fanmingming/live@main/tv"
# 输出文件
OUTPUT_FILE = "unicom_with_logo.m3u"

# 频道名 -> 台标文件名 的手动映射（不区分大小写，但建议与范明明库中文件名一致）
LOGO_NAME_MAP = {
    # 上海地方台
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
    # 茶频道特例（如果列表中有）
    "茶频道": "茶",
}

def clean_channel_name(raw_name: str) -> str:
    """
    清洗频道名称，去除清晰度/制式后缀，标准化 CCTV 写法。
    返回可能匹配范明明库文件名的字符串。
    """
    n = raw_name.strip()
    # 去掉清晰度、制式等标记
    n = re.sub(r'\b(4K|8K|HD|FHD|UHD|SD|50帧|60帧|高清|标清|超清)\b', '', n, flags=re.IGNORECASE).strip()
    # CCTV 标准化：CCTV-1 综合 -> CCTV1
    m = re.match(r'^CCTV-?(\d+[\+]?).*', n, re.IGNORECASE)
    if m:
        return 'CCTV' + m.group(1)
    # CGTN 等保持原样
    return n

def get_logo_url(channel_name: str) -> str:
    """根据频道显示名生成台标 URL"""
    clean = clean_channel_name(channel_name)
    # 先查映射表
    logo_key = LOGO_NAME_MAP.get(clean, clean)
    return f"{LOGO_BASE}/{logo_key}.png"

def main():
    req = urllib.request.Request(
        ORIGINAL_M3U_URL,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8', errors='ignore')

    out_lines = []
    modified_count = 0

    for line in content.splitlines():
        if line.startswith('#EXTINF:'):
            # 分离属性部分和频道显示名
            if ',' not in line:
                out_lines.append(line)
                continue

            attrs_part, display_name = line.split(',', 1)
            display_name = display_name.strip()
            new_logo_url = get_logo_url(display_name)

            # 如果已有 tvg-logo，替换它的值；否则在属性区末尾添加
            if 'tvg-logo="' in attrs_part:
                # 替换现有 tvg-logo 的 URL
                new_attrs = re.sub(
                    r'tvg-logo="[^"]*"',
                    f'tvg-logo="{new_logo_url}"',
                    attrs_part
                )
                line = new_attrs + ',' + display_name
            else:
                # 在属性末尾追加 tvg-logo（紧挨逗号前加一个空格）
                # 注意 attrs_part 尾部可能已有空格，先 rstrip 再补空格
                line = attrs_part.rstrip() + f' tvg-logo="{new_logo_url}",' + display_name

            modified_count += 1

        out_lines.append(line)

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out_lines) + '\n')

    print(f"已生成 {OUTPUT_FILE}，共更新 {modified_count} 个频道的台标。")

if __name__ == '__main__':
    main()
