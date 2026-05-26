"""
Daily article generator for Curata.
- Uses AI API (Anthropic) if ANTHROPIC_API_KEY env var is set
- Falls back to pre-written article templates
- Generates HTML, updates blog listing, updates sitemap
"""

import os
import json
import re
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date
from html import escape

BASE_DIR = Path(__file__).resolve().parent.parent
BLOG_DIR = BASE_DIR / "blog"
IMAGES_DIR = BASE_DIR / "images"
SITEMAP = BASE_DIR / "sitemap.xml"
BLOG_INDEX = BLOG_DIR / "index.html"

# ── Article Templates ──────────────────────────────────────────
# Each template has: id, category, title, description, body_html, products, image_seed
# body_html uses Python format strings: {title}, {description}

TEMPLATES = [
    {
        "id": "portable-speaker",
        "category": "数码科技",
        "category_en": "tech",
        "title": "便携蓝牙音箱推荐：2026 年户外好声音",
        "description": "JBL、Marshall、Bose、Sonos 四品牌主流便携音箱横评。音质、续航、防水、便携性全维度对比。",
        "image_seed": "speaker",
        "products": [
            ("JBL Charge 5", "¥1,299", "编辑推荐", "JBL+Charge+5+%E8%93%9D%E7%89%99%E9%9F%B3%E7%AE%B1"),
            ("Marshall Emberton II", "¥1,499", "颜值之选", "Marshall+Emberton+II+%E9%9F%B3%E7%AE%B1"),
            ("Bose SoundLink Flex", "¥1,199", "户外首选", "Bose+SoundLink+Flex+%E8%93%9D%E7%89%99%E9%9F%B3%E7%AE%B1"),
        ],
    },
    {
        "id": "air-purifier-guide",
        "category": "生活好物",
        "category_en": "life",
        "title": "空气净化器选购指南：2026 年家用推荐",
        "description": "CADR、CCM、滤芯类型一次看懂。小米、IQAir、戴森、Blueair 四大品牌横评。",
        "image_seed": "purifier",
        "products": [
            ("小米空气净化器 4 Pro", "¥889", "性价比之选", "%E7%B1%B3%E5%AE%B6%E7%A9%BA%E6%B0%94%E5%87%80%E5%8C%96%E5%99%A8+4+Pro"),
            ("IQAir HealthPro 250", "¥7,999", "旗舰之选", "IQAir+HealthPro+250+%E7%A9%BA%E6%B0%94%E5%87%80%E5%8C%96%E5%99%A8"),
            ("Blueair 411", "¥1,499", "入门推荐", "Blueair+411+%E7%A9%BA%E6%B0%94%E5%87%80%E5%8C%96%E5%99%A8"),
        ],
    },
    {
        "id": "smartwatch-guide",
        "category": "数码科技",
        "category_en": "tech",
        "title": "智能手表怎么选？Apple Watch、佳明、小米对比",
        "description": "运动、健康、续航、生态全方位对比。帮你找到最适合自己生活方式的那一块手表。",
        "image_seed": "watch",
        "products": [
            ("Apple Watch Series 10", "¥3,199", "iPhone 首选", "Apple+Watch+Series+10+%E6%99%BA%E8%83%BD%E6%89%8B%E8%A1%A8"),
            ("佳明 Forerunner 265", "¥2,480", "运动之选", "%E4%BD%B3%E6%98%8E+Forerunner+265+%E8%BF%90%E5%8A%A8%E6%89%8B%E8%A1%A8"),
            ("小米 Watch S4", "¥999", "性价比之选", "%E5%B0%8F%E7%B1%B3+Watch+S4+%E6%99%BA%E8%83%BD%E6%89%8B%E8%A1%A8"),
        ],
    },
    {
        "id": "desk-lamp",
        "category": "生活好物",
        "category_en": "life",
        "title": "护眼台灯横评：2026 年哪款最值得买？",
        "description": "BenQ、小米、欧普、松下四品牌护眼台灯实测。照度、显色、频闪、蓝光全维度对比。",
        "image_seed": "lamp",
        "products": [
            ("BenQ ScreenBar Pro", "¥1,299", "编辑推荐", "BenQ+ScreenBar+Pro+%E6%88%B4%E5%AD%97%E5%8F%B0%E7%81%AF"),
            ("米家台灯 Pro", "¥249", "性价比之选", "%E7%B1%B3%E5%AE%B6%E5%8F%B0%E7%81%AF+Pro+%E6%8A%A4%E7%9C%BC"),
            ("松下致飒 HHLT-0633", "¥599", "品质之选", "%E6%9D%BE%E4%B8%8B%E8%87%B4%E9%A3%92+%E6%8A%A4%E7%9C%BC%E5%8F%B0%E7%81%AF"),
        ],
    },
    {
        "id": "water-flosser",
        "category": "生活好物",
        "category_en": "life",
        "title": "冲牙器推荐：2026 年 6 款主流冲牙器实测",
        "description": "洁碧、飞利浦、小米、松下冲牙器横评。水压、续航、使用体验全方位对比。",
        "image_seed": "flosser",
        "products": [
            ("洁碧 Waterpik WP-660", "¥599", "编辑推荐", "%E6%B4%81%E7%A2%A7+Waterpik+WP-660+%E5%86%B2%E7%89%99%E5%99%A8"),
            ("飞利浦 Sonicare AirFloss", "¥399", "便携之选", "%E9%A3%9E%E5%88%A9%E6%B5%A6+Sonicare+AirFloss+%E5%86%B2%E7%89%99%E5%99%A8"),
            ("米家冲牙器", "¥149", "入门首选", "%E7%B1%B3%E5%AE%B6+%E5%86%B2%E7%89%99%E5%99%A8+%E6%8C%81%E7%BB%AD%E5%96%B7%E5%B0%84"),
        ],
    },
    {
        "id": "monitor-guide",
        "category": "数码科技",
        "category_en": "tech",
        "title": "2026 年显示器选购指南：办公、设计、游戏怎么选",
        "description": "4K、高刷、OLED、MiniLED 一次看懂。戴尔、LG、华硕、小米四品牌横评。",
        "image_seed": "monitor",
        "products": [
            ("Dell U2724D", "¥3,499", "办公首选", "Dell+U2724D+27%E5%AF%B8+4K+%E6%98%BE%E7%A4%BA%E5%99%A8"),
            ("LG 27GP95R", "¥3,999", "游戏之选", "LG+27GP95R+4K+%E9%AB%98%E5%88%B7+%E6%98%BE%E7%A4%BA%E5%99%A8"),
            ("小米 27 寸 4K", "¥1,999", "性价比之选", "%E5%B0%8F%E7%B1%B3+27%E5%AF%B8+4K+%E6%98%BE%E7%A4%BA%E5%99%A8"),
        ],
    },
    {
        "id": "winter-jacket",
        "category": "旅行装备",
        "category_en": "travel",
        "title": "冲锋衣选购指南：始祖鸟、北面、凯乐石横评",
        "description": "GTX、防风、保暖、透气全维度对比。户外运动爱好者的终极装备指南。",
        "image_seed": "jacket",
        "products": [
            ("始祖鸟 Alpha SV", "¥7,999", "旗舰之选", "%E5%A7%8B%E7%A5%96%E9%B8%9F+Alpha+SV+%E5%86%B2%E9%94%8B%E8%A1%A3"),
            ("北面 1996 Retro Nuptse", "¥2,599", "经典款", "%E5%8C%97%E9%9D%A2+1996+Retro+Nuptse+%E7%BE%BD%E7%BB%92%E6%9C%8D"),
            ("凯乐石 Mont-X", "¥1,999", "国产精品", "%E5%87%AF%E4%B9%90%E7%9F%B3+Mont-X+%E5%86%B2%E9%94%8B%E8%A1%A3"),
        ],
    },
]

# ── Helper: pick next template ─────────────────────────────────
STATE_FILE = BASE_DIR / "scripts" / ".generator_state.json"

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"index": 0, "used": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def pick_template():
    state = load_state()
    # Cycle through templates
    idx = state["index"] % len(TEMPLATES)
    template = TEMPLATES[idx]
    state["index"] += 1
    state["used"].append(template["id"])
    save_state(state)
    return template

# ── AI Content Generation ──────────────────────────────────────
def call_ai_api(prompt):
    """Use Anthropic API if key is available."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    import urllib.request
    import json

    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except Exception as e:
        print(f"AI API call failed: {e}")
        return None

def generate_with_ai(template):
    """Generate article body using AI."""
    prompt = f"""
    你是一个中文评测博主，为 Curata 网站写一篇产品评测文章。
    要求：
    - 标题：{template['title']}
    - 分类：{template['category']}
    - 文章长度：800-1200 字
    - 风格：第一人称真实体验，诚实、有洞察力
    - 结构：开头引入 → 2-3 个核心卖点或对比 → 缺点 → 购买建议 → 总结
    - 不要用 markdown，返回纯 HTML（用 <p> <h2> <ul> <li> <strong> 等标签）
    - 文中要植入 affiliate 链接，用以下格式：
      <a href="https://mobile.yangkeduo.com/search_result.html?search_key=KEYWORD" rel="sponsored">产品名</a>
    """
    return call_ai_api(prompt)

# ── Template-based generation ──────────────────────────────────
def generate_template_body(template):
    """Generate article body from template."""
    p = template["products"]
    name1, price1, tag1, kw1 = p[0]
    name2, price2, tag2, kw2 = p[1]
    name3, price3, tag3, kw3 = p[2]

    bodies = {
        "portable-speaker": f"""
<p>夏天到了，又到了带着音箱去户外撒野的季节。我花了三周时间，把市面上主流的便携蓝牙音箱都试了一遍——从公园野餐到海边派对，从露营到骑行，模拟了所有我真实会用到音箱的场景。</p>
<p>先说结论：<strong>没有完美的音箱，但一定有最适合你的那一款。</strong>下面的推荐按使用场景划分，对号入座就好。</p>

<h2>JBL Charge 5：全能选手</h2>
<p>JBL Charge 5 是这个品类里的「标准答案」。IP67 防水防尘（掉水里捞出来照样响）、20 小时续航、低音在这个体积下令人惊讶地好。还能当充电宝给手机应急充电——这个功能在户外真的救过我的命。</p>
<p>缺点就是 1.2kg 不算轻，挂在背包上能感觉到重量。音质方面中高频一般，听人声够用，听古典乐就别指望了。</p>

<h2>Marshall Emberton II：颜值即正义</h2>
<p>承认吧，大部分人买 Marshall 就是冲那个外观去的——经典的黑金配色、皮革纹理、标志性的 Marshall logo。摆在桌上本身就是一件装饰品。音质偏摇滚调音，中频饱满，听人声和吉他非常舒服。</p>
<p>防水只有 IPX4（防泼溅），不能泡水。而且 20W 的功率在户外开阔空间略显不足。适合主要在室内用、偶尔带去阳台或庭院的人。</p>

<h2>Bose SoundLink Flex：技术流的选择</h2>
<p>Bose 在这台小音箱里塞进了他们独家的 PositionIQ 技术——不管你怎么摆，它都能自动优化音质，让它「听起来是正对着你的」。实际体验确实神奇，放在地上、挂包里、倒着放，声音都一样好。低频量感在同类产品里数一数二。</p>
<p>缺点是用 Bose 专用的充电线（不是 Type-C），出门多带一根线挺烦的。</p>

<h2>总结推荐</h2>
<ul style="margin-bottom:var(--space-lg);padding-left:var(--space-lg);color:var(--text-soft);line-height:2;">
<li><strong>全能户外</strong> — JBL Charge 5 ¥1,299（防水+长续航+充电宝）</li>
<li><strong>颜值优先</strong> — Marshall Emberton II ¥1,499（好看+人声好）</li>
<li><strong>技术流</strong> — Bose SoundLink Flex ¥1,199（音质最优）</li>
</ul>
""",
        "air-purifier-guide": f"""
<p>在北京住了这么多年，每年换季的时候鼻炎必犯。以前以为是体质问题，后来才发现——很多症状其实是室内空气质量引起的。</p>
<p>空气净化器这个东西，买之前觉得「有必要吗」，买之后「为什么不早点买」。这次我整理了四个价位段最值得买的净化器，<strong>不踩坑、不交税</strong>。</p>

<h2>看懂三个参数再选</h2>
<p><strong>CADR 值</strong>决定了净化速度。30 平米的房间选 300m³/h 以上的就够了。CADR 越高，净化越快，但噪音也越大。<strong>CCM 值</strong>看滤芯寿命，选 P4（颗粒物）和 F4（甲醛）最高等级准没错。<strong>滤芯成本</strong>是长期投入，有些机器便宜但滤芯半年一换，两年下来总成本比买贵的还多。</p>

<h2>小米空气净化器 4 Pro：千元级标杆</h2>
<p>颗粒物 CADR 500m³/h，甲醛 CADR 200m³/h。对于 30-50 平米的房间绰绰有余。睡眠档 32dB 几乎无声，米家生态联动很方便——配合温湿度计自动开关、离家自动关闭。滤芯 ¥149 一年一换，使用成本极低。</p>
<p>缺点是做工一般，塑料外壳质感不高级。而且没有甲醛传感器，除甲醛效果只能靠算。</p>

<h2>总结</h2>
<ul style="margin-bottom:var(--space-lg);padding-left:var(--space-lg);color:var(--text-soft);line-height:2;">
<li><strong>预算有限</strong> — 小米空气净化器 4 Pro ¥889（性价比无敌）</li>
<li><strong>品质首选</strong> — Blueair 411 ¥1,499（静音+好看+够用）</li>
<li><strong>一步到位</strong> — IQAir HealthPro 250 ¥7,999（十年不换机）</li>
</ul>
""",
        "smartwatch-guide": f"""
<p>从最早的 Pebble 开始，我戴智能手表已经快十年了。这十年里智能手表从「极客玩具」变成了「健康刚需」。</p>
<p>但市面上选择太多了——Apple Watch、佳明、小米、华为……价格从几百到几千，到底有什么区别？这篇文章帮你理清楚。</p>

<h2>Apple Watch Series 10：iPhone 用户的首选</h2>
<p>如果你用 iPhone，Apple Watch 是体验最好的选择——没有之一。消息通知、接电话、解锁 Mac、查找手机，这些「无缝衔接」的小事累积起来，就是每天省下的大量时间和精力。</p>
<p>Series 10 比上一代更薄、屏幕更大，新增了睡眠呼吸暂停检测和电量显示。续航 18 小时（一天一充），快充 30 分钟充到 80%。</p>
<p>缺点很明显：续航撑不过两天。如果你经常出差或户外活动，还得带着充电器。</p>

<h2>佳明 Forerunner 265：运动爱好者的最爱</h2>
<p>Forerunner 265 是佳明最值得买的跑表。AMOLED 屏幕终于跟上时代了，GPS 定位秒连、心率监测准确、运动数据分析极其详细。续航 13 天（智能模式）</p>
<p>佳明的生态是另一个核心优势——Garmin Coach 训练计划、Body Battery 体能状态、训练准备程度……对这些数据和量化训练有追求的人，佳明是唯一的选择。</p>
<p>缺点是屏幕在强光下不如老款 MIP 屏清晰，而且日常通知功能比 Apple Watch 差不少。</p>

<h2>总结</h2>
<ul style="margin-bottom:var(--space-lg);padding-left:var(--space-lg);color:var(--text-soft);line-height:2;">
<li><strong>iPhone 用户</strong> — Apple Watch Series 10 ¥3,199（体验最完整）</li>
<li><strong>运动爱好者</strong> — 佳明 Forerunner 265 ¥2,480（数据最专业）</li>
<li><strong>安卓/性价比</strong> — 小米 Watch S4 ¥999（够用不贵）</li>
</ul>
""",
        "desk-lamp": f"""
<p>每天在电脑前坐 8-10 个小时，灯光对于工作效率和眼睛健康的影响远超我的想象。以前我用的是淘宝几十块的台灯，换了 BenQ ScreenBar 之后才发现——原来光线是可以「没有存在感」的。</p>
<p>这次我找了市面上四款主流护眼台灯，每款至少用了一周，以下是真实体验。</p>

<h2>BenQ ScreenBar Pro：屏幕挂灯的天花板</h2>
<p>ScreenBar Pro 的核心理念是「不占桌面空间、不照屏幕反光」。挂在显示器上，光线只照亮桌面区域，不会照到屏幕上造成反光，也不会直射眼睛。</p>
<p>自动调光功能很实用——通过环境光传感器自动调节亮度和色温。新一代 Pro 版亮度比上一代提升了 50%，照亮 1.2 米宽的桌面完全够用。Ra > 95 的高显色指数，看东西颜色很正。</p>
<p>缺点就是贵，¥1,299 一个灯确实需要心理建设。而且只适合配显示器用，没有显示器的话用不了。</p>

<h2>米家台灯 Pro：性价比神灯</h2>
<p>¥249 的价格，给到了 Ra 95 显色、无频闪、无蓝光危害、App 控制、小爱同学语音控制。虽然做工和光照均匀度不如 BenQ，但对大多数人来说完全够用了。适合学生党、租房党。</p>

<h2>总结</h2>
<ul style="margin-bottom:var(--space-lg);padding-left:var(--space-lg);color:var(--text-soft);line-height:2;">
<li><strong>桌面极简</strong> — BenQ ScreenBar Pro ¥1,299（不占空间+自动调光）</li>
<li><strong>传统台灯</strong> — 松下致飒 HHLT-0633 ¥599（品质稳定）</li>
<li><strong>预算有限</strong> — 米家台灯 Pro ¥249（够用）</li>
</ul>
""",
        "water-flosser": f"""
<p>牙医第三次建议我用冲牙器的时候，我终于认真考虑了。然后我发现一个问题：市面上的冲牙器从一百到一千，参数看起来都差不多，到底有什么区别？</p>
<p>我用了两个月时间，把主流品牌的冲牙器都试了一遍。答案是：<strong>区别非常大，而且越贵的确实越好——但贵的边际效益递减很快。</strong></p>

<h2>洁碧 Waterpik WP-660：行业标杆</h2>
<p>洁碧是冲牙器的发明者，WP-660 是全球销量最高的家用冲牙器。10 档水压调节、1.2L 大水箱、7 种喷头满足不同需求。水压开到 5 档以上就能感受到脉冲水流的强力清洁效果——牙缝里的食物残渣冲得干干净净。</p>
<p>缺点：大、占地方、噪音不小。出差没法带。而且水箱底部容易积水垢，需要定期清洁。</p>

<h2>飞利浦 Sonicare AirFloss：便携派的胜利</h2>
<p>AirFloss 的思路和传统冲牙器完全不同——它不是用水柱冲洗，而是用「微爆气流」+ 水滴的方式清洁牙缝。优点是极其便携（比电动牙刷还小），操作快（一次加水够用全口），噪音小。适合出差党和办公室午饭后使用。</p>
<p>缺点是清洁力不如传统冲牙器。如果你牙缝紧、牙齿整齐，AirFloss 够用了。但如果你的牙缝比较大或者有牙周问题，还是推荐洁碧的经典款。</p>

<h2>总结</h2>
<ul style="margin-bottom:var(--space-lg);padding-left:var(--space-lg);color:var(--text-soft);line-height:2;">
<li><strong>居家首选</strong> — 洁碧 Waterpik WP-660 ¥599（清洁力最强）</li>
<li><strong>便携出差</strong> — 飞利浦 Sonicare AirFloss ¥399（小巧快捷）</li>
<li><strong>入门体验</strong> — 米家冲牙器 ¥149（够用不贵）</li>
</ul>
""",
        "monitor-guide": f"""
<p>显示器是我们每天面对时间最长的电子设备——比手机、比电脑本身都长。但很多人愿意花两万买电脑，却在显示器上省钱。这其实搞反了：<strong>你每天看到的「画面」，是由显示器决定的。</strong></p>
<p>这篇指南帮你搞清楚 2026 年买显示器的核心要点，按预算推荐。</p>

<h2>办公首选：Dell U2724D</h2>
<p>Dell UltraSharp 系列是办公显示器的代名词。U2724D 采用 IPS Black 技术，对比度从常规 IPS 的 1000:1 提升到 2000:1，黑色更深邃、色彩更通透。27 寸 4K 分辨率，文字显示极其锐利。</p>
<p>出厂校色 Delta E < 2，开箱即用不需要自己调色。Type-C 接口支持 90W 反向充电，一根线连笔记本搞定视频信号+充电。做工优秀，三年质保上门换新。</p>

<h2>游戏之选：LG 27GP95R</h2>
<p>LG 的 Nano IPS 面板是 4K 高刷显示器的标杆。27 寸 4K + 160Hz 超频刷新率 + 1ms 响应时间，HDR600 认证。色彩覆盖 DCI-P3 98%——不管是 3A 大作还是看 HDR 电影，效果都非常震撼。</p>

<h2>总结</h2>
<ul style="margin-bottom:var(--space-lg);padding-left:var(--space-lg);color:var(--text-soft);line-height:2;">
<li><strong>办公/设计</strong> — Dell U2724D ¥3,499（色彩准+Type-C 充电）</li>
<li><strong>游戏/娱乐</strong> — LG 27GP95R ¥3,999（4K 160Hz 色彩好）</li>
<li><strong>预算之选</strong> — 小米 27 寸 4K ¥1,999（够用）</li>
</ul>
""",
        "winter-jacket": f"""
<p>两三年前我爬了一次四姑娘山，穿着一件普通的棉服上去，到半山腰就被风吹透了。下山第一件事：买一件正经的冲锋衣。</p>
<p>之后我前前后后买了七八件冲锋衣，从几百到上万都试过。这篇文章分享我的一些经验和推荐。</p>

<h2>始祖鸟 Alpha SV：硬壳天花板</h2>
<p>Alpha SV 是始祖鸟最经典的硬壳冲锋衣，Gore-Tex Pro 面料，N80p-X 级耐磨。这么说吧：如果你只买一件冲锋衣且预算充足，买 Alpha SV 不会后悔。它能在最恶劣的天气里保护你，而且一件穿十年质量依然没问题。</p>
<p>但说实话，对 90% 的人来说是性能过剩的。¥7,999 的价格不是小数目，除非你经常去高海拔、恶劣天气的户外环境，否则没必要上这个级别。</p>

<h2>凯乐石 Mont-X：国产骄傲</h2>
<p>中国的户外品牌这些年进步很大，凯乐石的 Mont-X 是代表作之一。采用了和 Gore-Tex 类似的ePTFE 面料技术，防水透气性能不输国际大牌。版型更适合亚洲人体型——肩宽、袖长、衣长都更合身。</p>
<p>¥1,999 的价格，能买到这个级别的防水透气性能，性价比确实高。</p>

<h2>总结</h2>
<ul style="margin-bottom:var(--space-lg);padding-left:var(--space-lg);color:var(--text-soft);line-height:2;">
<li><strong>专业户外</strong> — 始祖鸟 Alpha SV ¥7,999（最强防护）</li>
<li><strong>日常+轻户外</strong> — 凯乐石 Mont-X ¥1,999（国货精品）</li>
<li><strong>保暖休闲</strong> — 北面 1996 ¥2,599（经典不过时）</li>
</ul>
""",
    }

    return bodies.get(template["id"], "")

# ── HTML Generation ────────────────────────────────────────────
def make_platform_buttons(keyword):
    """Generate multi-platform buy buttons for a product keyword."""
    buttons = []

    # Pinduoduo (always enabled)
    pdd_url = f"https://mobile.yangkeduo.com/search_result.html?search_key={keyword}"
    buttons.append(f'<a href="{pdd_url}" class="post-pick-btn post-pick-btn-pdd" rel="sponsored" target="_blank">拼多多</a>')

    # Taobao
    tb_url = f"https://s.taobao.com/search?q={keyword}"
    buttons.append(f'<a href="{tb_url}" class="post-pick-btn post-pick-btn-taobao" rel="sponsored" target="_blank">淘宝</a>')

    # Jingdong
    jd_url = f"https://search.jd.com/Search?keyword={keyword}"
    buttons.append(f'<a href="{jd_url}" class="post-pick-btn post-pick-btn-jd" rel="sponsored" target="_blank">京东</a>')

    return f'<div class="post-pick-actions">{"".join(buttons)}</div>'


def make_article_html(template, body_html, today):
    """Generate full article HTML page."""
    slug = template["id"]
    title = escape(template["title"])
    desc = escape(template["description"])
    cat = template["category"]

    hero_img = f"../images/{slug}-hero.jpg"
    products_html = ""
    for name, price, tag, kw in template["products"]:
        platform_btns = make_platform_buttons(kw)
        products_html += f'''
          <a href="https://mobile.yangkeduo.com/search_result.html?search_key={kw}" class="post-pick-card" rel="sponsored">
            <span class="post-pick-name">{name}</span>
            <span class="post-pick-tag">{tag}</span>
            <span class="post-pick-price">{price}</span>
            <span class="post-pick-link">查看价格 &rarr;</span>
            {platform_btns}
          </a>'''

    return f'''<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Curata</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title} — Curata">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://curata-green.vercel.app/blog/{slug}.html">
<meta property="og:site_name" content="Curata">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../css/style.css">
<link rel="icon" type="image/svg+xml" href="../data:image/svg+xml,%3Csvg viewBox='0 0 32 32' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='16' cy='16' r='14' fill='%23c17f3b'/%3E%3Cpath d='M10 16l4 4 8-8' stroke='white' stroke-width='2.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<!-- Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QC390JPYTQ"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', 'G-QC390JPYTQ');
</script>
<script>
var _hmt = _hmt || [];
(function() {{
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?c165cd4594a273315b3e2d69cdacdd55";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
}})();
</script>
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{desc}",
  "author": {{"@type": "Organization", "name": "Curata"}}
}}</script>
</head>
<body>
<a href="#main" class="skip-link">跳转到主要内容</a>
<header class="site-header" role="banner">
  <div class="container">
    <a href="../index.html" class="logo"><span class="logo-dot"></span>Curata</a>
    <button class="menu-toggle" id="menuToggle" aria-label="打开菜单"><span></span><span></span><span></span></button>
    <nav class="nav-links" id="navLinks" role="navigation" aria-label="主导航">
      <a href="../index.html">首页</a><a href="index.html">文章</a><a href="../recommends.html">精选推荐</a><a href="../about.html">关于</a>
      <button class="theme-toggle" id="themeToggle" aria-label="切换主题"><svg class="sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg></button>
      <a href="../newsletter.html" class="nav-cta"><span>订阅</span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
    </nav>
  </div>
  <div class="reading-progress"><div class="reading-progress-bar" id="readingProgress"></div></div>
</header>
<main id="main">
<article class="post-article">
  <div class="container">
    <header class="post-header">
      <span class="post-category">{cat}</span>
      <h1>{title}</h1>
      <div class="post-meta">
        <span>{today}</span><span class="dot"></span><span>6 分钟阅读</span><span class="dot"></span>
        <span class="disclosure-badge">含联盟链接</span>
      </div>
    </header>
    <div class="post-featured-image"><img src="{hero_img}" alt="{title}" style="width:100%;height:100%;object-fit:cover;border-radius:var(--radius-lg);">
    </div>
    <div class="post-content">
      {body_html}
      <div class="post-picks">
        <h3>推荐产品</h3>
        <div class="post-picks-grid">{products_html}
        </div>
      </div>
      <div class="affiliate-disclosure">
        <strong>&#9432; 利益声明</strong><br>本文中的部分商品链接为联盟营销链接。
      </div>
    </div>
  </div>
</article>
<section class="newsletter-section">
  <div class="container">
    <div class="newsletter-card">
      <h2>每周精选，直达邮箱</h2>
      <p>订阅后每周收到深度评测 × 好物推荐。</p>
      <form class="newsletter-form" action="#" method="post">
        <input type="email" placeholder="输入你的邮箱" required aria-label="邮箱地址">
        <button type="submit" class="btn btn-primary">免费订阅</button>
      </form>
    </div>
  </div>
</section>
</main>
<footer class="site-footer" role="contentinfo">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="../index.html" class="logo"><span class="logo-dot"></span>Curata</a>
        <p>精选推荐，品质生活。</p>
      </div>
      <div class="footer-col">
        <h4>探索</h4>
        <ul><li><a href="index.html">文章</a></li><li><a href="../recommends.html">精选推荐</a></li><li><a href="../about.html">关于我们</a></li></ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; 2026 Curata.</span>
      <span class="disclosure-badge">部分链接为联盟营销</span>
    </div>
  </div>
</footer>
<script src="../js/main.js"></script>
</body>
</html>'''


# ── Blog Index Update ──────────────────────────────────────────
def update_blog_index(template, today):
    """Insert new article card at top of blog list."""
    slug = template["id"]
    title = escape(template["title"])
    desc = escape(template["description"])
    cat_en = template["category_en"]

    new_card = f'''      <article class="post-card" data-category="{cat_en}">
        <div class="post-card-image">
          <img src="../images/{slug}-thumb.jpg" alt="{title}" style="width:100%;height:100%;object-fit:cover;transition:transform 0.6s var(--ease);" loading="lazy">
          <span class="post-card-category">{template["category"]}</span>
        </div>
        <div class="post-card-body">
          <div class="post-card-meta"><span>{today}</span><span class="dot"></span><span>6 分钟</span></div>
          <h3 class="post-card-title"><a href="{slug}.html">{title}</a></h3>
          <p class="post-card-excerpt">{desc}</p>
        </div>
      </article>'''

    with open(BLOG_INDEX, encoding="utf-8") as f:
        html = f.read()

    # Insert after blog-list opening
    html = html.replace(
        '<div class="blog-list" id="blogList">',
        f'<div class="blog-list" id="blogList">\n{new_card}',
        1
    )

    with open(BLOG_INDEX, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Updated blog/index.html with new card")


# ── Sitemap Update ─────────────────────────────────────────────
def update_sitemap(slug, today):
    """Add new URL to sitemap."""
    new_url = f'''
  <url>
    <loc>https://curata-green.vercel.app/blog/{slug}.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>'''

    with open(SITEMAP, encoding="utf-8") as f:
        xml = f.read()

    xml = xml.replace('</urlset>', f'{new_url}\n</urlset>')

    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"  Updated sitemap.xml")


# ── Main ────────────────────────────────────────────────────────
def main():
    print("=== Curata Daily Article Generator ===\n")

    template = pick_template()
    slug = template["id"]
    today = date.today().isoformat()

    print(f"  Template: {template['title']} ({template['id']})")

    # Check if already generated today
    article_path = BLOG_DIR / f"{slug}.html"
    if article_path.exists():
        print(f"  SKIP: {slug}.html already exists")
        return

    # Generate body
    body = generate_with_ai(template)
    if not body:
        print("  Using template-based content")
        body = generate_template_body(template)

    if not body:
        print("  ERROR: No content generated!")
        return

    # Generate article HTML
    article_html = make_article_html(template, body, today)
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(article_html)
    print(f"  Created blog/{slug}.html")

    # Update blog index
    update_blog_index(template, today)

    # Update sitemap
    update_sitemap(slug, today)

    print(f"\n=== Done! Article published: {template['title']} ===")


if __name__ == "__main__":
    main()
