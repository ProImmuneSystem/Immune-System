#!/usr/bin/env python3
"""Mirror all published WordPress.com posts. Fail closed before deleting on API errors."""
import argparse, hashlib, html, json, re, sys, time, urllib.request
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
API = 'https://public-api.wordpress.com/rest/v1.1/sites/proimmunesystem.wordpress.com/posts/'
SITE = 'proimmunesystem.wordpress.com'
STATE = ROOT / '_data/sync_state.json'
ALIASES = {'면역세포':'immune-cells','음식과 영양':'food-nutrition','암의 이해':'understanding-cancer','생활과 여성 건강':'everyday-health','생활 건강':'everyday-health','병원과 보험':'hospital-insurance','연구와 논문':'research','해외 건강 자료':'global-health'}
STRIP = re.compile(r'<(?:script|iframe)\b[^>]*>.*?</(?:script|iframe)\s*>', re.I|re.S)
IMG = re.compile(r'https?://(?:proimmunesystem\.wordpress\.com|proimmunesystem\.files\.wordpress\.com|i[0-2]\.wp\.com)/[^\s\"\'<>),]+', re.I)

def fetch(url):
    err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'ImmuneNewsSync/1.0'})
            with urllib.request.urlopen(req, timeout=45) as response:
                return response.read()
        except Exception as exc:
            err = exc
            if attempt < 2: time.sleep(2 ** attempt)
    raise RuntimeError(f'Fetch failed: {url}: {err}')

def get_posts():
    posts, found, page = [], None, 1
    while True:
        fields = 'ID,title,date,modified,slug,URL,content,excerpt,categories,tags,featured_image'
        obj = json.loads(fetch(API + f'?number=100&page={page}&status=publish&fields={fields}'))
        if not isinstance(obj.get('posts'),list) or not isinstance(obj.get('found'),int):
            raise ValueError('Unexpected API result; refusing to delete local posts')
        found = obj['found']; batch = obj['posts']; posts.extend(batch)
        if len(posts) >= found: break
        if not batch or page > 1000: raise ValueError('Incomplete API pagination; refusing to delete local posts')
        page += 1
    if len(posts) != found or len({p.get('ID') for p in posts}) != found:
        raise ValueError('Post count changed or duplicate IDs; retry sync')
    return posts

def snapshot_posts(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('failures'): raise ValueError('Snapshot has failed fetches')
    cats = {c['id']: c for c in data['categories']}; media={m['id']:m['source_url'] for m in data['media']}
    result=[]
    for p in data['posts']:
        result.append({'ID':p['id'],'slug':p['slug'],'date':p['date'],'modified':p['modified'],'URL':p['link'],'title':p['title'],'content':p['content'],'excerpt':p['excerpt'],'categories':{cats[c]['name']:cats[c] for c in p['categories'] if c in cats},'tags':{},'featured_image':media.get(p['featured_media'],'')})
    return result

def image_path(raw, offline):
    url=html.unescape(raw).split('?')[0].rstrip('.')
    parsed=urlparse(url)
    if parsed.netloc in ('i0.wp.com','i1.wp.com','i2.wp.com'):
        host_and_path=parsed.path.lstrip('/'); url='https://'+host_and_path
        parsed=urlparse(url)
    if parsed.netloc not in (SITE,'proimmunesystem.files.wordpress.com') or '/wp-content/uploads/' not in parsed.path and parsed.netloc == SITE:
        return raw
    ext=Path(parsed.path).suffix.lower()
    if ext not in ('.png','.jpg','.jpeg','.webp','.gif','.svg'): return raw
    name=hashlib.sha256(url.encode()).hexdigest()[:18]+ext
    target=ROOT/'assets/images'/name
    if offline: return raw
    if not target.exists():
        data=fetch(url)
        if len(data)<100 or data.lstrip().lower().startswith((b'<html', b'<!doctype')): raise ValueError('Invalid image response '+url)
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data)
    return '/assets/images/'+name

def transform(content,offline):
    content=STRIP.sub('',content or '')
    # Replacing each srcset candidate with the full-size original yields incorrect descriptors.
    content=re.sub(r'\s+(?:srcset|sizes|data-permalink|data-orig-file|data-large-file)="[^"]*"','',content)
    content=IMG.sub(lambda m:image_path(m.group(0),offline),content)
    content=content.replace('/assets/images/','{{ site.baseurl }}/assets/images/')
    # Same-site content links stay within the mirror. WordPress image URLs are handled first.
    content=re.sub(r'https://'+re.escape(SITE)+r'/(?!wp-content/uploads/)', '{{ site.baseurl }}/', content)
    content=re.sub(r'''((?:href|src)=["'])/(?!/)''', r'\1{{ site.baseurl }}/', content)
    return content

def write_if_changed(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_text(encoding='utf-8') == value: return False
    path.write_text(value,encoding='utf-8');return True

def cat_name(name): return '생활 건강' if name=='생활과 여성 건강' else name

def render_post(post,offline):
    categories=[]
    for name, info in sorted((post.get('categories') or {}).items()):
        normalized=cat_name(name); slug=ALIASES.get(name) or unquote(info.get('slug') or name)
        wp_slug=unquote(info.get('slug') or slug)
        if '/' in wp_slug or wp_slug in ('.', '..'): raise ValueError('Invalid category slug')
        categories.append({'name':normalized,'slug':slug,'wp_slug':wp_slug})
    title=html.unescape(re.sub('<[^>]+>','',post.get('title') or '')).strip()
    excerpt=html.unescape(re.sub('<[^>]+>','',post.get('excerpt') or '')).replace('\n',' ').strip()
    image=image_path(post.get('featured_image') or '',offline) if post.get('featured_image') else ''
    date=post['date']; slug=post['slug']; path=urlparse(post['URL']).path
    data={'layout':'post','title':title,'date':date,'last_modified_at':post['modified'],'slug':slug,'categories':[], 'wp_categories':categories,'tags':list((post.get('tags') or {}).keys()),'excerpt':excerpt,'image':image,'wp_id':post['ID'],'permalink':path}
    front='---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in data.items())+'\n---\n'
    content=transform(post.get('content'),offline)
    # Content may contain literal Liquid. The only intended template expression is our base URL.
    content=content.replace('{{ site.baseurl }}','__IMMUNE_BASEURL__')
    content='{% raw %}'+content+'{% endraw %}'
    content=content.replace('__IMMUNE_BASEURL__','{% endraw %}{{ site.baseurl }}{% raw %}')
    return front+content+'\n',categories

def sync(posts,offline):
    if not posts: raise ValueError('Empty post list; refusing to delete local posts')
    previous=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    wanted={}; categories={}; dirty=0
    for post in sorted(posts,key=lambda p:p['ID']):
        if not all(post.get(k) for k in ('ID','slug','date','modified','URL')): raise ValueError('Missing required fields')
        filename=post['date'][:10]+'-'+post['slug']+'.html'
        if '/' in filename or '..' in filename: raise ValueError('Invalid filename')
        text, cats=render_post(post,offline)
        wanted[filename] = (post,text)
        for c in cats: categories[c['slug']]=c['name']; categories[c['wp_slug']]=c['name']
    for filename,(p,text) in wanted.items(): dirty += write_if_changed(ROOT/'_posts'/filename,text)
    for path in (ROOT/'_posts').glob('*.html'):
        if path.name not in wanted and re.search(r'^wp_id:',path.read_text(encoding='utf-8'),re.M): path.unlink();dirty+=1
    state={str(p['ID']):{'modified':p['modified'],'file':f} for f,(p,_) in wanted.items()}
    dirty+=write_if_changed(STATE,json.dumps(state,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    dirty+=write_if_changed(ROOT/'_data/categories.json',json.dumps([{'slug':s,'name':n} for s,n in sorted(categories.items())],ensure_ascii=False,indent=2)+'\n')
    for slug,name in categories.items():
        target=ROOT/'category'/slug/'index.html'
        dirty+=write_if_changed(target,'---\nlayout: category\ntitle: '+json.dumps(name,ensure_ascii=False)+'\ncategory_slug: '+json.dumps(slug,ensure_ascii=False)+'\npermalink: /category/'+slug+'/\n---\n')
    # Pagination pages are generated from the verified full count.
    for name in ('all-news','latest-news'):
        for n in range(1,(len(posts)+11)//12+1):
            suffix='' if n==1 else 'page/'+str(n)+'/'
            data={'layout':'listing','title':'전체 기사' if name=='all-news' else '최신 기사','page_number':n,'listing_name':name,'permalink':'/'+name+'/'+suffix}
            raw='---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in data.items())+'\n---\n'
            dirty+=write_if_changed(ROOT/name/suffix/'index.html',raw)
        page_dir=ROOT/name/'page'
        if page_dir.exists():
            for index in page_dir.glob('*/index.html'):
                if index.parent.name.isdigit() and int(index.parent.name)>(len(posts)+11)//12: index.unlink();dirty+=1
    print(f'posts={len(posts)} categories={len(categories)} changed_files={dirty} images={len(list((ROOT/"assets/images").glob("*")))}')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--snapshot');parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    try: sync(snapshot_posts(args.snapshot) if args.snapshot else get_posts(),args.offline)
    except Exception as exc: print('Sync aborted:',exc,file=sys.stderr);return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
