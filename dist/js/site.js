(function(){
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const header = document.querySelector('header');
  const onScroll = () => { if (header) header.classList.toggle('scrolled', window.scrollY>12); };
  onScroll();
  window.addEventListener('scroll', onScroll, {passive:true});

  const toggle = document.querySelector('.nav-toggle');
  const panel = document.querySelector('.nav-panel');
  if (toggle && panel){
    toggle.addEventListener('click', () => {
      const open = panel.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  if (!reduce){
    const io = new IntersectionObserver((ents)=>{
      ents.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target);} });
    }, {threshold:0.16, rootMargin:'0px 0px -8% 0px'});
    document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
  } else {
    document.querySelectorAll('.reveal').forEach(el=>el.classList.add('in'));
  }

  document.querySelectorAll('video.device-video').forEach((v) => {
    if (reduce) {
      v.removeAttribute('autoplay');
      v.pause();
      v.controls = true;
      try { v.currentTime = 0; } catch (err) {}
    }
  });

  const steps = [...document.querySelectorAll('[data-step]')];
  const shots = [...document.querySelectorAll('[data-shot]')];
  if (steps.length && shots.length){
    let currentStep = -1;
    const activate = (i) => {
      steps.forEach((s,j)=>s.classList.toggle('active', j===i));
      shots.forEach((s,j)=>s.classList.toggle('active', j===i));
      if (i !== currentStep){
        currentStep = i;
        document.dispatchEvent(new CustomEvent('story:activate', { detail: { index: i, shot: shots[i] } }));
      }
    };
    activate(0);
    const mobile = () => window.matchMedia('(max-width: 960px)').matches;
    const marginFor = () => mobile() ? '-55% 0px -25% 0px' : '-40% 0px -40% 0px';
    const pick = () => {
      const mid = window.innerHeight * (mobile() ? 0.65 : 0.5);
      let idx = 0;
      steps.forEach((s, i) => {
        if (s.getBoundingClientRect().top <= mid) idx = i;
      });
      activate(idx);
    };
    let sio;
    const observeSteps = () => {
      if (sio) sio.disconnect();
      sio = new IntersectionObserver(() => pick(), {
        rootMargin: marginFor(),
        threshold: [0, 0.15, 0.35, 0.55, 0.75, 1]
      });
      steps.forEach(s => sio.observe(s));
      pick();
    };
    observeSteps();
    window.addEventListener('resize', observeSteps);
    window.addEventListener('scroll', pick, {passive: true});
  }

  const heroImg = document.querySelector('.hero-parallax');
  if (heroImg && !reduce){
    window.addEventListener('scroll', () => {
      const y = Math.min(40, window.scrollY * 0.08);
      heroImg.style.transform = `translateY(${y}px)`;
    }, {passive:true});
  }

  document.querySelectorAll('.ind-picker').forEach(initIndustryPicker);
})();

function initIndustryPicker(root){
  const btn = root.querySelector('.ind-trigger');
  const list = root.querySelector('.ind-list');
  const options = [...root.querySelectorAll('[role="option"]')];
  const panels = [...root.querySelectorAll('.ind-panel')];
  if (!btn || !list || !options.length) return;

  let open = false;
  let active = Math.max(0, options.findIndex(o => o.getAttribute('aria-selected') === 'true'));

  options.forEach(o => { o.tabIndex = -1; });

  function setOpen(v){
    open = v;
    btn.setAttribute('aria-expanded', v ? 'true' : 'false');
    if (v) list.removeAttribute('hidden');
    else list.setAttribute('hidden', '');
    if (v){
      highlight(active);
      options[active].focus();
    }
  }

  function highlight(i){
    options.forEach((o, j) => o.classList.toggle('is-active', j === i));
  }

  function select(i){
    active = i;
    const opt = options[i];
    const id = opt.getAttribute('data-ind');
    options.forEach((o, j) => o.setAttribute('aria-selected', j === i ? 'true' : 'false'));
    const label = btn.querySelector('.ind-value');
    if (label) label.textContent = opt.textContent.trim();
    panels.forEach(panel => {
      const on = panel.getAttribute('data-ind') === id;
      if (on) panel.removeAttribute('hidden');
      else panel.setAttribute('hidden', '');
    });
    highlight(i);
    setOpen(false);
    btn.focus();
  }

  btn.addEventListener('click', (e) => {
    e.preventDefault();
    setOpen(!open);
  });
  btn.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' '){
      e.preventDefault();
      if (!open) setOpen(true);
      if (e.key === 'ArrowUp') active = Math.max(0, active - 1);
      if (e.key === 'ArrowDown') active = Math.min(options.length - 1, active + 1);
      highlight(active);
      options[active].focus();
    }
  });
  list.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown'){
      e.preventDefault();
      active = Math.min(options.length - 1, active + 1);
      highlight(active);
      options[active].focus();
    } else if (e.key === 'ArrowUp'){
      e.preventDefault();
      active = Math.max(0, active - 1);
      highlight(active);
      options[active].focus();
    } else if (e.key === 'Home'){
      e.preventDefault();
      active = 0;
      highlight(active);
      options[active].focus();
    } else if (e.key === 'End'){
      e.preventDefault();
      active = options.length - 1;
      highlight(active);
      options[active].focus();
    } else if (e.key === 'Enter' || e.key === ' '){
      e.preventDefault();
      select(active);
    } else if (e.key === 'Escape'){
      e.preventDefault();
      setOpen(false);
      btn.focus();
    } else if (e.key === 'Tab'){
      setOpen(false);
    }
  });
  options.forEach((o, i) => {
    o.addEventListener('click', (e) => {
      e.preventDefault();
      select(i);
    });
    o.addEventListener('mousemove', () => highlight(i));
  });
  document.addEventListener('pointerdown', (e) => {
    if (open && !root.contains(e.target)) setOpen(false);
  });
}

/* Header dropdowns: hover and click on desktop, expandable groups on mobile */
(function(){
  const groups = [...document.querySelectorAll('.nav-group')];
  if (!groups.length) return;
  const desktop = () => window.matchMedia('(min-width: 961px)').matches;
  const canHover = () => window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const parts = (g) => ({ btn: g.querySelector('.nav-trigger'), menu: g.querySelector('.nav-menu') });
  const timers = new WeakMap();

  function setOpen(g, v){
    const { btn, menu } = parts(g);
    if (!v) g.dataset.pinned = 'false';
    btn.setAttribute('aria-expanded', v ? 'true' : 'false');
    if (v) menu.removeAttribute('hidden'); else menu.setAttribute('hidden', '');
  }
  function closeAll(except){ groups.forEach(g => { if (g !== except) setOpen(g, false); }); }
  const isOpen = (g) => parts(g).btn.getAttribute('aria-expanded') === 'true';

  groups.forEach(g => {
    const { btn, menu } = parts(g);
    const links = () => [...menu.querySelectorAll('a')];
    btn.addEventListener('click', () => {
      let v = !isOpen(g);
      if (desktop() && canHover()){
        // opened by hover: a click pins it open; a second click closes it
        if (isOpen(g) && g.dataset.pinned !== 'true'){ g.dataset.pinned = 'true'; v = true; }
        else { g.dataset.pinned = 'false'; }
      }
      if (desktop()) closeAll(g);
      setOpen(g, v);
    });
    btn.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown'){ e.preventDefault(); setOpen(g, true); closeAll(g); links()[0].focus(); }
      if (e.key === 'Escape'){ setOpen(g, false); }
    });
    menu.addEventListener('keydown', (e) => {
      const l = links(); const i = l.indexOf(document.activeElement);
      if (e.key === 'ArrowDown'){ e.preventDefault(); l[Math.min(l.length - 1, i + 1)].focus(); }
      else if (e.key === 'ArrowUp'){ e.preventDefault(); if (i <= 0) btn.focus(); else l[i - 1].focus(); }
      else if (e.key === 'Home'){ e.preventDefault(); l[0].focus(); }
      else if (e.key === 'End'){ e.preventDefault(); l[l.length - 1].focus(); }
      else if (e.key === 'Escape'){ e.preventDefault(); setOpen(g, false); btn.focus(); }
    });
    g.addEventListener('focusout', (e) => {
      if (desktop() && !g.contains(e.relatedTarget)) setOpen(g, false);
    });
    g.addEventListener('mouseenter', () => {
      if (!desktop() || !canHover()) return;
      clearTimeout(timers.get(g)); closeAll(g); setOpen(g, true);
    });
    g.addEventListener('mouseleave', () => {
      if (!desktop() || !canHover()) return;
      if (g.dataset.pinned === 'true') return;
      timers.set(g, setTimeout(() => setOpen(g, false), 160));
    });
  });
  document.addEventListener('pointerdown', (e) => {
    if (!e.target.closest('.nav-group')) closeAll();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape'){
      const open = groups.find(isOpen);
      if (open){ setOpen(open, false); parts(open).btn.focus(); }
    }
  });
  window.addEventListener('resize', () => { if (desktop()) closeAll(); });
})();

(function(){
  document.querySelectorAll('[data-flow]').forEach(root => {
    const tabs = [...root.querySelectorAll('[role="tab"]')];
    const board = root.querySelector('.flow-board');
    const copies = [...root.querySelectorAll('[data-mode-copy]')];
    if (!tabs.length || !board) return;

    function select(tab, focus){
      const mode = tab.getAttribute('data-mode');
      tabs.forEach(t => t.setAttribute('aria-selected', t === tab ? 'true' : 'false'));
      board.setAttribute('data-mode', mode);
      board.setAttribute('aria-labelledby', tab.id);
      copies.forEach(p => {
        if (p.getAttribute('data-mode-copy') === mode) p.removeAttribute('hidden');
        else p.setAttribute('hidden', '');
      });
      if (focus) tab.focus();
    }

    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => select(tab, false));
      tab.addEventListener('keydown', (e) => {
        let next = null;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = tabs[(i + 1) % tabs.length];
        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = tabs[(i - 1 + tabs.length) % tabs.length];
        if (e.key === 'Home') next = tabs[0];
        if (e.key === 'End') next = tabs[tabs.length - 1];
        if (next){ e.preventDefault(); select(next, true); }
      });
    });
  });
})();

(function(){
  const BASE = 900;
  function fitPscreens(){
    document.querySelectorAll('.pscreen').forEach(el => {
      const inner = el.querySelector('.pscreen-inner');
      if (!inner) return;
      const w = el.clientWidth;
      const compact = w > 0 && w < 540;
      el.classList.toggle('is-compact', compact);
      if (compact){
        inner.style.transform = 'none';
        inner.style.marginLeft = '0';
        return;
      }
      const s = Math.min(1, w / BASE);
        inner.style.transform = 'scale(' + s + ')';
        inner.style.marginLeft = ((w - BASE * s) / 2) + 'px';
    });
  }
  fitPscreens();
  window.addEventListener('resize', fitPscreens);
  if (document.fonts?.ready) document.fonts.ready.then(fitPscreens);
})();

(function(){
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduce) document.documentElement.classList.add('js-motion');

  function once(el, fn){
    if (!el || el.dataset.played === '1') return;
    el.dataset.played = '1';
    fn(el);
  }

  function watch(el, fn, opts){
    if (!el) return;
    if (reduce){ fn(el); return; }
    const io = new IntersectionObserver((ents) => {
      ents.forEach((e) => {
        if (!e.isIntersecting) return;
        once(el, fn);
        io.unobserve(el);
      });
    }, opts || { threshold: 0.28, rootMargin: '0px 0px -8% 0px' });
    io.observe(el);
  }

  function countTo(el, from, to, dur){
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = String(Math.round(from + (to - from) * eased));
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = String(to);
    };
    requestAnimationFrame(tick);
  }

  function scaleOf(host){
    const r = host.getBoundingClientRect();
    return host.offsetWidth ? r.width / host.offsetWidth : 1;
  }

  function localRect(target, host){
    const hr = host.getBoundingClientRect();
    const tr = target.getBoundingClientRect();
    const s = scaleOf(host);
    return {
      top: (tr.top - hr.top) / s,
      left: (tr.left - hr.left) / s,
      width: tr.width / s,
      height: tr.height / s
    };
  }

  function place(box, target, host){
    const r = localRect(target, host);
    const pad = 3;
    box.style.top = (r.top - pad) + 'px';
    box.style.left = (r.left - pad) + 'px';
    box.style.width = (r.width + pad * 2) + 'px';
    box.style.height = (r.height + pad * 2) + 'px';
    box.hidden = false;
  }

  function placeTip(tip, src, host, mode){
    const r = localRect(src, host);
    const maxL = Math.max(0, host.offsetWidth - 86);
    let top, left;
    if (mode === 'above'){
      top = Math.max(0, r.top - 20);
      left = Math.min(maxL, r.left);
    } else if (mode === 'right'){
      top = Math.max(0, r.top + (r.height - 16) / 2);
      left = r.left + r.width + 8;
      if (left > maxL) left = Math.max(0, r.left - 8);
    } else {
      top = Math.max(0, r.top + 4);
      left = Math.min(maxL, r.left + 8);
    }
    tip.style.top = top + 'px';
    tip.style.left = Math.max(0, Math.min(maxL, left)) + 'px';
  }

  function playExtract(screen){
    if (reduce){
      screen.classList.add('is-extract');
      screen.querySelectorAll('.ps-tip').forEach((t) => t.classList.add('is-on'));
      return;
    }
    const doc = screen.querySelector('.ps-doc');
    const box = screen.querySelector('.ps-box');
    if (!doc || !box){ screen.classList.add('is-extract'); return; }
    const hops = ['amount', 'date', 'stamp']
      .map((k) => doc.querySelector('[data-hot="' + k + '"]'))
      .filter(Boolean);
    const showTips = () => {
      box.hidden = true;
      screen.classList.add('is-extract');
      const modes = { supplier: 'above', date: 'right', lines: 'start' };
      ['supplier', 'date', 'lines'].forEach((k, n) => {
        setTimeout(() => {
          const tip = doc.querySelector('.ps-tip[data-tip="' + k + '"]');
          const src = doc.querySelector('[data-hot="' + k + '"]');
          if (tip && src){
            placeTip(tip, src, doc, modes[k]);
            tip.classList.add('is-on');
          }
        }, n * 280);
      });
    };
    if (!hops.length){ showTips(); return; }
    box.style.transition = 'none';
    place(box, hops[0], doc);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { box.style.transition = ''; });
    });
    let i = 1;
    const step = () => {
      if (i < hops.length){
        place(box, hops[i], doc);
        i += 1;
        setTimeout(step, 720);
      } else {
        setTimeout(showTips, 560);
      }
    };
    setTimeout(step, 720);
  }

  function playAnalyze(screen){
    screen.classList.add('is-analyze');
  }

  function playControl(screen){
    const status = screen.querySelector('.ps-status');
    const num = screen.querySelector('[data-count-to]');
    const btn = screen.querySelector('.ps-fwd');
    const pass = () => {
      if (status){
        status.textContent = 'Passed';
        status.classList.remove('is-wait');
        status.classList.add('is-pass');
      }
      if (num){
        const to = Number(num.getAttribute('data-count-to'));
        const from = Number(num.getAttribute('data-count-from') || '0');
        if (reduce) num.textContent = String(to);
        else countTo(num, from, to, 650);
      }
    };
    if (reduce){
      pass();
      return;
    }
    setTimeout(pass, 480);
    setTimeout(() => { if (btn) btn.classList.add('is-pulse'); }, 1400);
  }

  const storyPlays = [playExtract, playAnalyze, playControl];

  function playShot(shot, index){
    if (!shot) return;
    const screen = shot.querySelector('.pscreen.is-live');
    if (!screen) return;
    once(screen, () => {
      const fn = storyPlays[index];
      if (fn) fn(screen);
    });
  }

  document.addEventListener('story:activate', (e) => {
    const shot = e.detail.shot;
    const index = e.detail.index;
    if (!shot) return;
    const tryPlay = () => {
      const r = shot.getBoundingClientRect();
      if (r.height === 0) return false;
      if (r.bottom > 80 && r.top < window.innerHeight - 80){
        playShot(shot, index);
        return true;
      }
      return false;
    };
    if (tryPlay()) return;
    const io = new IntersectionObserver((ents) => {
      if (ents.some((en) => en.isIntersecting) && shot.classList.contains('active')){
        playShot(shot, index);
        io.disconnect();
      }
    }, { threshold: 0.28 });
    io.observe(shot);
  });

  const activeShot = document.querySelector('.story-shot.active');
  if (activeShot){
    document.dispatchEvent(new CustomEvent('story:activate', {
      detail: { index: Number(activeShot.getAttribute('data-shot') || 0), shot: activeShot }
    }));
  }

  const wall = document.querySelector('.doc-wall');
  watch(wall, (el) => {
    el.classList.add('is-in');
    if (reduce) return;
    const follow = el.querySelector('.wall-line-follow');
    if (follow){
      setTimeout(() => follow.classList.add('is-on'), 1500);
    }
  }, { threshold: 0.22 });

  document.querySelectorAll('.circuit-story, .story-band').forEach((el) => {
    if (el.classList.contains('story-band')) watch(el, (n) => n.classList.add('is-in'), { threshold: 0.15 });
  });

  const stats = document.querySelector('[data-motion="stats"]');
  if (stats){
    const nums = [...stats.querySelectorAll('[data-count]')];
    watch(stats, (el) => {
      el.classList.add('is-in');
      if (reduce) return;
      nums.forEach((n) => {
        const to = Number(n.getAttribute('data-count'));
        n.textContent = '0';
        countTo(n, 0, to, 1100);
      });
    }, { threshold: 0.55 });
  }

  const clients = document.querySelector('.clients');
  watch(clients, (el) => el.classList.add('is-in'), { threshold: 0.2 });

  const closing = document.querySelector('[data-motion="float"]');
  watch(closing, (el) => el.classList.add('is-in'), { threshold: 0.2 });
})();

(function () {
  const cards = [...document.querySelectorAll('[data-voice]')];
  if (!cards.length) return;

  const btnOf = (card) => card.querySelector('.voice-toggle');
  const panelOf = (card) => card.querySelector('.voice-back');
  const labelOf = (btn) => btn.querySelector('.voices-sr');

  function setOpen(card, open) {
    const btn = btnOf(card);
    const panel = panelOf(card);
    card.classList.toggle('is-open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    panel.setAttribute('aria-hidden', open ? 'false' : 'true');
    const label = open ? btn.getAttribute('data-close-label') : btn.getAttribute('data-open-label');
    if (label && labelOf(btn)) labelOf(btn).textContent = label;
  }

  function closeAll(except) {
    cards.forEach((card) => {
      if (card !== except) setOpen(card, false);
    });
  }

  cards.forEach((card) => {
    setOpen(card, false);
    btnOf(card).addEventListener('click', () => {
      const open = !card.classList.contains('is-open');
      if (open) closeAll(card);
      setOpen(card, open);
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAll();
  });
})();
