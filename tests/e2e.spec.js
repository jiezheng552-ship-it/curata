const { test, expect } = require('@playwright/test');

// ─── Page rendering ───

test.describe('Page rendering', () => {
  const pages = [
    { path: '/', title: /Curata.*精选推荐/ },
    { path: '/about.html', title: '关于 Curata' },
    { path: '/recommends.html', title: /精选推荐.*Curata/ },
    { path: '/blog/index.html', title: /文章.*Curata/ },
  ];

  for (const { path, title } of pages) {
    test(`loads ${path} with correct title`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveTitle(title);
    });
  }

  test('homepage has SEO meta description', async ({ page }) => {
    await page.goto('/');
    const meta = page.locator('meta[name="description"]');
    await expect(meta).toHaveAttribute('content', /Curata/);
  });

  test('all pages have skip-link', async ({ page }) => {
    await page.goto('/');
    const skip = page.locator('.skip-link');
    await expect(skip).toHaveText('跳转到主要内容');
  });
});

// ─── Navigation ───

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('header logo links to homepage', async ({ page }) => {
    await page.locator('.logo').first().click();
    await expect(page).toHaveURL('/');
  });

  test('nav links point to correct pages', async ({ page }) => {
    const links = [
      { text: '首页', href: 'index.html' },
      { text: '文章', href: 'blog/index.html' },
      { text: '精选推荐', href: 'recommends.html' },
      { text: '关于', href: 'about.html' },
    ];

    for (const { text, href } of links) {
      const link = page.locator('.nav-links a', { hasText: text });
      await expect(link).toHaveAttribute('href', href);
    }
  });
});

test.describe('Mobile menu', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
  });

  test('toggle opens and closes menu', async ({ page }) => {
    const nav = page.locator('#navLinks');

    await page.evaluate(() => {
      document.getElementById('menuToggle').click();
    });
    await expect(nav).toHaveClass(/open/);
    await expect(page.locator('#menuToggle')).toHaveAttribute('aria-label', '关闭菜单');

    await page.evaluate(() => {
      document.getElementById('menuToggle').click();
    });
    await expect(nav).not.toHaveClass(/open/);
  });

  test('clicking nav link closes mobile menu', async ({ page }) => {
    const nav = page.locator('#navLinks');

    await page.evaluate(() => {
      document.getElementById('menuToggle').click();
    });
    await expect(nav).toHaveClass(/open/);

    await page.locator('.nav-links a', { hasText: '精选推荐' }).click();
    await expect(nav).not.toHaveClass(/open/);
    await expect(page).toHaveURL(/\/recommends/);
  });
});

// ─── Theme toggle ───

test.describe('Theme toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('default theme is light', async ({ page }) => {
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  });

  test('toggle switches to dark and persists', async ({ page }) => {
    await page.locator('#themeToggle').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    const theme = await page.evaluate(() => localStorage.getItem('curata-theme'));
    expect(theme).toBe('dark');
  });

  test('toggle switches back to light', async ({ page }) => {
    await page.locator('#themeToggle').click();
    await page.locator('#themeToggle').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  });

  test('theme persists across page navigation', async ({ page }) => {
    await page.locator('#themeToggle').click();
    await page.goto('/about.html');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  });
});

// ─── Newsletter form ───

test.describe('Newsletter form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('rejects empty email', async ({ page }) => {
    const emailInput = page.locator('#newsletterEmail');
    await page.locator('#newsletterForm .btn').click();
    await expect(emailInput).toBeFocused();
  });

  test('rejects invalid email and sets focus', async ({ page }) => {
    const emailInput = page.locator('#newsletterEmail');
    await emailInput.fill('not-an-email');
    await page.locator('#newsletterForm .btn').click();
    await expect(emailInput).toBeFocused();
  });

  test('accepts valid email and shows success', async ({ page }) => {
    const emailInput = page.locator('#newsletterEmail');
    await emailInput.fill('test@example.com');
    await page.locator('#newsletterForm .btn').click();

    const btn = page.locator('#newsletterForm .btn');
    await expect(btn).toHaveText('订阅成功 ✓');
    await expect(btn).toHaveCSS('background-color', /rgb\(74, 158, 90\)/);
  });

  test('newsletter form works on about page too', async ({ page }) => {
    await page.goto('/about.html');
    const emailInput = page.locator('#newsletterEmail');
    await emailInput.fill('user@test.com');
    await page.locator('#newsletterForm .btn').click();

    const btn = page.locator('#newsletterForm .btn');
    await expect(btn).toHaveText('订阅成功 ✓');
  });
});

// ─── Blog filters and search ───

test.describe('Blog page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blog/index.html');
  });

  test('all filter buttons exist', async ({ page }) => {
    const filters = ['全部', '数码科技', '生活好物', '阅读书单', '旅行装备'];
    for (const name of filters) {
      await expect(page.locator('.filter-btn', { hasText: name })).toBeVisible();
    }
  });

  test('filter by tech shows only tech posts', async ({ page }) => {
    await page.locator('.filter-btn[data-filter="tech"]').click();
    const visible = page.locator('.post-card:visible');
    const count = await visible.count();
    expect(count).toBeGreaterThan(0);

    const allTech = await visible.evaluateAll(cards =>
      cards.every(c => c.dataset.category === 'tech')
    );
    expect(allTech).toBe(true);
  });

  test('filter by life shows only life posts', async ({ page }) => {
    await page.locator('.filter-btn[data-filter="life"]').click();
    const visible = page.locator('.post-card:visible');
    const allLife = await visible.evaluateAll(cards =>
      cards.every(c => c.dataset.category === 'life')
    );
    expect(allLife).toBe(true);
  });

  test('"全部" shows all posts', async ({ page }) => {
    await page.locator('.filter-btn[data-filter="tech"]').click();
    await page.locator('.filter-btn[data-filter="all"]').click();
    const visible = page.locator('.post-card:visible');
    await expect(visible.first()).toBeVisible();
  });

  test('search filters posts by title', async ({ page }) => {
    const searchInput = page.locator('.blog-search input');
    await searchInput.fill('降噪耳机');
    await expect(page.locator('.post-card:visible').first()).toContainText('降噪耳机');
  });

  test('search filters posts by excerpt', async ({ page }) => {
    const searchInput = page.locator('.blog-search input');
    await searchInput.fill('历时两周');
    await expect(page.locator('.post-card:visible').first()).toContainText('降噪耳机');
  });

  test('search with no match hides all posts', async ({ page }) => {
    const searchInput = page.locator('.blog-search input');
    await searchInput.fill('zzzznonexistent');
    const visible = page.locator('.post-card:visible');
    await expect(visible).toHaveCount(0);
  });

  test('pagination is visible', async ({ page }) => {
    await expect(page.locator('.pagination')).toBeVisible();
  });
});

// ─── Footer ───

test.describe('Footer', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('footer has copyright', async ({ page }) => {
    await expect(page.locator('.footer-bottom')).toContainText('2026 Curata');
  });

  test('footer has disclosure badge', async ({ page }) => {
    await expect(page.locator('.disclosure-badge')).toBeVisible();
  });

  test('footer has navigation links', async ({ page }) => {
    const links = page.locator('.footer-grid a');
    const texts = await links.allTextContents();
    expect(texts.length).toBeGreaterThan(5);
  });
});

// ─── Responsive ───

test.describe('Responsive layout', () => {
  test('hero is visible on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await expect(page.locator('.hero h1')).toBeVisible();
  });
});
