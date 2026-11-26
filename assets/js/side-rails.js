(() => {
  const footer = document.querySelector('.site-footer');
  const rails = document.querySelectorAll('.site-side-ad');
  if (!footer || !rails.length) return;
  let ticking = false;
  function update() {
    const footerTop = footer.getBoundingClientRect().top;
    rails.forEach((rail) => {
      if (getComputedStyle(rail).display === 'none') return;
      const top = parseFloat(getComputedStyle(rail).top) || 0;
      const offset = Math.min(0, footerTop - 16 - top - rail.offsetHeight);
      rail.style.setProperty('--rail-offset', `${offset}px`);
    });
    ticking = false;
  }
  function schedule() {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule, { passive: true });
  window.addEventListener('load', schedule, { once: true });
  if ('ResizeObserver' in window) new ResizeObserver(schedule).observe(footer);
  schedule();
})();
