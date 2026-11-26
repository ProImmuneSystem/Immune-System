(() => {
  const carousel = document.querySelector('[data-guide-carousel]');
  if (!carousel) return;
  const track = carousel.querySelector('.guide-track');
  const next = carousel.querySelector('[data-guide-next]');
  const pause = carousel.querySelector('[data-guide-pause]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reducedMotion.matches, busy = false, timer = null, visible = true;
  carousel.classList.add('is-ready');
  next.hidden = false;
  pause.hidden = false;

  function displayPause() {
    pause.textContent = paused ? '자동 재생' : '일시정지';
    pause.setAttribute('aria-label', paused ? '자동 이동 재생' : '자동 이동 일시정지');
  }
  function stop() { window.clearInterval(timer); timer = null; }
  function start() {
    stop();
    if (!paused && visible && !carousel.matches(':hover, :focus-within') && !document.hidden) {
      timer = window.setInterval(advance, 5000);
    }
  }
  function advance() {
    if (busy || track.children.length < 2) return;
    busy = true;
    const first = track.firstElementChild;
    const clone = first.cloneNode(true);
    clone.setAttribute('aria-hidden', 'true');
    clone.querySelectorAll('a,button').forEach(el => el.tabIndex = -1);
    track.appendChild(clone);
    const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
    const distance = first.getBoundingClientRect().width + gap;
    const finish = () => {
      track.removeEventListener('transitionend', finish);
      track.style.transition = 'none';
      track.appendChild(first);
      clone.remove();
      track.style.transform = '';
      void track.offsetWidth;
      track.style.transition = '';
      busy = false;
    };
    if (reducedMotion.matches) { finish(); return; }
    track.addEventListener('transitionend', finish, { once: true });
    track.style.transform = `translateX(-${distance}px)`;
  }
  next.addEventListener('click', () => { advance(); start(); });
  pause.addEventListener('click', () => { paused = !paused; displayPause(); start(); });
  carousel.addEventListener('mouseenter', stop);
  carousel.addEventListener('mouseleave', start);
  carousel.addEventListener('focusin', stop);
  carousel.addEventListener('focusout', () => window.setTimeout(start, 0));
  document.addEventListener('visibilitychange', start);
  reducedMotion.addEventListener('change', e => { if (e.matches) paused = true; displayPause(); start(); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => { visible = entries[0].isIntersecting; start(); }, { threshold: 0.1 }).observe(carousel);
  }
  displayPause();
  start();
})();
