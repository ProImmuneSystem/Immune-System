const q = new URLSearchParams(location.search).get('q') || '';
document.getElementById('search-query').textContent = q ? `“${q}” 검색 결과` : '검색어를 입력해 주세요.';
const list = document.getElementById('search-results');
for (const post of window.searchIndex.filter(p => (p.title + ' ' + p.excerpt).toLowerCase().includes(q.toLowerCase())).slice(0,100)) {
  if (!q) break;
  const card = document.createElement('article'); card.className = 'post-card';
  if (post.image) { const a=document.createElement('a'), img=document.createElement('img');a.href=post.url;img.src=post.image;img.alt='';a.appendChild(img);card.appendChild(a); }
  const h=document.createElement('h3'), a=document.createElement('a');a.href=post.url;a.textContent=post.title;h.appendChild(a);card.appendChild(h);list.appendChild(card);
}
if(q && !list.childElementCount) list.textContent='검색 결과가 없습니다.';
