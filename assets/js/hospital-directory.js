(() => {
  'use strict';
  const root = document.querySelector('.hospital-directory');
  if (!root) return;
  const base = root.dataset.hospitalBase;
  const regionLinks = [...root.querySelectorAll('[data-region]')];
  const district = root.querySelector('#hd-district');
  const type = root.querySelector('#hd-type');
  const search = root.querySelector('#hd-search');
  const districtButtons = root.querySelector('.hd-districts');
  const resultCount = root.querySelector('#hd-result-count');
  const status = root.querySelector('.hd-status');
  const cards = root.querySelector('.hd-card-grid');
  const pagination = root.querySelector('.hd-pagination');
  const results = root.querySelector('#hospital-results');
  const cache = new Map();
  const perPage = 24;
  let manifest = {}, region = '', records = [], page = 1, fetchId = 0;

  function el(tag, className, content) {
    const e = document.createElement(tag);
    if (className) e.className = className;
    if (content !== undefined) e.textContent = content;
    return e;
  }
  function anchor(text, url, external = true) {
    const a = el('a', '', text); a.href = url;
    if (external) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
    return a;
  }
  function safeWebsite(raw) {
    if (!raw) return '';
    try {
      const input = raw.trim().replace(/\?+$/, '');
      const u = new URL(/^https?:\/\//i.test(input) ? input : 'https://' + input);
      if (!/^https?:$/.test(u.protocol) || !u.hostname.includes('.') || u.username || u.password) return '';
      return u.href;
    } catch (_) { return ''; }
  }
  async function unpack(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error('데이터를 불러오지 못했습니다.');
    const data = await response.arrayBuffer();
    const bytes = new Uint8Array(data);
    if (bytes[0] !== 0x1f || bytes[1] !== 0x8b) return JSON.parse(new TextDecoder().decode(bytes));
    if (!('DecompressionStream' in window)) throw new Error('브라우저가 목록 압축을 지원하지 않습니다. 아래 심평원 검색을 이용해주세요.');
    const stream = new Blob([data]).stream().pipeThrough(new DecompressionStream('gzip'));
    return JSON.parse(await new Response(stream).text());
  }
  function makeCard(row) {
    const [name, area, kind, address, phone, website] = row;
    const card = el('article', 'hd-card');
    card.append(el('p', 'hd-card-label', area + ' · ' + kind), el('h3', '', name), el('p', '', address || '주소 정보 없음'));
    if (phone) {
      const p = el('p');
      const digits = phone.replace(/[^0-9+]/g, '');
      if (digits) p.append(anchor(phone, 'tel:' + digits, false)); else p.textContent = phone;
      card.append(p);
    }
    const links = el('div', 'hd-card-links');
    const site = safeWebsite(website);
    if (site) links.append(anchor('병원 홈페이지', site));
    const query = encodeURIComponent(name + ' ' + (address || area));
    links.append(anchor('병원 정보 검색', 'https://search.naver.com/search.naver?query=' + query));
    card.append(links);
    return card;
  }
  function renderDistricts() {
    districtButtons.replaceChildren();
    const items = [['', '전체'], ...Object.keys(manifest[region].districts).map(x => [x, x])];
    for (const [value, label] of items) {
      const button = el('button', '', label); button.type = 'button';
      button.dataset.district = value; button.setAttribute('aria-pressed', String(district.value === value));
      districtButtons.append(button);
    }
  }
  function render() {
    if (!region || !manifest[region]) return;
    const needle = search.value.trim().toLocaleLowerCase('ko');
    const subset = records.filter(r => (!district.value || r[1] === district.value) && (!type.value || r[2] === type.value) && (!needle || (r[0] + ' ' + r[3]).toLocaleLowerCase('ko').includes(needle)));
    const totalPages = Math.max(1, Math.ceil(subset.length / perPage));
    page = Math.min(page, totalPages);
    cards.replaceChildren(...subset.slice((page - 1) * perPage, page * perPage).map(makeCard));
    resultCount.textContent = '검색 결과 ' + subset.length.toLocaleString('ko-KR') + '곳';
    status.textContent = subset.length ? manifest[region].name + (district.value ? ' · ' + district.value : ' 전체') + '의 의료기관' : '조건에 맞는 병원이 없습니다. 다른 지역이나 검색어를 선택해 보세요.';
    pagination.replaceChildren();
    if (subset.length > perPage) {
      const prev = el('button', '', '이전'); prev.type = 'button'; prev.disabled = page === 1;
      const label = el('span', '', page.toLocaleString('ko-KR') + ' / ' + totalPages.toLocaleString('ko-KR'));
      const next = el('button', '', '다음'); next.type = 'button'; next.disabled = page === totalPages;
      prev.addEventListener('click', () => { page--; render(); results.scrollIntoView({block:'start'}); });
      next.addEventListener('click', () => { page++; render(); results.scrollIntoView({block:'start'}); });
      pagination.append(prev, label, next);
    }
  }
  async function selectRegion(slug, scroll) {
    if (!manifest[slug]) return;
    region = slug; page = 1; records = []; search.value = '';
    const id = ++fetchId;
    regionLinks.forEach(a => a.setAttribute('aria-current', String(a.dataset.region === slug)));
    const districts = Object.keys(manifest[slug].districts);
    district.replaceChildren(new Option('전체 시·군·구', ''));
    districts.forEach(name => district.add(new Option(name, name)));
    type.replaceChildren(new Option('전체 기관', ''));
    renderDistricts();
    status.textContent = manifest[slug].name + '의 병원 목록을 불러오는 중입니다.';
    resultCount.textContent = ''; cards.replaceChildren(); pagination.replaceChildren();
    if (scroll) results.scrollIntoView({block:'start', behavior:'smooth'});
    try {
      if (!cache.has(slug)) {
        const chunks = await Promise.all(manifest[slug].parts.map(file => unpack(base + file)));
        cache.set(slug, chunks.flat());
      }
      if (id !== fetchId) return;
      records = cache.get(slug);
      [...new Set(records.map(r => r[2]))].sort((a,b) => a.localeCompare(b,'ko')).forEach(name => type.add(new Option(name,name)));
      render();
    } catch (error) {
      if (id === fetchId) status.textContent = error.message + ' 심평원 병원·약국 찾기에서 확인해 주세요.';
    }
  }
  regionLinks.forEach(a => a.addEventListener('click', event => {
    event.preventDefault();
    history.replaceState(null, '', '#' + a.dataset.region);
    selectRegion(a.dataset.region, true);
  }));
  district.addEventListener('change', () => { page = 1; renderDistricts(); render(); });
  type.addEventListener('change', () => { page = 1; render(); });
  search.addEventListener('input', () => { page = 1; render(); });
  districtButtons.addEventListener('click', event => {
    const button = event.target.closest('button[data-district]');
    if (!button) return;
    district.value = button.dataset.district; page = 1; renderDistricts(); render();
  });
  fetch(base + 'manifest.json').then(r => { if (!r.ok) throw Error(); return r.json(); }).then(data => {
    manifest = data;
    const slug = location.hash.slice(1);
    selectRegion(manifest[slug] ? slug : 'seoul', Boolean(manifest[slug]));
  }).catch(() => { status.textContent = '목록을 불러오지 못했습니다. 아래 심평원 병원·약국 찾기를 이용해 주세요.'; });
})();
