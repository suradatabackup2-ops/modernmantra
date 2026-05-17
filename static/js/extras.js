/* ═══════════════════════════════════════════
   MODERN MANTRA — ENHANCEMENTS (additive)
   Hooked into base.html via {% static 'js/extras.js' %}
   Loads AFTER main.js so it can wrap its functions safely.
   ═══════════════════════════════════════════ */
(function () {
  'use strict';

  // Respect "reduced motion" preference.
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ─── Page-load fade ────────────────────────────────────────────
  document.documentElement.classList.add('mm-ready');
  document.body.classList.add('mm-loading');
  window.addEventListener('load', function () {
    document.body.classList.remove('mm-loading');
    document.body.classList.add('mm-loaded');
  });
  // Failsafe in case 'load' is delayed by a slow image
  setTimeout(function () {
    document.body.classList.remove('mm-loading');
    document.body.classList.add('mm-loaded');
  }, 1200);

  // ─── Scroll-reveal via IntersectionObserver ────────────────────
  if (!prefersReduced && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -80px 0px', threshold: 0.05 });

    document.querySelectorAll('.mm-reveal, .mm-stagger').forEach(function (el) {
      io.observe(el);
    });

    // Also auto-upgrade any pre-existing `.reveal` / `.reveal-right` from the
    // legacy stylesheet — saves us editing every template.
    document.querySelectorAll('.reveal, .reveal-right, .reveal-left').forEach(function (el) {
      if (!el.classList.contains('mm-reveal')) {
        el.classList.add('mm-reveal');
        if (el.classList.contains('reveal-right')) el.classList.add('mm-reveal-right');
        if (el.classList.contains('reveal-left'))  el.classList.add('mm-reveal-left');
        io.observe(el);
      }
    });
  } else {
    // Reduced motion or no IO support → make everything visible immediately.
    document.querySelectorAll('.mm-reveal, .mm-stagger, .reveal, .reveal-right, .reveal-left')
      .forEach(function (el) { el.classList.add('is-in'); });
  }

  // ─── Image fade-in on load ─────────────────────────────────────
  document.querySelectorAll('img').forEach(function (img) {
    if (img.dataset.mmNoFade) return;
    img.classList.add('mm-fade-img');
    if (img.complete && img.naturalWidth > 0) {
      img.classList.add('is-loaded');
    } else {
      img.addEventListener('load',  function () { img.classList.add('is-loaded'); });
      img.addEventListener('error', function () { img.classList.add('is-loaded'); });
    }
  });

  // ─── Card tilt — applied to package & testimonial cards ────────
  if (!prefersReduced) {
    const tiltSelector = '.pkg-card, .testi-card, .feature-card';
    document.querySelectorAll(tiltSelector).forEach(function (card) {
      card.classList.add('mm-tilt');
    });
  }

  // ─── Back-to-top button ─────────────────────────────────────────
  const btn = document.createElement('button');
  btn.className = 'mm-to-top';
  btn.setAttribute('aria-label', 'Back to top');
  btn.innerHTML = '↑';
  btn.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: prefersReduced ? 'auto' : 'smooth' });
  });
  document.body.appendChild(btn);

  let ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      btn.classList.toggle('is-visible', window.scrollY > 600);
      ticking = false;
    });
  });

  // ─── Newsletter form ────────────────────────────────────────────
  document.querySelectorAll('form.mm-newsletter').forEach(function (form) {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      const emailInput = form.querySelector('input[type=email]');
      const submitBtn = form.querySelector('button[type=submit]');
      const successEl = form.parentElement.querySelector('.mm-newsletter-success');
      if (!emailInput || !emailInput.value.trim()) return;

      submitBtn.disabled = true;
      const origText = submitBtn.textContent;
      submitBtn.textContent = 'Subscribing…';

      try {
        const fd = new FormData();
        fd.append('email', emailInput.value.trim());
        fd.append('source', form.dataset.source || 'footer');
        const url = (window.MM_ENDPOINTS && window.MM_ENDPOINTS.newsletter) || '/api/catalog/newsletter/';
        const res = await fetch(url, {
          method: 'POST',
          body: fd,
          credentials: 'same-origin',
          headers: {
            'X-CSRFToken': window.MM_CSRF_TOKEN || '',
            'Accept': 'application/json'
          }
        });
        const data = await res.json().catch(function () { return {}; });
        if (res.ok && data.ok) {
          form.reset();
          if (successEl) successEl.textContent = '✓ Thanks for subscribing!';
          else if (typeof showToast === 'function') showToast('✓ Subscribed!');
        } else {
          const msg = (data && data.error) || 'Something went wrong. Try again.';
          if (successEl) { successEl.style.color = '#e08'; successEl.textContent = msg; }
          else if (typeof showToast === 'function') showToast('⚠️ ' + msg);
        }
      } catch (err) {
        if (typeof showToast === 'function') showToast('⚠️ Network error. Try again.');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = origText;
      }
    });
  });

  // ─── Subtle parallax on hero (off on small screens) ─────────────
  if (!prefersReduced && window.innerWidth > 900) {
    const hero = document.getElementById('hero') ||
                 document.querySelector('.hero-section, [class*="hero-bg"]');
    if (hero) {
      let ticking2 = false;
      window.addEventListener('scroll', function () {
        if (ticking2) return;
        ticking2 = true;
        requestAnimationFrame(function () {
          const y = Math.min(window.scrollY, 600);
          hero.style.backgroundPositionY = (y * 0.35) + 'px';
          ticking2 = false;
        });
      });
    }
  }
  // ─── Inject "View details →" links on package cards ─────────────
  // Each card has data-trip="Trip Name". We slug it and link to the detail page.
  function _slugify(s) {
    return s
      .toLowerCase()
      .replace(/[\u2013\u2014]/g, '-')   // en dash, em dash → hyphen
      .replace(/[^a-z0-9\s-]/g, '')      // drop everything else
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }
  document.querySelectorAll('.pkg-card[data-trip]').forEach(function (card) {
    var trip = card.dataset.trip;
    if (!trip) return;
    if (card.querySelector('.pd-card-link')) return; // already injected
    var slug = _slugify(trip);
    var link = document.createElement('a');
    link.className = 'pd-card-link';
    link.href = '/packages/' + slug + '/';
    link.textContent = 'View full details →';
    link.style.cssText =
      'display:inline-block;margin-top:8px;color:var(--forest,#4A7C59);'
      + 'font-size:.85rem;font-weight:500;text-decoration:none;'
      + 'border-bottom:1px solid transparent;transition:border-color .2s;';
    link.addEventListener('mouseenter', function () {
      link.style.borderBottomColor = 'var(--forest, #4A7C59)';
    });
    link.addEventListener('mouseleave', function () {
      link.style.borderBottomColor = 'transparent';
    });
    // Inject just before the buttons section
    var bottomBtns = card.querySelector('.pkg-actions, .pkg-cta, .pkg-buttons');
    var content = card.querySelector('.pkg-content, .pkg-body');
    if (bottomBtns) bottomBtns.parentNode.insertBefore(link, bottomBtns);
    else if (content) content.appendChild(link);
    else card.appendChild(link);
  });

})();
