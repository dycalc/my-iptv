import re
import urllib.request

# 原作者的 M3U 链接（保持源头，原作者改了你自动跟）
ORIGINAL_M3U_URL = "https://raw.githubusercontent.com/babylife/China-ShangHai-IPTV-list/master/IPTV_Enhanced_change.m3u"
OUTPUT_FILE = "live_with_logo.m3u"

def main():
    req = urllib.request.Request(ORIGINAL_M3U_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        content = response.read().decode('utf-8')

    output_lines = []
    for line in content.splitlines():
        # 给头部补上 EPG 节目单地址
        if line.startswith('#EXTM3U') and 'x-tvg-url' not in line:
            line = '#EXTM3U x-tvg-url="https://live.fanmingming.cn/e.xml"'
        elif line.startswith('#EXTINF:') and 'tvg-logo' not in line:
            parts = line.split(',')
            if len(parts) > 1:
                ch_name = parts[-1].strip()
                # 清洗频道名，去掉 4K/HD 等后缀，提升台标匹配率
                clean_name = re.sub(r'(4K|HD|FHD|50帧)', '', ch_name).strip()
                logo_url = f"https://live.fanmingming.cn/tv/{clean_name}.png"
                line = line.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-name="{clean_name}" tvg-logo="{logo_url}"')
        output_lines.append(line)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    print(f"已生成 {OUTPUT_FILE}，共 {len(output_lines)} 行")

if __name__ == '__main__':
    main()
