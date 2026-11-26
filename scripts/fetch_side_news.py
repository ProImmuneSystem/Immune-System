#!/usr/bin/env python3
"""Refresh public headline feeds for the site rails; failures never block deploy."""
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

OUTPUT = Path('_data/side_news.json')
SOURCES = {
    'trends': 'https://trends.google.com/trending/rss?geo=KR',
    'health': 'https://www.yna.co.kr/rss/health.xml',
}

def refresh(name, url):
    request = urllib.request.Request(url, headers={'User-Agent': 'ImmuneNewsFeed/1.0'})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read(2_000_000)
    root = ET.fromstring(data)
    items = []
    for item in root.findall('./channel/item'):
        title = (item.findtext('title') or '').strip()
        if not title:
            continue
        if name == 'trends':
            url = 'https://trends.google.com/trends/explore?geo=KR&q=' + urllib.parse.quote(title)
        else:
            url = (item.findtext('link') or '').strip()
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme != 'https' or parsed.hostname not in ('www.yna.co.kr', 'yna.co.kr'):
                continue
        items.append({'title': title, 'url': url})
        if len(items) == 4:
            break
    if not items:
        raise ValueError('feed returned no usable headlines')
    return {'updated': datetime.now(ZoneInfo('Asia/Seoul')).strftime('%m.%d %H:%M'), 'items': items}

def main():
    try:
        old = json.loads(OUTPUT.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        old = {}
    for name, url in SOURCES.items():
        try:
            old[name] = refresh(name, url)
            print(name + ': updated')
        except Exception as exc:
            print(name + ': retaining previous data:', str(exc), file=sys.stderr)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(old, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
