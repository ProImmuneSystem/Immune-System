import html, re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote

root=Path(sys.argv[1]).resolve(); missing=[]; checked=0
class Links(HTMLParser):
 def __init__(self): super().__init__(); self.urls=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for key in ('href','src'):
   if key in a:self.urls.append(a[key])
for file in root.rglob('*.html'):
 parser=Links(); parser.feed(file.read_text(encoding='utf-8'))
 for url in parser.urls:
  u=urlsplit(html.unescape(url))
  if u.scheme or u.netloc or not u.path or u.path.startswith(('mailto:','tel:','data:')):continue
  path=unquote(u.path)
  if path.startswith('/Immune-System/'):
   target=root/path[len('/Immune-System/'):]
  elif path.startswith('/'):
   missing.append((str(file.relative_to(root)),url));continue
  else:target=(file.parent/path).resolve()
  if not target.is_relative_to(root):continue
  if target.is_dir():target=target/'index.html'
  if not target.exists() and not target.suffix:target=target.with_suffix('.html')
  checked+=1
  if not target.exists():missing.append((str(file.relative_to(root)),url))
print(f'checked={checked} missing={len(missing)}')
for file,url in missing[:100]:print(file,url)
if missing:sys.exit(1)
