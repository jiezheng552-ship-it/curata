/**
 * Curata — Main Script
 * Navigation, dark mode, newsletter, blog filters
 */

document.addEventListener('DOMContentLoaded', () => {

  // ─── Theme Toggle ───
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    // Load saved theme
    const savedTheme = localStorage.getItem('curata-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    // Update icon based on current theme
    const updateThemeIcon = (theme) => {
      const sunIcon = themeToggle.querySelector('.sun');
      if (!sunIcon) return;
      if (theme === 'dark') {
        sunIcon.innerHTML = `<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>`;
      } else {
        sunIcon.innerHTML = `<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>`;
      }
    };
    updateThemeIcon(savedTheme);

    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('curata-theme', next);
      updateThemeIcon(next);
    });
  }

  // ─── Mobile Menu ───
  const menuToggle = document.getElementById('menuToggle');
  const navLinks = document.getElementById('navLinks');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      menuToggle.setAttribute('aria-label',
        navLinks.classList.contains('open') ? '关闭菜单' : '打开菜单'
      );
    });

    // Close menu on link click
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
        menuToggle.setAttribute('aria-label', '打开菜单');
      });
    });

    // Close menu on outside click
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.site-header')) {
        navLinks.classList.remove('open');
        menuToggle.setAttribute('aria-label', '打开菜单');
      }
    });
  }

  // ─── Newsletter Form ───
  const newsletterForm = document.getElementById('newsletterForm');
  if (newsletterForm) {
    newsletterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const email = newsletterForm.querySelector('input[type="email"]');
      if (!email.value || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        email.style.borderColor = '#d45a5a';
        email.focus();
        return;
      }
      email.style.borderColor = '';
      const btn = newsletterForm.querySelector('.btn');
      const originalText = btn.textContent;
      btn.textContent = '订阅成功 ✓';
      btn.style.background = '#4a9e5a';
      email.value = '';

      setTimeout(() => {
        btn.textContent = originalText;
        btn.style.background = '';
      }, 3000);
    });
  }

  // ─── Blog Filters ───
  const filterBtns = document.querySelectorAll('.filter-btn');
  const blogList = document.getElementById('blogList');

  if (filterBtns.length && blogList) {
    const posts = blogList.querySelectorAll('.post-card');

    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.dataset.filter;

        posts.forEach(post => {
          if (filter === 'all') {
            post.style.display = '';
            return;
          }
          if (post.dataset.category === filter) {
            post.style.display = '';
          } else {
            post.style.display = 'none';
          }
        });
      });
    });
  }

  // ─── Blog Search ───
  const searchInput = document.querySelector('.blog-search input');
  if (searchInput && blogList) {
    searchInput.addEventListener('input', () => {
      const query = searchInput.value.toLowerCase().trim();
      const posts = blogList.querySelectorAll('.post-card');

      posts.forEach(post => {
        const title = post.querySelector('.post-card-title')?.textContent?.toLowerCase() || '';
        const excerpt = post.querySelector('.post-card-excerpt')?.textContent?.toLowerCase() || '';

        if (!query || title.includes(query) || excerpt.includes(query)) {
          post.style.display = '';
        } else {
          post.style.display = 'none';
        }
      });
    });
  }

  // ─── Scroll Reveal Animations ───
  const revealElements = document.querySelectorAll('.reveal');
  if (revealElements.length > 0) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    revealElements.forEach(el => revealObserver.observe(el));
  }

  // ─── Pick cards hover subtle effect ───
  document.querySelectorAll('.pick-card, .recommend-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transition = 'transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.35s ease';
    });
  });

  // ─── Smooth scroll for anchor links ───
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const href = anchor.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

});
