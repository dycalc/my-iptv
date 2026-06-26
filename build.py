import re
import urllib.request
from urllib.parse import quote

# ============ 配置区 ============
# 原作者的 M3U 链接
ORIGINAL_M3U_URL = "https://raw.githubusercontent.com/babylife/China-ShangHai-IPTV-list/master/IPTV_Enhanced_change.m3u"
# 更改为使用 gh-proxy 代理 Github Raw 的台标库基准路径
LOGO_BASE = "https://gh-proxy.com/https://raw.githubusercontent.com/fanmingming/live/main/tv"
# 节目单地址也同步更改为 gh-proxy 代理源
EPG_URL = "https://gh-proxy.com/https://raw.githubusercontent.com/fanmingming/live/main/e.xml"
# 输出文件名
OUTPUT_FILE = "live_with_logo.m3u"

# 完美本地台标映射表：你的频道名 -> 范明明库里真实存在的文件名
LOGO_NAME_MAP = {
    "新闻综合": "上海新闻综合",
    "都市频道": "上海都市",
    "第一财经": "第一财经东方财经",  # 核心修正：库里这两个台是合并的
    "东方财经": "第一财经东方财经",  # 核心修正
    "CGTN": "CGTN",
    "CCTV1": "CCTV1",
    "CCTV2": "CCTV2",
    "CCTV3": "CCTV3",
    "CCTV4": "CCTV4",
    "CCTV5": "CCTV5",
    "CCTV6": "CCTV6",
    "CCTV7": "CCTV7",
    "CCTV8": "CCTV8",
    "CCTV9": "CCTV9",
    "CCTV10": "CCTV10",
    "CCTV11": "CCTV11",
    "CCTV12": "CCTV12",
    "CCTV13": "CCTV13",
    "CCTV14": "CCTV14",
    "CCTV15": "CCTV15",
    "CCTV16": "CCTV16",
    "CCTV17": "CCTV17",
    "CCTV4K": "CCTV4K",
}
# ================================

def clean_channel_name(name):
    # 移除 4K, HD, 50帧 等修饰词
    n = re.sub(r'(4K|HD|FHD|UHD|50帧|高清|标清)', '', name).strip()
    
    # CCTV-1HD / CCTV-5+HD -> CCTV1 / CCTV5+
    m = re.match(r'^CCTV-?(\d+\+?)', n, re.IGNORECASE)
    if m:
        return 'CCTV' + m.group(1)
        
    return n

def main():
    print("开始从源头抓取最新的 IPTV 列表...")
    req = urllib.request.Request(
        ORIGINAL_M3U_URL,
        headers={'User-Agent': 'Mozilla/5.0'}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"抓取源 M3U 失败: {e}")
        return

    out = []
    count = 0

    for line in content.splitlines():
        # 1. 替换或插入 EPG 地址
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

        # 2. 注入台标和 tvg-name
        elif line.startswith('#EXTINF:') and 'tvg-logo' not in line:
            parts = line.rsplit(',', 1)
            if len(parts) == 2:
                left, ch_name = parts
                ch_name = ch_name.strip()
                
                # 清洗名字
                clean = clean_channel_name(ch_name)
                
                # 查表匹配真实台标文件名
                logo_key = LOGO_NAME_MAP.get(clean, clean)
                
                # 对文件名部分进行标准百分号编码，防止中文路径在部分播放器中解析失败
                encoded_file = quote(f"{logo_key}.png")
                logo_url = f"{LOGO_BASE}/{encoded_file}"

                line = f'{left} tvg-name="{clean}" tvg-logo="{logo_url}",{ch_name}'
                count += 1

        out.append(line)

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='
') as f:
        f.write('
'.join(out) + '
')

    print(f"台标注入成功！共生成 {len(out)} 行数据，成功匹配并写入了 {count} 个频道台标。")

if __name__ == '__main__':
    main()
