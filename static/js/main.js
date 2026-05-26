/* ═══════════════════════════════════════════
   MODERN MANTRA — SHARED JS
   ═══════════════════════════════════════════ */

// ── Form endpoints ──
// Django sets window.MM_ENDPOINTS in base.html. We fall back to legacy
// Formspree URLs only when the site is served as plain static files (no Django).
const ENDPOINTS = (window.MM_ENDPOINTS) ? {
  enquiry:  window.MM_ENDPOINTS.enquiry,
  register: window.MM_ENDPOINTS.registration,
  booking:  window.MM_ENDPOINTS.booking,
  review:   window.MM_ENDPOINTS.review
} : {
  enquiry:  'https://formspree.io/f/xqengvqe',
  register: 'https://formspree.io/f/mojrpodn',
  booking:  'https://formspree.io/f/xvzlvjal'
};

// ─────────────────────────────────────────────────────────────────
// 🗄️  GOOGLE SHEETS BACKEND (legacy — disabled when running on Django)
// When window.MM_ENDPOINTS exists (Django-rendered page) we skip this
// path entirely; Django is the source of truth and the form-submit
// helper below already persists to the database.
// ─────────────────────────────────────────────────────────────────
const MM_BACKEND = {
  url:    (window.MM_ENDPOINTS) ? '' : 'https://script.google.com/macros/s/AKfycbyIS-GdmUhanMB44l9egY4LBMKk7wOqzj-CmKA6xDYztr2lXkm4nxts-tXSfHTzeUfG/exec',
  secret: (window.MM_ENDPOINTS) ? '' : 'modernmantra2026',
  offlineFirst: false
};

// Bootstrap from localStorage (when admin saved it via the Backend tab)
try {
  const _u = localStorage.getItem('mm_be_url');
  const _s = localStorage.getItem('mm_be_secret');
  if (_u && !MM_BACKEND.url)    MM_BACKEND.url    = _u;
  if (_s && !MM_BACKEND.secret) MM_BACKEND.secret = _s;
} catch (e) { /* no localStorage */ }
// ─────────────────────────────────────────────────────────────────

// ── Backend API adapter ──
const MMBackend = {
  isEnabled() { return !!(MM_BACKEND.url && MM_BACKEND.secret); },

  async _post(action, data) {
    if (!this.isEnabled()) return { ok:false, error:'not_configured' };
    try {
      const res = await fetch(MM_BACKEND.url, {
        method: 'POST',
        // Apps Script doesn't allow custom headers from CORS, so we send the secret in the body
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify({ action, data, secret: MM_BACKEND.secret })
      });
      return await res.json();
    } catch (e) {
      console.warn('MMBackend POST failed:', e.message);
      return { ok:false, error:String(e) };
    }
  },

  async _get(action, extra) {
    if (!this.isEnabled()) return { ok:false, error:'not_configured' };
    try {
      const params = new URLSearchParams({ action, secret: MM_BACKEND.secret, ...(extra || {}) });
      const res = await fetch(MM_BACKEND.url + '?' + params.toString());
      return await res.json();
    } catch (e) {
      console.warn('MMBackend GET failed:', e.message);
      return { ok:false, error:String(e) };
    }
  },

  // Public methods
  addEnquiry(data)    { return this._post('addEnquiry', data); },
  addBooking(data)    { return this._post('addBooking', data); },
  addReview(data)     { return this._post('addReview', data); },
  updateStatus(type, id, status) { return this._post('updateStatus', {type, id, status}); },
  updateNotes(type, id, notes)   { return this._post('updateNotes', {type, id, notes}); },
  updatePrice(trip, price, by)   { return this._post('updatePrice', {trip, price, updatedBy: by}); },
  approveReview(id, approved)    { return this._post('approveReview', {id, approved}); },
  deleteRow(type, id)            { return this._post('deleteRow', {type, id}); },
  setConfig(key, value)          { return this._post('setConfig', {key, value}); },
  addBatch(data)                 { return this._post('addBatch', data); },
  updateBatch(data)              { return this._post('updateBatch', data); },
  deleteBatch(id)                { return this._post('deleteBatch', {id}); },
  setComingSoon(trip, value)     { return this._post('setComingSoon', {trip, value}); },
  getConfig()         { return this._get('getConfig'); },
  getBatches()        { return this._get('getBatches'); },
  ping()              { return this._post('ping', {}); },
  getAll()            { return this._get('getAll'); },
  getEnquiries()      { return this._get('getEnquiries'); },
  getBookings()       { return this._get('getBookings'); },
  getReviews()        { return this._get('getReviews'); },
  getPrices()         { return this._get('getPrices'); }
};

// Expose globally
window.MMBackend = MMBackend;
window.MM_BACKEND = MM_BACKEND;


const MM_NOTIFY = {
  // Option 1 (EASIEST, recommended): ntfy.sh – completely free, no signup
  // 1. Install "ntfy" app on your phone from Play Store / App Store
  // 2. Pick a UNIQUE secret topic name below (e.g. mantra-alerts-x9k7q3)
  // 3. In the app, tap + and subscribe to that topic name
  // Leave empty ('') to disable.
  ntfyTopic: '',

  // Option 2: Telegram bot — richer formatting
  // Token is visible to site visitors but Telegram bots can only send TO chats
  // they are members of, so worst-case is spam to your own chat (which is rate-limited).
  telegramBotToken: '',
  telegramChatId:   ''
};
// ─────────────────────────────────────────────────────────────────

// ── Reading progress bar ── (skip on admin)
(function(){
  if (document.body && document.body.dataset.admin === 'true') return;
  if (location.pathname.endsWith('admin.html')) return;
  const bar = document.createElement('div');
  bar.id = 'read-progress';
  document.body.prepend(bar);
  window.addEventListener('scroll', () => {
    const doc = document.documentElement;
    const pct = (doc.scrollTop / (doc.scrollHeight - doc.clientHeight)) * 100;
    bar.style.width = Math.min(pct, 100) + '%';
  }, { passive: true });
})();

// ── Back to top ── (skip on admin)
(function(){
  if (location.pathname.endsWith('admin.html')) return;
  const btn = document.createElement('button');
  btn.id = 'back-top';
  btn.innerHTML = '↑';
  btn.title = 'Back to top';
  btn.setAttribute('aria-label', 'Back to top');
  document.body.appendChild(btn);
  window.addEventListener('scroll', () => btn.classList.toggle('show', window.scrollY > 400), { passive: true });
  btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
})();

// ── Page navigation: instant, no transition ──
(function(){})();

document.addEventListener('DOMContentLoaded', () => {
  const nav = document.getElementById('mainNav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 60);
    });
  }

  // ── Dark mode toggle ──
  const darkBtn = document.createElement('button');
  darkBtn.id = 'dark-toggle';
  darkBtn.setAttribute('aria-label', 'Toggle dark mode');
  darkBtn.title = 'Toggle dark mode';
  const isDark = localStorage.getItem('mm-dark') === '1';
  if (isDark) document.body.classList.add('dark-mode');
  darkBtn.textContent = isDark ? '☀️' : '🌙';
  document.body.appendChild(darkBtn);
  darkBtn.addEventListener('click', () => {
    const on = document.body.classList.toggle('dark-mode');
    darkBtn.textContent = on ? '☀️' : '🌙';
    localStorage.setItem('mm-dark', on ? '1' : '0');
  });


  const heroSection = document.getElementById('hero');
  if (heroSection) {
    window.addEventListener('scroll', () => {
      const sy = window.scrollY;
      const slides = heroSection.querySelectorAll('.hero-slide');
      slides.forEach(s => {
        s.style.transform = `translateY(${sy * 0.18}px)`;
      });
    }, { passive: true });
  }

  // ── iOS parallax fallback for .parallax-divider ──
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  if (isIOS) {
    document.querySelectorAll('.parallax-divider, .page-hero').forEach(el => {
      el.style.backgroundAttachment = 'scroll';
      window.addEventListener('scroll', () => {
        const top = el.getBoundingClientRect().top;
        el.style.backgroundPositionY = `calc(50% + ${-top * 0.28}px)`;
      }, { passive: true });
    });
  }

  // ── Staggered card reveal for destination & package grids ──
  document.querySelectorAll('.dest-grid .dest-card, .pkg-grid .pkg-card, .why-grid .why-card').forEach((el, i) => {
    el.style.transitionDelay = `${i * 75}ms`;
  });

  // ── Button ripple effect ──
  document.querySelectorAll('.btn-primary, .btn-book').forEach(btn => {
    btn.addEventListener('click', e => {
      const r = document.createElement('span');
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      r.className = 'ripple';
      r.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX - rect.left - size / 2}px;top:${e.clientY - rect.top - size / 2}px`;
      btn.appendChild(r);
      setTimeout(() => r.remove(), 520);
    });
  });

  // ── Hero skeleton shimmer on load ──
  if (heroSection) {
    const sk = document.createElement('div');
    sk.className = 'hero-skeleton';
    heroSection.appendChild(sk);
    window.addEventListener('load', () => {
      setTimeout(() => { sk.style.opacity = '0'; }, 250);
      setTimeout(() => { sk.remove(); }, 700);
    });
    setTimeout(() => { if (sk.parentNode) { sk.style.opacity = '0'; setTimeout(() => sk.remove(), 500); } }, 2200);
  }

  // ── Hero title word-by-word reveal ──
  const heroTitle = document.querySelector('.hero-title');
  if (heroTitle) {
    const html = heroTitle.innerHTML;
    let wordIndex = 0;
    heroTitle.innerHTML = html.replace(/(\S+)/g, w => {
      const delay = (wordIndex++ * 0.072).toFixed(3);
      return `<span class="hero-word" style="animation-delay:${delay}s">${w}</span> `;
    });
  }

  // ── Magnetic cursor trail on hero ──
  const cursorEl = document.createElement('div');
  cursorEl.id = 'mm-cursor';
  document.body.appendChild(cursorEl);
  let mx = 0, my = 0, cx = 0, cy = 0;
  const heroCursorTarget = document.getElementById('hero');
  if (heroCursorTarget) {
    heroCursorTarget.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; cursorEl.style.opacity = '1'; });
    heroCursorTarget.addEventListener('mouseleave', () => { cursorEl.style.opacity = '0'; });
    (function cursorLoop() {
      cx += (mx - cx) * 0.13; cy += (my - cy) * 0.13;
      cursorEl.style.left = cx + 'px'; cursorEl.style.top = cy + 'px';
      requestAnimationFrame(cursorLoop);
    })();
  }

  // ── Section label animated line ──
  const labelObs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('line-ready'); labelObs.unobserve(e.target); } });
  }, { threshold: 0.3 });
  document.querySelectorAll('.section-label').forEach(el => labelObs.observe(el));

  // ── About images scroll float ──
  const aImg1 = document.querySelector('.about-img1');
  const aImg2 = document.querySelector('.about-img2');
  const aboutSec = document.getElementById('about');
  if (aImg1 && aImg2 && aboutSec) {
    window.addEventListener('scroll', () => {
      const rect = aboutSec.getBoundingClientRect();
      const progress = -rect.top / aboutSec.offsetHeight;
      if (progress > -0.4 && progress < 1.3) {
        aImg1.style.transform = `translateY(${progress * -24}px)`;
        aImg2.style.transform = `translateY(${progress * 20}px)`;
      }
    }, { passive: true });
  }

  // ── Destination card SVG border trace ──
  document.querySelectorAll('.dest-card').forEach(card => {
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.classList.add('dest-card-tracer');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('preserveAspectRatio', 'none');
    const rect = document.createElementNS(svgNS, 'rect');
    rect.setAttribute('x', '1'); rect.setAttribute('y', '1');
    rect.setAttribute('width', '98'); rect.setAttribute('height', '98');
    rect.setAttribute('rx', '5');
    svg.appendChild(rect);
    card.appendChild(svg);
  });

  // ── Package price count-up on hover ──
  document.querySelectorAll('.pkg-card').forEach(card => {
    const amountEl = card.querySelector('.pkg-price .amount');
    if (!amountEl) return;
    const raw = amountEl.textContent.trim();
    const num = parseInt(raw.replace(/[^0-9]/g, ''));
    if (!num) return;
    const prefix = raw.match(/[₹$€£]/)?.[0] || '';
    const suffix = raw.replace(/[₹$€£0-9,]/g, '');
    let running = false;
    card.addEventListener('mouseenter', () => {
      if (running) return; running = true;
      const dur = 580; const start = Date.now();
      const tick = () => {
        const p = Math.min((Date.now() - start) / dur, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        amountEl.textContent = prefix + Math.round(num * ease).toLocaleString('en-IN') + suffix;
        if (p < 1) requestAnimationFrame(tick);
        else { amountEl.textContent = raw; running = false; }
      };
      requestAnimationFrame(tick);
    });
  });

  // ── Favourite heartbeat burst ──
  document.querySelectorAll('.pkg-fav').forEach(f => {
    f.addEventListener('click', function () {
      this.classList.remove('liked');
      void this.offsetWidth;
      const isLiked = this.textContent.trim() === '♥';
      this.textContent = isLiked ? '♡' : '♥';
      this.style.color = isLiked ? '' : '#e74c3c';
      if (!isLiked) this.classList.add('liked');
    });
  });

  // ── Float labels for enquiry form inputs ──
  document.querySelectorAll('#enquiry .form-group input, #enquiry .form-group select').forEach(input => {
    const label = input.parentElement.querySelector('label');
    if (!label) return;
    input.parentElement.insertBefore(input, label);
    const check = () => input.value ? input.classList.add('has-value') : input.classList.remove('has-value');
    input.addEventListener('input', check);
    input.addEventListener('change', check);
    check();
  });

  // Active nav link
  const path = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a, .nav-mobile a').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });

  // ── Hamburger ──
  const toggle = document.getElementById('navToggle');
  const mobileMenu = document.getElementById('navMobile');
  if (toggle && mobileMenu) {
    toggle.addEventListener('click', () => {
      toggle.classList.toggle('open');
      mobileMenu.classList.toggle('open');
    });
    mobileMenu.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        toggle.classList.remove('open');
        mobileMenu.classList.remove('open');
      });
    });
  }

  // ── Scroll reveal ──
  const revealEls = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
    });
  }, { threshold: 0.08 });
  revealEls.forEach(r => obs.observe(r));
  window.revealObs = obs;

  // ── Stat counter animation ──
  const statEls = document.querySelectorAll('.stat-num[data-target]');
  if (statEls.length) {
    const cObs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        cObs.unobserve(e.target);
        const el = e.target;
        const raw = el.dataset.target;
        const suffix = raw.replace(/[\d.]/g, '');
        const target = parseFloat(raw);
        const dur = 1600;
        const start = performance.now();
        el.classList.add('counted');
        function tick(now) {
          const p = Math.min((now - start) / dur, 1);
          const ease = 1 - Math.pow(1 - p, 3);
          const cur = target * ease;
          el.textContent = (Number.isInteger(target) ? Math.round(cur) : cur.toFixed(1)) + suffix;
          if (p < 1) requestAnimationFrame(tick);
          else el.textContent = raw;
        }
        requestAnimationFrame(tick);
      });
    }, { threshold: 0.5 });
    statEls.forEach(el => cObs.observe(el));
  }

  // ── Testimonial carousel ──
  const grid = document.getElementById('testiGrid');
  if (grid && grid.querySelector('.testi-track')) {
    const track = grid.querySelector('.testi-track');
    const cards = track.querySelectorAll('.testi-card');
    const dotsWrap = grid.parentElement.querySelector('.testi-dots');
    if (!dotsWrap || !cards.length) return;
    let cur = 0, timer;
    const dots = Array.from(dotsWrap.querySelectorAll('.testi-dot'));
    function goTo(n) {
      cur = (n + cards.length) % cards.length;
      track.style.transform = `translateX(-${cur * 100}%)`;
      dots.forEach((d, i) => d.classList.toggle('active', i === cur));
    }
    dots.forEach((d, i) => d.addEventListener('click', () => { clearInterval(timer); goTo(i); timer = setInterval(() => goTo(cur + 1), 5000); }));
    timer = setInterval(() => goTo(cur + 1), 5000);
  }

  // ── Package filter ──
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.dataset.cat;
      document.querySelectorAll('.pkg-card').forEach(c => {
        c.style.display = (cat === 'all' || c.dataset.cat?.includes(cat)) ? 'block' : 'none';
      });
    });
  });

  // ── Booking Modal ──
  const bookModal = document.getElementById('bookModal');
  if (bookModal) {
    bookModal.addEventListener('click', e => { if (e.target === bookModal) closeModal(); });
  }

  // ── Favourite toggle handled above with burst ──

  // ── Enquiry form ──
  const eForm = document.getElementById('enquiryForm');
  if (eForm) {
    eForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const btn = document.getElementById('enquiryBtn');
      saveEnquiryLocal(this);
      await sendToFormspree(this, ENDPOINTS.enquiry, btn, `✅ Enquiry sent! We'll reply within 24 hours.`);
    });
  }

  // ── Contact form ──

  // ── Booking modal form ──
  const bForm = document.getElementById('bookingForm');
  if (bForm) {
    bForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const btn = document.getElementById('bookingBtn');
      saveBookingLocal(this);
      const ok = await sendToFormspree(this, ENDPOINTS.booking, btn, `🎉 Booking request received! We'll WhatsApp you within 2 hours.`);
      if (ok) closeModal();
    });
  }

  // ── Register form ──
  const rForm = document.getElementById('registerForm');
  if (rForm) {
    rForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const btn = document.getElementById('registerBtn');
      await sendToFormspree(this, ENDPOINTS.register, btn, '🙌 Registered! Check your email for confirmation.');
    });
  }
});

// ── Save enquiry: backend (master) + localStorage (cache) ──
function saveEnquiryLocal(formEl) {
  try {
    const fd = new FormData(formEl);
    const item = {
      id:   'ENQ-' + Date.now(),
      name: fd.get('Name') || '',
      phone:fd.get('Phone') || '',
      email:fd.get('Email') || '',
      destination: fd.get('Destination') || '',
      groupSize:   fd.get('GroupSize') || '',
      month:       fd.get('Month') || '',
      budget:      fd.get('Budget') || '',
      message:     fd.get('Message') || '',
      time:   new Date().toISOString(),
      status: 'new'
    };
    // 1. Send to Google Sheets backend (fire-and-forget)
    if (MMBackend.isEnabled()) {
      MMBackend.addEnquiry(item).then(r => {
        if (r && r.ok && r.id) {
          // Re-tag local entry with backend's ID for sync
          try {
            const list = JSON.parse(localStorage.getItem('mm_enquiries') || '[]');
            const idx = list.findIndex(x => x.id === item.id);
            if (idx >= 0) { list[idx].id = r.id; list[idx]._synced = true; localStorage.setItem('mm_enquiries', JSON.stringify(list)); }
          } catch(e){}
        }
      });
    }
    // 2. Save to localStorage as offline cache (always)
    const enqs = JSON.parse(localStorage.getItem('mm_enquiries') || '[]');
    enqs.unshift(item);
    localStorage.setItem('mm_enquiries', JSON.stringify(enqs.slice(0, 500)));
    // 3. Push notification to admin
    sendToTelegram('📩 New Enquiry',
      `Name: ${item.name}\nPhone: ${item.phone}\nEmail: ${item.email}\nDestination: ${item.destination||'—'}\nGroup: ${item.groupSize||'—'}\nMonth: ${item.month||'—'}\nBudget: ${item.budget||'—'}\nMessage: ${item.message||'—'}`);
  } catch(e) { /* silent fail */ }
}

// ── Save booking: backend (master) + localStorage (cache) ──
function saveBookingLocal(formEl) {
  try {
    const fd = new FormData(formEl);
    const item = {
      id:      'BK-' + Date.now(),
      name:    fd.get('Name') || '',
      phone:   fd.get('Phone') || '',
      email:   fd.get('Email') || '',
      package: fd.get('Package') || '',
      price:   fd.get('Price') || '',
      persons: fd.get('Persons') || '',
      date:    fd.get('Date') || '',
      time:    new Date().toISOString(),
      status:  'new'
    };
    if (MMBackend.isEnabled()) {
      MMBackend.addBooking(item).then(r => {
        if (r && r.ok && r.id) {
          try {
            const list = JSON.parse(localStorage.getItem('mm_bookings') || '[]');
            const idx = list.findIndex(x => x.id === item.id);
            if (idx >= 0) { list[idx].id = r.id; list[idx]._synced = true; localStorage.setItem('mm_bookings', JSON.stringify(list)); }
          } catch(e){}
        }
      });
    }
    const books = JSON.parse(localStorage.getItem('mm_bookings') || '[]');
    books.unshift(item);
    localStorage.setItem('mm_bookings', JSON.stringify(books.slice(0, 500)));
    sendToTelegram('📋 New Booking',
      `Customer: ${item.name}\nPhone: ${item.phone}\nEmail: ${item.email}\nPackage: ${item.package}\nPrice: ${item.price}\nPersons: ${item.persons}\nPreferred date: ${item.date||'—'}`);
  } catch(e) { /* silent fail */ }
}

// ── Push notifications to admin (fire-and-forget) ──
async function sendToTelegram(title, body){
  // Try ntfy.sh first (simpler, no token in code)
  // Falls back to admin's localStorage if set there (logged-in admin browser)
  const ntfyTopic = MM_NOTIFY.ntfyTopic || localStorage.getItem('mm_ntfy_topic') || '';
  if (ntfyTopic) {
    try {
      await fetch('https://ntfy.sh/' + ntfyTopic, {
        method: 'POST',
        headers: {
          'Title':    title,
          'Tags':     'bell',
          'Priority': 'high'
        },
        body: body
      });
    } catch(e){ /* silent */ }
  }

  // Try Telegram
  const tk = MM_NOTIFY.telegramBotToken || localStorage.getItem('mm_tg_tok') || '';
  const ch = MM_NOTIFY.telegramChatId   || localStorage.getItem('mm_tg_chat') || '';
  if (tk && ch) {
    try {
      const msg = `*${title}*\n${body}\n\n_${new Date().toLocaleString('en-IN')}_`;
      await fetch(`https://api.telegram.org/bot${tk}/sendMessage`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({chat_id: ch, text: msg, parse_mode:'Markdown'})
      });
    } catch(e){ /* silent */ }
  }
}

// ── Form-submit helper ──
// Works against either Django (when window.MM_ENDPOINTS is set and the URL
// is same-origin) or legacy Formspree URLs. The Django path adds the CSRF
// token and reads the {ok, errors} response shape from apps/bookings/views.py.
async function sendToFormspree(formEl, endpoint, btnEl, successMsg) {
  const origText = btnEl.textContent;
  btnEl.textContent = 'Sending…';
  btnEl.disabled = true;

  const isDjango = !!(window.MM_ENDPOINTS) && !/^https?:\/\//i.test(endpoint);
  const headers = { 'Accept': 'application/json' };
  if (isDjango && window.MM_CSRF_TOKEN) {
    headers['X-CSRFToken'] = window.MM_CSRF_TOKEN;
  }

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      body: new FormData(formEl),
      headers: headers,
      credentials: 'same-origin'
    });
    const json = await res.json().catch(() => ({}));
    if (res.ok && (json.ok !== false)) {
      formEl.reset();
      showToast(successMsg);
      return true;
    }
    // Django: errors is {field: [msgs...]}. Formspree: errors is [{message: ...}]
    let errMsg = 'Submission failed.';
    if (json && json.errors) {
      if (Array.isArray(json.errors)) {
        errMsg = json.errors.map(e => e.message).join(', ');
      } else if (typeof json.errors === 'object') {
        errMsg = Object.entries(json.errors)
          .map(([f, msgs]) => `${f}: ${(Array.isArray(msgs) ? msgs.join(' ') : msgs)}`)
          .join(' · ');
      }
    }
    showToast('⚠️ ' + errMsg);
    return false;
  } catch (err) {
    showToast('⚠️ Network error. Please try again.');
    return false;
  } finally {
    btnEl.textContent = origText;
    btnEl.disabled = false;
  }
}

// ── Modal ──
function openModal(name, price) {
  const badge = document.getElementById('modalPackageBadge');
  const pName = document.getElementById('modalPackageName');
  const pPrice = document.getElementById('modalPackagePrice');
  if (badge) { badge.textContent = `📦 ${name}  ·  ${price} / person`; badge.style.display = 'block'; }
  if (pName) pName.value = name;
  if (pPrice) pPrice.value = price;
  document.getElementById('bookModal')?.classList.add('open');
}
function closeModal() {
  document.getElementById('bookModal')?.classList.remove('open');
  document.getElementById('bookingForm')?.reset();
  const badge = document.getElementById('modalPackageBadge');
  if (badge) badge.style.display = 'none';
}

// ── Toast ──
function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 5000);
}

// ═══════════════════════════════════════════════════════════
//  ADVANCED ANIMATIONS v4
// ═══════════════════════════════════════════════════════════

(function initAdvancedAnimations() {
  'use strict';

  // Skip heavy motion for users who prefer reduced motion
  const noMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── 1. Magnetic 3D card tilt ────────────────────────────
  if (!noMotion) {
    document.querySelectorAll('.pkg-card').forEach(card => {
      card.addEventListener('mousemove', e => {
        const r = card.getBoundingClientRect();
        const x = e.clientX - r.left - r.width  / 2;
        const y = e.clientY - r.top  - r.height / 2;
        const tiltX = (y / r.height) * -10;  // degrees
        const tiltY = (x / r.width)  *  10;
        card.classList.add('tilting');
        card.style.transform =
          `perspective(900px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateY(-10px) scale(1.01)`;
      });
      card.addEventListener('mouseleave', () => {
        card.classList.remove('tilting');
        card.style.transform = '';
      });
    });
  }

  // ── 2. Parallax scroll layers ───────────────────────────
  if (!noMotion) {
    const parallaxEls = document.querySelectorAll('[data-parallax]');
    if (parallaxEls.length) {
      function updateParallax() {
        const sy = window.scrollY;
        parallaxEls.forEach(el => {
          const speed = parseFloat(el.dataset.parallax) || 0.15;
          el.style.transform = `translateY(${sy * speed}px)`;
        });
      }
      window.addEventListener('scroll', updateParallax, { passive: true });
      updateParallax();
    }
  }

  // ── 3. Staggered reveal with IntersectionObserver ───────
  const revealEls = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
  if (revealEls.length && 'IntersectionObserver' in window) {
    const revealObs = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        // Stagger siblings that appear at the same time
        const siblings = Array.from(
          entry.target.parentElement?.querySelectorAll('.reveal, .reveal-left, .reveal-right') || []
        );
        const idx = siblings.indexOf(entry.target);
        const delay = idx * 80;  // ms between siblings
        setTimeout(() => entry.target.classList.add('visible'), delay);
        revealObs.unobserve(entry.target);
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(el => revealObs.observe(el));
  }

  // ── 4. Stat counter animation ───────────────────────────
  function animateCounter(el) {
    const target = parseInt(el.textContent.replace(/\D/g, ''), 10);
    if (isNaN(target) || target === 0) return;
    const suffix = el.textContent.replace(/[\d,]/g, '');
    const duration = 1400;
    const start = performance.now();
    function step(now) {
      const t = Math.min((now - start) / duration, 1);
      // Ease out expo
      const eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
      const val = Math.round(eased * target);
      el.textContent = val.toLocaleString('en-IN') + suffix;
      if (t < 1) requestAnimationFrame(step);
      else {
        el.textContent = target.toLocaleString('en-IN') + suffix;
        el.classList.add('counted');
      }
    }
    requestAnimationFrame(step);
  }

  const statEls = document.querySelectorAll('.stat-num');
  if (statEls.length && 'IntersectionObserver' in window) {
    const statObs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        if (!noMotion) animateCounter(e.target);
        else e.target.classList.add('counted');
        statObs.unobserve(e.target);
      });
    }, { threshold: 0.6 });
    statEls.forEach(el => statObs.observe(el));
  }

  // ── 5. Section label underline animate ─────────────────
  const labelObs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('line-ready');
        labelObs.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('.section-label').forEach(el => labelObs.observe(el));

  // ── 6. Smooth scroll for anchor links ──────────────────
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const id = a.getAttribute('href').slice(1);
      const target = document.getElementById(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── 7. Hero: soft cursor glow that follows mouse ────────
  if (!noMotion) {
    const hero = document.getElementById('hero');
    if (hero) {
      let glow = document.querySelector('.hero-cursor-glow');
      if (!glow) {
        glow = document.createElement('div');
        glow.className = 'hero-cursor-glow';
        glow.style.cssText = [
          'position:absolute', 'width:300px', 'height:300px',
          'border-radius:50%', 'pointer-events:none', 'z-index:3',
          'background:radial-gradient(circle, rgba(201,146,43,.18) 0%, transparent 70%)',
          'transform:translate(-50%,-50%)',
          'transition:left .12s ease, top .12s ease',
          'top:50%', 'left:50%'
        ].join(';');
        hero.appendChild(glow);
      }
      hero.addEventListener('mousemove', e => {
        const r = hero.getBoundingClientRect();
        glow.style.left = (e.clientX - r.left) + 'px';
        glow.style.top  = (e.clientY - r.top)  + 'px';
      });
    }
  }

})();
