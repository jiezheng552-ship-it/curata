"""
Batch update affiliate links in all articles.
Adds multi-platform buy buttons to product cards.
"""
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BLOG_DIR = BASE_DIR / "blog"
PRODUCTS_FILE = BASE_DIR / "_data" / "products.json"
AFFILIATE_CONFIG = BASE_DIR / "affiliate-config.json"
IMAGES_DIR = BASE_DIR / "images"

def load_products():
    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        return json.load(f)["products"]

def load_config():
    with open(AFFILIATE_CONFIG, encoding="utf-8") as f:
        return json.load(f)

def make_platform_buttons(product):
    """Generate multi-platform HTML buttons for a product."""
    buttons = []
    platforms = {
        "pinduoduo": ("拼多多", "post-pick-btn-pdd"),
        "taobao": ("淘宝", "post-pick-btn-taobao"),
        "jingdong": ("京东", "post-pick-btn-jd"),
    }

    for key, (label, css_class) in platforms.items():
        info = product.get(key, {})
        if info and info.get("enabled", False):
            keyword = info.get("keyword", "")
            if key == "pinduoduo":
                url = f"https://mobile.yangkeduo.com/search_result.html?search_key={keyword}"
            elif key == "taobao":
                url = f"https://s.taobao.com/search?q={keyword}"
            elif key == "jingdong":
                url = f"https://search.jd.com/Search?keyword={keyword}"
            buttons.append(
                f'<a href="{url}" class="post-pick-btn {css_class}" rel="sponsored" target="_blank">{label}</a>'
            )

    if buttons:
        return f'<div class="post-pick-actions">{"".join(buttons)}</div>'
    return ""

def update_article_picks(filepath, products):
    """Replace single link with multi-platform buttons in article product cards."""
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

    changes = 0
    for prod_key, prod_info in products.items():
        name = prod_info["name"]
        # Find existing link: 查看价格 or similar with yangkeduo
        old_pattern = re.compile(
            r'(<span class="post-pick-link">).*?(?:查看价格|→|&rarr;).*?(</span>)',
            re.DOTALL
        )

        def replace_link(match):
            nonlocal changes
            start = match.group(1)
            end = match.group(2)
            buttons = make_platform_buttons(prod_info)
            if not buttons:
                return match.group(0)
            changes += 1
            return f'{start}查看价格{end}\n{buttons}'

        html = old_pattern.sub(replace_link, html)

    # Also update recommendation page cards
    for prod_key, prod_info in products.items():
        name = prod_info["name"]
        old_pattern2 = re.compile(
            r'(<div class="recommend-footer">.*?<a href=")[^"]*(" class="btn btn-outline"[^>]*>查看价格</a>)',
            re.DOTALL
        )

        def replace_btn(match):
            nonlocal changes
            url_start = match.group(1)
            url_end = match.group(2)
            buttons = make_platform_buttons(prod_info)
            if not buttons:
                return match.group(0)
            changes += 1
            # Keep the original button but add platform buttons below
            return f'{match.group(0)}\n{buttons}'

        html = old_pattern2.sub(replace_btn, html)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return changes

def main():
    print("=== Affiliate Link Updater ===\n")
    products = load_products()
    print(f"Loaded {len(products)} products from products.json\n")

    # Update blog articles
    total_changes = 0
    for html_file in sorted(BLOG_DIR.glob("*.html")):
        if html_file.name == "index.html":
            continue
        try:
            c = update_article_picks(html_file, products)
            if c > 0:
                print(f"  Updated {html_file.name}: {c} changes")
            total_changes += c
        except Exception as e:
            print(f"  ERROR {html_file.name}: {e}")

    # Update recommends.html
    recommends = BASE_DIR / "recommends.html"
    if recommends.exists():
        try:
            c = update_article_picks(recommends, products)
            if c > 0:
                print(f"  Updated recommends.html: {c} changes")
            total_changes += c
        except Exception as e:
            print(f"  ERROR recommends.html: {e}")

    print(f"\n=== Done! {total_changes} total changes ===")

if __name__ == "__main__":
    main()
