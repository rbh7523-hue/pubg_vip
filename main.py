import os
import re
import json
import base64
import tempfile
import math
import datetime
import textwrap
import threading
import webbrowser

import requests

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex as hexc
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDIcon, MDLabel
from kivymd.uix.navigationdrawer import MDNavigationDrawer, MDNavigationLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

try:
    from kivymd.toast import toast
except Exception:
    toast = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def find_local_font(name):
    for folder in (os.path.join(BASE_DIR, "fonts"), BASE_DIR):
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return path
    return None


def write_embedded_font(filename, data_b64):
    for folder in (BASE_DIR, tempfile.gettempdir()):
        try:
            path = os.path.join(folder, filename)
            if not os.path.exists(path) or os.path.getsize(path) < 1000:
                with open(path, "wb") as fh:
                    fh.write(base64.b64decode(data_b64))
            return path
        except Exception:
            continue
    return None


try:
    import fontdata

    EMB_REG = write_embedded_font("vip_regular.ttf", fontdata.REG_B64)
    EMB_BOLD = write_embedded_font("vip_bold.ttf", fontdata.BOLD_B64)
except Exception:
    EMB_REG = None
    EMB_BOLD = None

FONT_AR = find_local_font("arabic.ttf")
FONT_AR_B = find_local_font("arabic_bold.ttf")
FONT_BRAND = find_local_font("brand.ttf")


def first_font(candidates, default="Roboto"):
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return default


AR_FONT = first_font([
    FONT_AR,
    EMB_REG,
    "/system/fonts/NotoNaskhArabic-Regular.ttf",
    "/system/fonts/NotoSansArabic-Regular.ttf",
    "/system/fonts/NotoNaskhArabicUI-Regular.ttf",
    "/system/fonts/DroidSansArabic.ttf",
])
AR_FONT_B = first_font([
    FONT_AR_B,
    EMB_BOLD,
    "/system/fonts/NotoNaskhArabic-Bold.ttf",
    "/system/fonts/NotoSansArabic-Bold.ttf",
    "/system/fonts/NotoNaskhArabicUI-Bold.ttf",
], AR_FONT)
BRAND_FONT = first_font([FONT_BRAND, EMB_BOLD], AR_FONT_B)

try:
    import assets as _assets
except Exception:
    _assets = None


def asset_path(name):
    if _assets is None or name not in _assets.IMGS:
        return None
    for folder in (BASE_DIR, tempfile.gettempdir()):
        try:
            path = os.path.join(folder, "vip_" + name)
            if not os.path.exists(path) or os.path.getsize(path) < 100:
                with open(path, "wb") as fh:
                    fh.write(base64.b64decode(_assets.IMGS[name]))
            return path
        except Exception:
            continue
    return None


BG = hexc("#0A0C11")
BAR = hexc("#10131B")
CARD = hexc("#151A24")
CARD2 = hexc("#1D2433")
GOLD = hexc("#E08A4B")
ORANGE = hexc("#E5B25D")
TEXT = hexc("#E9ECF3")
MUTED = hexc("#8E97AB")
GREEN = hexc("#3DDC84")
RED = hexc("#FF5C5C")

DEFAULT_DATA_URL = "https://raw.githubusercontent.com/rbh7523-hue/pubg_vip/main/data.json"
DEFAULT_DATA = {
    "version": 0,
    "updated": "",
    "sensitivity_codes": [],
    "redeem_codes": [],
    "upcoming": [],
    "leaks": [],
    "links": [],
}
REDEEM_URL = "https://www.pubgmobile.com/redeem"
AI_MODEL = "claude-haiku-4-5-20251001"
DEV_NAME = "Murtadha"
DEV_TAG = "(VIP)"
DEV_INSTAGRAM = "g.eh0v"  # اسم حساب انستغرام بدون @


def shape(line):
    if not line:
        return line
    if arabic_reshaper is None or get_display is None:
        return line
    try:
        return get_display(arabic_reshaper.reshape(line))
    except Exception:
        return line


def chars_per_line(size, pad=64):
    usable = max(Window.width - dp(pad), dp(160))
    return max(14, int(usable / (sp(size) * 0.52)))


def fmt(text, size=16, pad=80, width=None):
    width = width or chars_per_line(size, pad)
    out = []
    for para in str(text).split("\n"):
        if not para.strip():
            out.append("")
            continue
        for line in textwrap.wrap(para, width):
            out.append(shape(line))
    return "\n".join(out)


def style_label(label, font, size):
    def apply(*_):
        label.font_name = font
        label.font_size = sp(size)

    apply()
    Clock.schedule_once(apply, 0)


def lab(text, size=16, bold=False, color=TEXT, halign="right", font=None, raw=False, pad=80):
    body = str(text) if raw else fmt(text, size, pad)
    use_font = font or (AR_FONT_B if bold else AR_FONT)
    label = MDLabel(
        text=body,
        halign=halign,
        theme_text_color="Custom",
        text_color=color,
        adaptive_height=True,
        markup=False,
    )
    style_label(label, use_font, size)
    return label


def head(text, size=19, color=GOLD):
    return lab(text, size=size, bold=True, color=color)


def para(text, size=15, color=TEXT):
    return lab(text, size=size, color=color)


def card(children, color=CARD, pad=18, spacing=10, accent=GOLD):
    box = MDCard(
        orientation="vertical",
        padding=dp(pad),
        spacing=dp(spacing),
        adaptive_height=True,
        size_hint_y=None,
        md_bg_color=color,
        radius=[dp(24)] * 4,
        elevation=0,
    )
    if accent is not None:
        strip = MDBoxLayout(
            size_hint=(None, None),
            size=(dp(44), dp(5)),
            md_bg_color=accent,
            radius=[dp(3)] * 4,
            pos_hint={"right": 1},
        )
        box.add_widget(strip)
    for child in children:
        box.add_widget(child)
    return box


def img_card(name, caption=None, accent=GOLD):
    path = asset_path(name)
    if not path:
        return None
    try:
        img = Image(source=path, size_hint_y=None, height=dp(200), fit_mode="contain")
    except TypeError:
        img = Image(source=path, size_hint_y=None, height=dp(200), allow_stretch=True, keep_ratio=True)
    img.bind(width=lambda inst, w: setattr(inst, "height", w * 520.0 / 900.0))
    parts = [img]
    if caption:
        parts.append(lab(caption, size=13, color=MUTED))
    return card(parts, accent=accent)


def tint(color, amount=0.22):
    return (
        CARD[0] * (1 - amount) + color[0] * amount,
        CARD[1] * (1 - amount) + color[1] * amount,
        CARD[2] * (1 - amount) + color[2] * amount,
        1,
    )


def notify(message):
    if toast is not None:
        try:
            toast(shape(message))
        except Exception:
            pass


def open_url(url):
    try:
        webbrowser.open(url)
    except Exception:
        notify("تعذر فتح الرابط")


def btn(text, callback, color=GOLD, text_color=(0, 0, 0, 1), size=14):
    b = MDRaisedButton(
        text=shape(text),
        md_bg_color=color,
        theme_text_color="Custom",
        text_color=text_color,
        font_name=AR_FONT_B,
        font_size=sp(size),
        elevation=0,
    )
    b.bind(on_release=lambda *_: callback())
    return b


def hseg(options, default, on_change, arabic=True):
    scroll = ScrollView(
        size_hint_y=None,
        height=dp(52),
        do_scroll_x=True,
        do_scroll_y=False,
        bar_width=0,
    )
    row = MDBoxLayout(orientation="horizontal", spacing=dp(8), adaptive_width=True, padding=[0, dp(4)])
    buttons = {}

    def paint(selected):
        for key, b in buttons.items():
            on = key == selected
            b.md_bg_color = GOLD if on else CARD2
            b.text_color = (0, 0, 0, 1) if on else TEXT

    def make(key):
        b = MDRaisedButton(
            text=shape(key) if arabic else key,
            md_bg_color=CARD2,
            theme_text_color="Custom",
            text_color=TEXT,
            font_name=AR_FONT_B if arabic else "Roboto",
            font_size=sp(14),
            elevation=0,
        )

        def pressed(*_):
            paint(key)
            on_change(key)

        b.bind(on_release=pressed)
        return b

    for opt in options:
        b = make(opt)
        buttons[opt] = b
        row.add_widget(b)
    paint(default)
    scroll.add_widget(row)
    return scroll


SENS_GUIDE = """ما هي أنواع الحساسية؟
في ببجي موبايل توجد ثلاث مجموعات: حساسية الكاميرا (تحريك الشاشة بدون تصويب)، وحساسية التصويب ADS (عند فتح المنظار)، وحساسية الجايروسكوب (تحريك الجوال نفسه). لكل منظار قيمة مستقلة في كل مجموعة.

القاعدة الذهبية
كلما كبّر المنظار قلّت الحساسية المناسبة له. الرد دوت يحتاج حساسية أعلى، و4x و6x و8x تحتاج حساسية أقل بكثير حتى لا يهتز التصويب."""

SENS_STEPS = """1) ابدأ بقيم متوسطة ثم عدّلها، ولا تنسخ أرقام أي شخص كما هي لأن شاشتك ويدك وجهازك مختلفة.
2) ادخل ساحة التدريب (Training Ground) وارمِ رشقة كاملة على هدف بعيد، ولاحظ إلى أين يهرب الرصاص.
3) غيّر قيمة واحدة فقط في كل مرة، وبمقدار 5 إلى 10 نقاط، ثم أعد التجربة.
4) إن كان الإيم يطير للأعلى بسرعة فاسحب بيدك للأسفل أكثر أو زد حساسية الجايروسكوب قليلاً للتعويض العمودي.
5) إن كان التصويب يهتز يميناً ويساراً فاخفض حساسية ADS للمنظار نفسه.
6) ثبّت اختيارك أسبوعاً كاملاً قبل أن تحكم عليه، فالتبديل المستمر يمنع تكوّن الذاكرة العضلية.
7) تأكد من نظافة الشاشة وإعدادات الإطارات (FPS) ثابتة، فالإطارات المتذبذبة تفسد الثبات.
8) سخّن لمدة 10 دقائق في ساحة التدريب قبل اللعب التنافسي."""

SENS_AIM = """ثبات الإيم (التحكم بالارتداد)
• اسحب للأسفل بحركة ناعمة ثابتة بدل الضغط المتقطع.
• استخدم الرشقات القصيرة في المدى البعيد (3 إلى 5 رصاصات) بدل الرش الكامل.
• ركّب الملحقات التي تقلل الارتداد: المقبض العمودي أو نصف الحربة، والفوهة المناسبة.
• الجلوس أو الانحناء يقلل الارتداد قليلاً ويزيد دقة الرشقة.
• اضبط موضع إبهام اليد المسؤولة عن الإطلاق على زر ثابت، واستعمل زر إطلاق إضافي إن لزم.
• الجايروسكوب: يمنحك تحكماً عمودياً أدق عند المناظير الكبيرة، ويفضّل أن يبدأ بقيم منخفضة جداً ثم يرتفع تدريجياً."""

TACTICS = [
    ("المواجهات القريبة (Close Range)", """• لا تقف ثابتاً: تحرك يميناً ويساراً بسرعة غير منتظمة.
• استخدم سلاحاً رشاشاً (SMG) أو بندقية بمعدل إطلاق عالٍ، وبدّل للسلاح الثانوي بدل إعادة التعبئة تحت النار.
• ابدأ بالرمي من الورك أو بنظام الرد دوت السريع حسب أسلوبك، وفعّل التصويب عند اقتراب الهدف.
• استعمل الجدران والزوايا: اظهر لرمية واحدة ثم اختبئ (Peek) بدل المواجهة المفتوحة.
• القنابل الدخانية والصاعقة تقلب المواجهة القريبة لصالحك."""),
    ("حركة الجيجل (Jiggle)", """الجيجل هو تحريك الشخصية جانبياً (أو الميل) بسرعة وبشكل غير متوقع أثناء المواجهة حتى يصعب على الخصم تثبيت تصويبه.
• أبدل الاتجاه بإيقاع غير ثابت، فالنمط المتكرر يُتوقع بسهولة.
• اجمع بين الميل (Peek) والحركة الجانبية.
• لا تبالغ في الحركة حتى لا تخسر تصويبك أنت أيضاً.
• تدرّب عليه في ساحة التدريب أمام هدف متحرك."""),
    ("ضبط التصويب (Crosshair Placement)", """• أبقِ مركز الشاشة دائماً على مستوى الرأس وعلى الزاوية التي يُتوقع أن يظهر منها العدو.
• لا تنظر إلى الأرض أثناء الركض، ارفع الكاميرا قليلاً ليكون الرأس هو نقطة التصويب.
• عند فتح باب أو تجاوز زاوية، صوّب مسبقاً قبل أن تتحرك.
• استعمل الحافة العمودية لجسم قريب (جدار أو شجرة) كمرجع لارتفاع الرأس."""),
    ("حاسبة الضرر", """الضرر النهائي = الضرر الأساسي للسلاح × مضاعف المنطقة × (1 − نسبة تخفيف الدرع).
يتغير مضاعف الرأس حسب السلاح، وتتغير الأرقام مع تحديثات اللعبة، لذلك استخدم حاسبة الضرر داخل قسم الأسلحة كتقدير تقريبي فقط."""),
    ("تقليل التقطيع (Lag / Ping)", """• استعمل شبكة واي فاي 5GHz قريبة من الراوتر، أو بيانات 4G/5G مستقرة.
• اختر السيرفر الأقرب لك من إعدادات اللعبة.
• أغلق التطبيقات التي تعمل بالخلفية، ولا تحمّل ملفات أثناء اللعب.
• اخفض الرسومات إلى مستوى ثابت وفعّل أعلى معدل إطارات يتحمله جهازك دون سخونة.
• راقب البنج (Ping): تحت 50 ممتاز، من 50 إلى 100 جيد، فوق 100 سيؤثر على المواجهات.
• بدّل بين الواي فاي والبيانات إن لاحظت ارتفاعاً مفاجئاً."""),
]

WEAPONS = {
    "M416": {"dmg": 41, "rate": 8, "ctrl": 8, "range": 8, "type": "AR"},
    "AKM": {"dmg": 49, "rate": 6, "ctrl": 5, "range": 8, "type": "AR"},
    "Beryl M762": {"dmg": 46, "rate": 8, "ctrl": 4, "range": 7, "type": "AR"},
    "SCAR-L": {"dmg": 41, "rate": 7, "ctrl": 8, "range": 8, "type": "AR"},
    "M16A4": {"dmg": 43, "rate": 6, "ctrl": 7, "range": 9, "type": "AR"},
    "Groza": {"dmg": 49, "rate": 9, "ctrl": 5, "range": 7, "type": "AR"},
    "AUG": {"dmg": 43, "rate": 8, "ctrl": 8, "range": 8, "type": "AR"},
    "QBZ": {"dmg": 41, "rate": 7, "ctrl": 8, "range": 8, "type": "AR"},
    "UMP45": {"dmg": 41, "rate": 7, "ctrl": 8, "range": 4, "type": "SMG"},
    "Vector": {"dmg": 31, "rate": 10, "ctrl": 7, "range": 3, "type": "SMG"},
    "UZI": {"dmg": 26, "rate": 10, "ctrl": 7, "range": 3, "type": "SMG"},
    "Mini14": {"dmg": 46, "rate": 5, "ctrl": 8, "range": 9, "type": "DMR"},
    "SKS": {"dmg": 53, "rate": 5, "ctrl": 7, "range": 9, "type": "DMR"},
    "Mk14": {"dmg": 61, "rate": 7, "ctrl": 4, "range": 9, "type": "DMR"},
    "Kar98k": {"dmg": 79, "rate": 2, "ctrl": 10, "range": 10, "type": "SR"},
    "M24": {"dmg": 79, "rate": 2, "ctrl": 10, "range": 10, "type": "SR"},
    "AWM": {"dmg": 105, "rate": 2, "ctrl": 10, "range": 10, "type": "SR"},
}
WEAPON_NAMES = list(WEAPONS.keys())
ARMOR_REDUCTION = {"بدون": 0.0, "مستوى 1": 0.30, "مستوى 2": 0.40, "مستوى 3": 0.55}
HEAD_MULT = {"AR": 2.1, "SMG": 2.1, "DMR": 2.1, "SR": 2.5}

MAPS = [
    ("Erangel", """الخريطة الكلاسيكية الكبيرة ذات التضاريس المتنوعة.
• لوت قوي: Pochinki، School، Georgopol، Military Base، Mylta Power.
• المركبات: متوفرة بكثرة قرب الطرق الرئيسية وفي القرى الكبيرة، والقوارب على السواحل.
• ملاحظة: الأماكن الأقوى مزدحمة، فاختر أطرافها إن أردت لوتاً هادئاً."""),
    ("Miramar", """خريطة صحراوية مفتوحة تميل للمواجهات بعيدة المدى.
• لوت قوي: Hacienda del Patron، Pecado، Los Leones، El Pozo.
• المركبات: منتشرة، وتحتاج إلى استغلال التلال للغطاء.
• ملاحظة: القناصات والمناظير الكبيرة مفيدة جداً هنا."""),
    ("Sanhok", """خريطة صغيرة ومكثفة ومعارك أسرع.
• لوت قوي: Bootcamp، Paradise Resort، Ruins، Pai Nan.
• المركبات: أقل مسافة بين المواجهات، والدراجات والقوارب مفيدة للتنقل السريع.
• ملاحظة: الغابات الكثيفة تقلل مدى الرؤية فتناسب الأسلحة القريبة."""),
    ("Vikendi", """خريطة ثلجية متوسطة بتضاريس متعددة.
• لوت قوي: Castle، Cosmodrome، Dino Park.
• المركبات: الدراجات الثلجية والسيارات متوفرة، وتترك الآثار على الثلج، فانتبه لمن يتبعك.
• ملاحظة: الأبيض في الثلج يكشف حركة من لا يغطي نفسه."""),
]

QUIZ = [
    ("خصم يقترب منك في غرفة صغيرة وأنت تحمل M416 وUZI، ما الأنسب؟", ["UZI مع حركة جانبية", "M416 والوقوف ثابتاً", "الهروب للعراء"], 0),
    ("ما الأفضل عند التصويب بمنظار 6x؟", ["رفع حساسية ADS للمنظار", "خفض حساسية ADS للمنظار", "عدم تغييرها أبداً"], 1),
    ("أين يجب أن يكون مركز التصويب أثناء التقدم؟", ["على الأرض", "على مستوى الرأس", "على السماء"], 1),
    ("بنج 140 في مواجهة قريبة، ما أول إجراء مناسب؟", ["إغلاق التطبيقات الخلفية وتبديل الشبكة", "الاستمرار بنفس الطريقة", "رفع الإطارات للحد الأقصى"], 0),
    ("لماذا نغير قيمة حساسية واحدة فقط في كل تجربة؟", ["لنعرف أي تعديل أثّر فعلاً", "لأنه إلزامي في اللعبة", "لتوفير البطارية"], 0),
]

LOCAL_KB = [
    (["حساسيه", "حساسية", "ثبات", "اهتزاز", "sensitivity", "ثبت"], "ابدأ بقيم متوسطة، وخفّض حساسية ADS كلما زاد تكبير المنظار، وغيّر قيمة واحدة فقط كل مرة وجرّبها في ساحة التدريب على هدف بعيد. راجع قسم الحساسية وثبات الإيم لخطوات التثبيت والحاسبة."),
    (["جايرو", "gyro", "جيرو", "جايروسكوب"], "الجايروسكوب يساعد في التحكم العمودي بالارتداد. ابدأ بقيم منخفضة للمناظير الكبيرة (4x و6x و8x) وارفعها تدريجياً مع التدريب، وجرّب تفعيله عند المناظير فقط أولاً."),
    (["ارتداد", "recoil", "رشقه", "رشق", "سحب", "يطير"], "اسحب للأسفل بحركة ناعمة ثابتة بدل الضغط المتقطع، واستخدم رشقات قصيرة (3 إلى 5 طلقات) في المدى البعيد، وركّب ملحقات تقلل الارتداد مثل المقبض العمودي. الجلوس أو الانحناء يقلل الارتداد قليلاً."),
    (["قريب", "close", "مواجهه", "مواجهات", "قرب"], "في المواجهات القريبة تحرك بشكل غير منتظم، استعمل رشاشاً (SMG) أو سلاحاً سريع الإطلاق، واظهر واختبئ من الزوايا بدل الوقوف المكشوف، وابدأ بقنبلة صاعقة أو دخان إن توفرت."),
    (["جيجل", "jiggle", "تحرك", "حركه"], "الجيجل هو تحريك الشخصية جانبياً أو بالميل بشكل غير متوقع أثناء المواجهة لتصعّب على الخصم التصويب. بدّل الاتجاه بإيقاع غير ثابت ولا تبالغ حتى لا تفقد تصويبك أنت أيضاً."),
    (["تصويب", "crosshair", "راس", "رأس", "مركز"], "أبقِ مركز الشاشة على مستوى الرأس دائماً وعلى الزاوية التي يُتوقع ظهور العدو منها، ولا تنظر للأرض أثناء الركض. صوّب مسبقاً قبل فتح باب أو تجاوز زاوية."),
    (["بنج", "ping", "lag", "تقطيع", "لاق", "تهنيج", "هنج"], "استعمل واي فاي 5GHz قريباً من الراوتر أو بيانات مستقرة، واختر السيرفر الأقرب، وأغلق التطبيقات الخلفية. البنج تحت 50 ممتاز، ومن 50 إلى 100 جيد، وفوق 100 سيؤثر على المواجهات."),
    (["كود حساسيه", "كود الحساسيه", "اكواد الحساسيه", "كود حساسية", "اكواد الحساسية", "شير كود"], "لا أولّد أكواد حساسية وهمية. أكواد الحساسية الحقيقية تُضاف إلى قسم أكواد الحساسية من ملف البيانات السحابي بعد التأكد منها، وتختفي تلقائياً عند انتهاء تاريخها."),
    (["استرداد", "redeem", "كود", "اكواد", "شحن مجاني"], "أكواد الاسترداد تُستبدل من الصفحة الرسمية فقط (pubgmobile.com/redeem) بإدخال Character ID والكود ورمز التحقق، وتصل المكافأة إلى بريد اللعبة. بعض الأكواد محدودة بالوقت أو بالعدد أو بالمنطقة. افتح قسم أكواد الاسترداد."),
    (["افضل سلاح", "اقوى سلاح", "سلاح"], "M416 متوازن وسهل التحكم لمعظم اللاعبين، وAKM أقوى ضرراً لكن ارتداده أعلى، وBeryl M762 سريع لكنه صعب الثبات، وVector وUZI للمواجهات القريبة جداً، وKar98k وAWM للمدى البعيد. استعمل قسم الأسلحة للمقارنة."),
    (["درع", "armor", "خوذه", "خوذة", "helmet"], "الدرع والخوذة من المستوى 3 يقللان الضرر أكثر. أولوية اللوت: درع وخوذة أعلى مستوى متاح، ثم الإسعافات، ثم الملحقات. استخدم حاسبة الضرر في قسم الأسلحة لمعرفة عدد الطلقات التقريبي."),
    (["مركبه", "مركبات", "سياره", "vehicle", "دراجه"], "المركبات تساعدك في الهروب من الدائرة السامة أو الانتقال بسرعة، لكنها تكشف موقعك بالصوت. اترك المركبة قبل الاشتباك واستعملها كغطاء إن لزم."),
    (["دائره", "زون", "zone", "الدائره", "منطقه امنه"], "ادخل الدائرة مبكراً واختر موقعاً مرتفعاً أو خلف غطاء، ولا تتأخر خارجها حتى لا تتحرك تحت النار. راقب الدائرة التالية قبل أن تغلق الحالية."),
    (["تسخين", "تمرين", "تدريب", "warm", "ساحه التدريب"], "سخّن 10 دقائق في ساحة التدريب قبل اللعب: ارمِ رشقات على هدف بعيد، ثم تدرّب على الجيجل أمام هدف متحرك، وبعدها ابدأ المباريات."),
    (["اطارات", "fps", "رسومات", "جرافيك", "سخونه", "سخونة"], "اختر معدل إطارات ثابتاً يتحمله جهازك دون سخونة، فالإطارات المتذبذبة تفسد الثبات أكثر من الإطارات المنخفضة الثابتة. أغلق التطبيقات الخلفية وتجنب اللعب أثناء الشحن السريع."),
    (["فريق", "سكواد", "squad", "تواصل", "ميكرفون"], "تواصل بجمل قصيرة (موقع العدو، المسافة، الاتجاه)، وتحركوا كمجموعة، وقسّموا الزوايا بين اللاعبين، وأنعشوا الزميل بعد تأمين الموقع وليس أثناء النار المفتوحة."),
    (["علاج", "اسعافات", "heal", "صحه", "شفاء"], "عالج بعد أن تؤمّن غطاءً أو تقطع خط النظر باستخدام دخان، ولا تعالج وأنت مكشوف. اللاعب الذي يعالج في العراء هو هدف سهل."),
]


def norm(text):
    t = str(text).lower()
    t = re.sub("[\u064B-\u0652\u0640]", "", t)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ة", "ه"), ("ؤ", "و"), ("ئ", "ي")):
        t = t.replace(a, b)
    return t


def smart_answer(text, data):
    q = norm(text)

    for name, w in WEAPONS.items():
        if norm(name) in q:
            return "%s (%s): ضرر أساسي تقريبي %d، سرعة الإطلاق %d/10، سهولة التحكم %d/10، المدى %d/10. الأرقام تقريبية وقد تتغير مع التحديثات. يمكنك المقارنة بين سلاحين في قسم الأسلحة." % (name, w["type"], w["dmg"], w["rate"], w["ctrl"], w["range"])

    for name, info in MAPS:
        if norm(name) in q:
            return name + "\n" + info

    m = re.search(r"(\d)\s*x", q)
    scope = None
    if m:
        scope = m.group(1) + "x"
    elif "ريد دوت" in q or "red dot" in q or "رد دوت" in q:
        scope = "Red Dot"
    if scope and any(k in q for k in ("حساسيه", "ثبات", "sens", "ads", "منظار")):
        for name, mult in SensCalc.SCOPES:
            if name.lower() == scope.lower():
                return "لمنظار %s: نقطة بداية حساسية ADS تقارب %d%% من قيمة الريد دوت. جرّبها في ساحة التدريب وعدّلها 5 إلى 10 نقاط في كل مرة. استعمل حاسبة نقاط البداية في قسم الحساسية لأرقام جاهزة." % (name, int(mult * 100))

    if any(k in q for k in ("تحديث", "قادم", "سيزون", "موسم", "نسخه", "تسريب", "بكج", "كريت", "عجله", "ترقيه", "رويال باس", "a21", "4.7", "4.6")):
        items = []
        for key in ("upcoming", "leaks"):
            for it in data.get(key, []):
                if isinstance(it, dict) and it.get("title") and not str(it.get("title")).startswith("_"):
                    items.append(str(it["title"]))
        if items:
            return "أحدث ما في التطبيق (معظمه تسريبات غير مؤكدة رسمياً):\n- " + "\n- ".join(items[:7]) + "\nافتح قسم التحديث القادم أو البكجات والتسريبات للتفاصيل والمصدر."
        return "لا توجد معلومات محفوظة حالياً. اضغط تحديث في قسم التحديث القادم ليجلب التطبيق آخر البيانات."

    best, best_score = None, 0
    for keys, answer in LOCAL_KB:
        score = sum((3 if " " in k else 1) for k in keys if norm(k) in q)
        if score > best_score:
            best, best_score = answer, score
    if best:
        return best

    return "لم أفهم سؤالك تماماً. جرّب أن تسأل مثلاً: كيف أثبت الحساسية؟ ما حساسية منظار 6x؟ كيف أقلل الارتداد؟ ما التحديث القادم؟ ما معلومات M416؟ أو راجع أقسام التطبيق من القائمة."


SYSTEM_PROMPT = (
    "أنت مساعد متخصص في لعبة PUBG Mobile داخل تطبيق للاعبين. أجب بالعربية الواضحة وباختصار وبشكل عملي "
    "عن الحساسية وثبات الإيم والتكتيكات والأسلحة والخرائط. لا تخترع أكواد حساسية أو أكواد استرداد أبداً، "
    "وإذا طُلب منك كود فوجّه المستخدم إلى قسم الأكواد في التطبيق أو إلى المصادر الرسمية. "
    "نبّه عندما تكون المعلومة تقريبية أو قد تتغير مع التحديثات."
)


def today_str():
    return datetime.date.today().isoformat()


def not_expired(item):
    exp = str(item.get("expires", "") or "").strip()
    if not exp:
        return True
    return exp >= today_str()


class Page(MDScreen):
    def __init__(self, name, title, builder, app, **kwargs):
        super().__init__(name=name, **kwargs)
        self.title_text = title
        self.builder = builder
        self.app_ref = app
        self.md_bg_color = BG
        root = MDBoxLayout(orientation="vertical")
        self.bar = MDTopAppBar(
            title=shape(title),
            md_bg_color=BAR,
            specific_text_color=GOLD,
            anchor_title="right",
            elevation=0,
            left_action_items=[["arrow-left", lambda *_: app.go("home")]],
            right_action_items=[["menu", lambda *_: app.open_drawer()]],
        )
        Clock.schedule_once(self._style_bar, 0)
        root.add_widget(self.bar)
        self.scroll = MDScrollView(bar_width=0)
        self.body = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=[dp(14), dp(14), dp(14), dp(28)],
            spacing=dp(14),
        )
        self.scroll.add_widget(self.body)
        root.add_widget(self.scroll)
        self.add_widget(root)
        self.refresh()

    def _style_bar(self, *_):
        try:
            self.bar.ids.label_title.font_name = AR_FONT_B
        except Exception:
            pass

    def refresh(self):
        self.body.clear_widgets()
        try:
            widgets = self.builder(self.app_ref)
        except Exception as exc:
            widgets = [para("حدث خطأ أثناء تحميل القسم: " + str(exc), color=RED)]
        for w in widgets:
            self.body.add_widget(w)


class SensCalc(MDBoxLayout):
    STYLES = {
        "ثبات أعلى": (80, 42, 170),
        "متوازن": (95, 50, 200),
        "سرعة أعلى": (110, 60, 240),
    }
    GYRO = ["بدون جايرو", "جايرو عند المناظير", "جايرو دائم"]
    SCOPES = [("Red Dot", 1.0), ("2x", 0.80), ("3x", 0.65), ("4x", 0.55), ("6x", 0.40), ("8x", 0.30)]

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", adaptive_height=True, spacing=dp(8), **kwargs)
        self.style = "متوازن"
        self.gyro = "جايرو عند المناظير"
        self.add_widget(para("أسلوبك في اللعب"))
        self.add_widget(hseg(list(self.STYLES.keys()), self.style, self.set_style))
        self.add_widget(para("استخدام الجايروسكوب"))
        self.add_widget(hseg(self.GYRO, self.gyro, self.set_gyro))
        self.out = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(4))
        self.add_widget(self.out)
        self.render()

    def set_style(self, key):
        self.style = key
        self.render()

    def set_gyro(self, key):
        self.gyro = key
        self.render()

    def render(self):
        self.out.clear_widgets()
        cam, ads, gyro = self.STYLES[self.style]
        self.out.add_widget(lab("نقاط بداية للتجربة (وليست أكواداً):", size=14, color=MUTED))
        for name, mult in self.SCOPES:
            c = int(round(cam * mult))
            a = int(round(ads * mult))
            if self.gyro == "بدون جايرو":
                g = "-"
            elif self.gyro == "جايرو عند المناظير":
                g = "-" if name == "Red Dot" else str(int(round(gyro * mult)))
            else:
                g = str(int(round(gyro * mult)))
            line = "%-8s  Cam %-4d  ADS %-4d  Gyro %s" % (name, c, a, g)
            self.out.add_widget(lab(line, size=13, color=GOLD, halign="left", raw=True, font="Roboto"))
        self.out.add_widget(lab("عدّل كل رقم بمقدار 5 إلى 10 نقاط حتى يستقر التصويب معك.", size=13, color=MUTED))


class DamageCalc(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", adaptive_height=True, spacing=dp(8), **kwargs)
        self.weapon = "M416"
        self.armor = "مستوى 2"
        self.helmet = "مستوى 2"
        self.add_widget(para("السلاح"))
        self.add_widget(hseg(WEAPON_NAMES, self.weapon, self.set_weapon, arabic=False))
        self.add_widget(para("درع الخصم"))
        self.add_widget(hseg(list(ARMOR_REDUCTION.keys()), self.armor, self.set_armor))
        self.add_widget(para("خوذة الخصم"))
        self.add_widget(hseg(list(ARMOR_REDUCTION.keys()), self.helmet, self.set_helmet))
        self.out = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(4))
        self.add_widget(self.out)
        self.render()

    def set_weapon(self, key):
        self.weapon = key
        self.render()

    def set_armor(self, key):
        self.armor = key
        self.render()

    def set_helmet(self, key):
        self.helmet = key
        self.render()

    def render(self):
        self.out.clear_widgets()
        w = WEAPONS[self.weapon]
        body = w["dmg"] * (1 - ARMOR_REDUCTION[self.armor])
        head_dmg = w["dmg"] * HEAD_MULT[w["type"]] * (1 - ARMOR_REDUCTION[self.helmet])
        stk_body = int(math.ceil(100.0 / body))
        stk_head = int(math.ceil(100.0 / head_dmg))
        self.out.add_widget(para("ضرر الطلقة في الجسم: %.1f  | عدد الطلقات للقتل: %d" % (body, stk_body), color=GOLD))
        self.out.add_widget(para("ضرر الطلقة في الرأس: %.1f  | عدد الطلقات للقتل: %d" % (head_dmg, stk_head), color=GOLD))
        self.out.add_widget(lab("الأرقام تقديرية على 100 نقطة صحة، وتتجاهل تأثير المسافة وقد تتغير مع التحديثات.", size=13, color=MUTED))


class WeaponCompare(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", adaptive_height=True, spacing=dp(8), **kwargs)
        self.a = "M416"
        self.b = "AKM"
        self.add_widget(para("السلاح الأول"))
        self.add_widget(hseg(WEAPON_NAMES, self.a, self.set_a, arabic=False))
        self.add_widget(para("السلاح الثاني"))
        self.add_widget(hseg(WEAPON_NAMES, self.b, self.set_b, arabic=False))
        self.out = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(4))
        self.add_widget(self.out)
        self.render()

    def set_a(self, key):
        self.a = key
        self.render()

    def set_b(self, key):
        self.b = key
        self.render()

    def bar(self, value):
        return "#" * int(value) + "." * (10 - int(value))

    def render(self):
        self.out.clear_widgets()
        wa, wb = WEAPONS[self.a], WEAPONS[self.b]
        self.out.add_widget(lab("%s   vs   %s" % (self.a, self.b), size=16, color=GOLD, halign="center", raw=True, font=BRAND_FONT))
        rows = [("Damage", min(wa["dmg"] / 10.5, 10), min(wb["dmg"] / 10.5, 10), wa["dmg"], wb["dmg"]),
                ("Fire Rate", wa["rate"], wb["rate"], wa["rate"], wb["rate"]),
                ("Control", wa["ctrl"], wb["ctrl"], wa["ctrl"], wb["ctrl"]),
                ("Range", wa["range"], wb["range"], wa["range"], wb["range"])]
        for title, va, vb, ra, rb in rows:
            self.out.add_widget(lab(title, size=13, color=MUTED, halign="left", raw=True, font="Roboto"))
            self.out.add_widget(lab("%-10s %s %s" % (self.a[:10], self.bar(va), ra), size=12, color=TEXT, halign="left", raw=True, font="Roboto"))
            self.out.add_widget(lab("%-10s %s %s" % (self.b[:10], self.bar(vb), rb), size=12, color=ORANGE, halign="left", raw=True, font="Roboto"))
        score_a = wa["dmg"] / 10.5 + wa["rate"] + wa["ctrl"] + wa["range"]
        score_b = wb["dmg"] / 10.5 + wb["rate"] + wb["ctrl"] + wb["range"]
        if abs(score_a - score_b) < 1.5:
            verdict = "السلاحان متقاربان بشكل عام، والاختيار يعتمد على أسلوبك والمسافة."
        elif score_a > score_b:
            verdict = "الأفضل بشكل عام حسب هذه المعايير: %s" % self.a
        else:
            verdict = "الأفضل بشكل عام حسب هذه المعايير: %s" % self.b
        self.out.add_widget(para(verdict, color=GOLD))
        self.out.add_widget(lab("التقييمات تقريبية من 10 وتعتمد على الأداء المعتاد، وقد تتغير مع تحديثات اللعبة.", size=13, color=MUTED))


class QuizBox(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", adaptive_height=True, spacing=dp(8), **kwargs)
        self.index = 0
        self.score = 0
        self.render()

    def render(self):
        self.clear_widgets()
        if self.index >= len(QUIZ):
            self.add_widget(head("انتهى الاختبار"))
            self.add_widget(para("نتيجتك: %d من %d" % (self.score, len(QUIZ)), color=GREEN))
            self.add_widget(btn("إعادة الاختبار", self.restart))
            return
        question, options, answer = QUIZ[self.index]
        self.add_widget(lab("السؤال %d من %d" % (self.index + 1, len(QUIZ)), size=13, color=MUTED))
        self.add_widget(para(question))
        for i, opt in enumerate(options):
            b = MDRaisedButton(
                text=shape(opt),
                md_bg_color=CARD2,
                theme_text_color="Custom",
                text_color=TEXT,
                font_name=AR_FONT_B,
                font_size=sp(14),
                elevation=0,
                size_hint_x=1,
            )
            b.bind(on_release=lambda _b, n=i: self.choose(n))
            self.add_widget(b)

    def choose(self, n):
        answer = QUIZ[self.index][2]
        if n == answer:
            self.score += 1
            notify("إجابة صحيحة")
        else:
            notify("إجابة خاطئة")
        self.index += 1
        self.render()

    def restart(self):
        self.index = 0
        self.score = 0
        self.render()


def update_status_card(app):
    state = app.status
    color = GREEN if state.startswith("ok") else (RED if state.startswith("off") else MUTED)
    texts = {
        "ok": "تم التحديث من السحابة",
        "off": "وضع غير متصل: يعرض آخر نسخة محفوظة",
        "nourl": "لم يُضبط رابط البيانات السحابية بعد، اضبطه من الإعدادات",
        "wait": "جاري التحديث...",
    }
    key = state.split(":")[0]
    msg = texts.get(key, state)
    extra = ""
    if app.data.get("updated"):
        extra = "\nآخر تحديث للبيانات: " + str(app.data.get("updated"))
    return card([lab(msg + extra, size=14, color=color), btn("تحديث الآن", app.fetch_data, color=CARD2, text_color=GOLD)], color=CARD)


def build_sens(app):
    widgets = [
        card([head("فهم الحساسية"), para(SENS_GUIDE)]),
        img_card("g_sens_scale.png", "كلما زاد تكبير المنظار قلّت نسبة حساسية ADS المناسبة. هذه نسب تقريبية لنقطة البداية وليست أرقاماً رسمية."),
        card([head("خطوات تثبيت الحساسية"), para(SENS_STEPS)]),
        card([head("ثبات الإيم"), para(SENS_AIM)]),
        img_card("g_recoil.png", "الرصاص يصعد للأعلى أثناء الرشق، فاسحب للأسفل بحركة ناعمة ثابتة لتعويضه.", accent=GREEN),
        card([head("حاسبة نقاط البداية"), para("اختر أسلوبك ليعطيك التطبيق نقاط بداية للمناظير بنسب مناسبة، ثم عدّلها بنفسك."), SensCalc()]),
    ]
    return [w for w in widgets if w is not None]


def build_scodes(app):
    items = [c for c in app.data.get("sensitivity_codes", []) if isinstance(c, dict) and not str(c.get("name", "")).startswith("_") and not_expired(c)]
    widgets = [
        update_status_card(app),
        card([
            head("أكواد الحساسية الحقيقية"),
            para("لا يولّد التطبيق أي كود وهمي. الأكواد تُجلب من ملف البيانات السحابي الذي تحدّثه من مصادر حقيقية (مثل قنوات اللاعبين أو صفحاتهم)، وتُخفى تلقائياً عند بلوغ تاريخ انتهائها."),
        ]),
    ]
    if not items:
        widgets.append(card([para("لا توجد أكواد صالحة حالياً. أضفها إلى ملف البيانات السحابي ثم اضغط تحديث.", color=MUTED)]))
    for item in items:
        code = str(item.get("code", ""))
        parts = [
            head(str(item.get("name", "كود حساسية")), size=17),
            lab("الجهاز: " + str(item.get("device", "غير محدد")), size=14, color=MUTED),
            lab(code, size=15, color=GOLD, halign="left", raw=True, font="Roboto"),
        ]
        if item.get("source"):
            parts.append(lab("المصدر: " + str(item.get("source")), size=13, color=MUTED))
        if item.get("expires"):
            parts.append(lab("صالح حتى: " + str(item.get("expires")), size=13, color=MUTED))
        parts.append(btn("نسخ الكود", lambda c=code: (Clipboard.copy(c), notify("تم نسخ الكود"))))
        widgets.append(card(parts))
    return widgets


def build_tactics(app):
    extras = {
        "حركة الجيجل (Jiggle)": ("g_jiggle.png", "الحركة المتعرجة غير المتوقعة تصعّب على الخصم تثبيت التصويب مقارنة بالحركة المستقيمة.", ORANGE),
        "ضبط التصويب (Crosshair Placement)": ("g_crosshair.png", "أبقِ مركز الشاشة على مستوى الرأس قبل أن يظهر العدو، لا على الأرض.", GREEN),
        "تقليل التقطيع (Lag / Ping)": ("g_ping.png", "البنج تحت 50 ممتاز، ومن 50 إلى 100 جيد، وفوق 100 سيؤثر على المواجهات.", GOLD),
    }
    widgets = []
    for title, text in TACTICS:
        widgets.append(card([head(title), para(text)]))
        if title in extras:
            name, caption, accent = extras[title]
            widgets.append(img_card(name, caption, accent))
    return [w for w in widgets if w is not None]


def build_quiz(app):
    return [card([head("اختبار المواجهات"), para("خمسة أسئلة سريعة لقياس فهمك للتكتيكات والحساسية."), QuizBox()])]


def build_weapons(app):
    return [
        card([head("مقارنة الأسلحة"), WeaponCompare()]),
        card([head("حاسبة الضرر"), DamageCalc()]),
    ]


def build_maps(app):
    widgets = []
    for name, text in MAPS:
        widgets.append(card([lab(name, size=20, color=GOLD, halign="left", raw=True, font=BRAND_FONT), para(text)]))
    widgets.append(card([para("قد تتغير الخرائط والمواقع مع كل تحديث، وتُضاف المعلومات الحديثة عبر التحديث السحابي.", color=MUTED)]))
    return widgets


def build_upcoming(app):
    widgets = [update_status_card(app)]
    items = [u for u in app.data.get("upcoming", []) if isinstance(u, dict) and not str(u.get("title", "")).startswith("_")]
    if not items:
        widgets.append(card([head("التحديث القادم"), para("لا توجد معلومات محفوظة حالياً. تُضاف التحديثات والمودات والقدرات الخاصة إلى ملف البيانات السحابي من المصادر الموثوقة (الموقع الرسمي وقنواته)، وتظهر هنا بعد التحديث.", color=MUTED)]))
    for u in items:
        parts = [head(str(u.get("title", "")), size=17)]
        if u.get("details"):
            parts.append(para(str(u.get("details"))))
        if u.get("source"):
            parts.append(lab("المصدر: " + str(u.get("source")), size=13, color=MUTED))
        widgets.append(card(parts))
    return widgets


LEAK_SECTIONS = [
    ("packs", "البكجات والصناديق وعجلات الحظ", "c_packs.png", GOLD,
     "لا توجد تسريبات عن البكجات أو الصناديق أو عجلات الحظ حالياً."),
    ("royale_pass", "تسريبات الرويال باس القادم", "c_pass.png", hexc("#A06EFF"),
     "لم تتوفر تسريبات كاملة للرويال باس القادم بعد. تظهر هنا المكافآت عند توفرها."),
    ("update", "التحديث القادم", "c_update.png", GREEN,
     "لا توجد معلومات عن التحديث القادم حالياً."),
    ("events", "الفعاليات القادمة", "c_events.png", ORANGE,
     "لا توجد فعاليات قادمة محفوظة حالياً."),
]


def leak_category(item):
    cat = str(item.get("category", "")).strip().lower()
    if cat in ("packs", "royale_pass", "update", "events"):
        return cat
    text = (str(item.get("title", "")) + " " + str(item.get("details", ""))).lower()
    if any(k in text for k in ("royale pass", "رويال باس", "الرويال باس", "rp ")):
        return "royale_pass"
    if any(k in text for k in ("فعالية", "event", "مسار", "ينتهي", "تنتهي")):
        return "events"
    if any(k in text for k in ("تحديث", "update", "الإصدار", "نسخة", "mode", "مود")):
        return "update"
    return "packs"


def leak_card(u, with_tag=True, accent=GOLD):
    parts = [head(str(u.get("title", "")), size=17)]
    if with_tag and "confirmed" in u:
        confirmed = bool(u.get("confirmed", False))
        parts.append(lab("مؤكد" if confirmed else "غير مؤكد", size=13, color=GREEN if confirmed else ORANGE, bold=True))
    if u.get("details"):
        parts.append(para(str(u.get("details"))))
    if u.get("source"):
        parts.append(lab("المصدر: " + str(u.get("source")), size=13, color=MUTED))
    return card(parts, accent=accent)


def build_leaks(app):
    widgets = [update_status_card(app)]

    def valid(lst):
        return [u for u in (lst or []) if isinstance(u, dict) and u.get("title") and not str(u.get("title")).startswith("_")]

    leaks = valid(app.data.get("leaks"))
    upcoming = valid(app.data.get("upcoming"))
    groups = {key: [] for key, _, _, _, _ in LEAK_SECTIONS}
    for u in leaks:
        groups[leak_category(u)].append(u)
    for u in upcoming:
        item = dict(u)
        item.pop("confirmed", None)
        groups["update"].append(item)

    for key, title, image, color, empty in LEAK_SECTIONS:
        widgets.append(card([head(title, size=21, color=color)], accent=color, color=tint(color, 0.18)))
        pic = img_card(image, None, color)
        if pic is not None:
            widgets.append(pic)
        if not groups[key]:
            widgets.append(card([para(empty, color=MUTED)], accent=color))
        for u in groups[key]:
            widgets.append(leak_card(u, with_tag=(key != "update"), accent=color))
    widgets.append(card([lab("هذه المعلومات تسريبات من مصادر خارجية وقد تتغير قبل الإصدار الرسمي. المؤكد منها يُعلَّم بكلمة (مؤكد).", size=13, color=MUTED)]))
    return widgets


def build_redeem(app):
    items = [c for c in app.data.get("redeem_codes", []) if isinstance(c, dict) and not str(c.get("code", "")).startswith("_") and not_expired(c)]
    widgets = [
        update_status_card(app),
        card([
            head("أكواد الاسترداد"),
            para("تُستبدل الأكواد من صفحة الاسترداد الرسمية فقط بإدخال Character ID والكود ورمز التحقق، وتصل المكافأة إلى بريد اللعبة. بعض الأكواد محدودة بالوقت أو بالعدد أو بالمنطقة."),
            btn("فتح صفحة الاسترداد الرسمية", lambda: open_url(REDEEM_URL)),
        ]),
    ]
    if not items:
        widgets.append(card([para("لا توجد أكواد صالحة حالياً. أضف الأكواد المؤكدة إلى الملف السحابي وستظهر هنا وتختفي عند انتهاء تاريخها.", color=MUTED)]))
    for item in items:
        code = str(item.get("code", ""))
        parts = [lab(code, size=18, color=GOLD, halign="left", raw=True, font="Roboto")]
        if item.get("reward"):
            parts.append(lab("المكافأة: " + str(item.get("reward")), size=14, color=TEXT))
        if item.get("expires"):
            parts.append(lab("صالح حتى: " + str(item.get("expires")), size=13, color=MUTED))
        if item.get("source"):
            parts.append(lab("المصدر: " + str(item.get("source")), size=13, color=MUTED))
        parts.append(btn("نسخ الكود", lambda c=code: (Clipboard.copy(c), notify("تم نسخ الكود"))))
        widgets.append(card(parts))
    return widgets


def build_links(app):
    base = [
        ("الموقع الرسمي", "https://www.pubgmobile.com"),
        ("صفحة الاسترداد الرسمية", REDEEM_URL),
        ("Midasbuy (الشحن الرسمي)", "https://www.midasbuy.com"),
        ("يوتيوب PUBG MOBILE", "https://www.youtube.com/@PUBGMOBILE"),
        ("فيسبوك PUBG MOBILE", "https://www.facebook.com/PUBGMOBILE"),
        ("انستغرام PUBG MOBILE", "https://www.instagram.com/pubgmobile"),
        ("إكس (تويتر) PUBG MOBILE", "https://x.com/PUBGMOBILE"),
    ]
    extra = []
    for l in app.data.get("links", []):
        if isinstance(l, dict) and l.get("title") and l.get("url"):
            extra.append((str(l["title"]), str(l["url"])))
    widgets = [card([head("المواقع الرسمية والبطولات"), para("بطولات PUBG Mobile تُبث على القناة الرسمية في يوتيوب، وتُعلن مواعيدها في الموقع الرسمي.")])]
    for title, url in base + extra:
        widgets.append(card([para(title), btn("فتح", lambda u=url: open_url(u))]))
    widgets.append(dev_card())
    return widgets


def build_settings(app):
    url_field = MDTextField(
        text=app.settings.get("data_url", DEFAULT_DATA_URL),
        hint_text="Data URL (JSON)",
        mode="rectangle",
        font_name="Roboto",
    )
    key_field = MDTextField(
        text=app.settings.get("api_key", ""),
        hint_text="Anthropic API Key",
        mode="rectangle",
        password=True,
        font_name="Roboto",
    )

    def save():
        app.settings["data_url"] = url_field.text.strip()
        app.settings["api_key"] = key_field.text.strip()
        app.save_settings()
        notify("تم الحفظ")
        app.fetch_data()

    return [
        card([
            head("رابط البيانات السحابية"),
            para("ضع رابط ملف data.json المستضاف (مثل GitHub Raw). يقرؤه التطبيق عند الفتح ويحفظ نسخة للعمل بدون إنترنت."),
            url_field,
        ]),
        card([
            head("مفتاح المساعد الذكي"),
            para("اختياري: المساعد يعمل مجاناً بدون أي مفتاح. إن أردتَ إجابات أوسع فضع مفتاح Anthropic API الخاص بك (خدمة مدفوعة). يُحفظ المفتاح على جهازك فقط."),
            key_field,
        ]),
        btn("حفظ الإعدادات", save),
    ]


def dev_card():
    parts = [
        lab("تطوير", size=13, color=MUTED, halign="center"),
        lab(DEV_NAME + " " + DEV_TAG, size=26, color=GOLD, halign="center", raw=True, font=BRAND_FONT),
    ]
    if DEV_INSTAGRAM:
        url = "https://www.instagram.com/" + DEV_INSTAGRAM
        parts.append(lab("Instagram: @" + DEV_INSTAGRAM, size=15, color=TEXT, halign="center", raw=True, font="Roboto"))
        parts.append(btn("فتح حسابي على انستغرام", lambda: open_url(url)))
    return card(parts, color=CARD2, accent=None)


class ChatPage(MDScreen):
    def __init__(self, app, **kwargs):
        super().__init__(name="chat", **kwargs)
        self.app_ref = app
        self.md_bg_color = BG
        self.history = []
        root = MDBoxLayout(orientation="vertical")
        self.bar = MDTopAppBar(
            title=shape("المساعد الذكي"),
            md_bg_color=BAR,
            specific_text_color=GOLD,
            anchor_title="right",
            elevation=0,
            left_action_items=[["arrow-left", lambda *_: app.go("home")]],
            right_action_items=[["menu", lambda *_: app.open_drawer()]],
        )
        Clock.schedule_once(self._style_bar, 0)
        root.add_widget(self.bar)
        self.scroll = MDScrollView(bar_width=0)
        self.msgs = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=dp(12),
            spacing=dp(10),
        )
        self.scroll.add_widget(self.msgs)
        root.add_widget(self.scroll)
        quick = [
            "كيف أثبت الحساسية؟",
            "ما حساسية منظار 6x؟",
            "كيف أقلل الارتداد؟",
            "ما التحديث القادم؟",
            "معلومات M416",
            "كيف أقلل البنج؟",
        ]
        root.add_widget(hseg(quick, None, lambda q: self.send(q)))
        row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(64), padding=dp(8), spacing=dp(8), md_bg_color=BAR)
        self.input = MDTextField(hint_text="Ask / اسأل", mode="rectangle", font_name=AR_FONT, multiline=False)
        self.input.bind(on_text_validate=lambda *_: self.send())
        send = MDIconButton(icon="send", theme_icon_color="Custom", icon_color=GOLD)
        send.bind(on_release=lambda *_: self.send())
        row.add_widget(self.input)
        row.add_widget(send)
        root.add_widget(row)
        self.add_widget(root)
        self.bubble("مرحباً بك، أنا مساعد PUBG Mobile المجاني. أعمل بدون إنترنت وبدون أي اشتراك. اسألني عن الحساسية وثبات الإيم والتكتيكات والأسلحة والخرائط والتحديثات، أو اضغط على سؤال سريع بالأسفل.", bot=True)

    def _style_bar(self, *_):
        try:
            self.bar.ids.label_title.font_name = AR_FONT_B
        except Exception:
            pass

    def bubble(self, text, bot):
        color = CARD2 if bot else hexc("#3A2414")
        box = card([lab(text, size=15, color=TEXT, pad=96)], color=color, pad=12, accent=None)
        box.size_hint_x = 0.88
        box.pos_hint = {"x": 0} if bot else {"right": 1}
        holder = MDBoxLayout(adaptive_height=True)
        holder.add_widget(box)
        if not bot:
            holder.clear_widgets()
            holder.add_widget(MDBoxLayout(size_hint_x=0.12))
            holder.add_widget(box)
        self.msgs.add_widget(holder)
        Clock.schedule_once(lambda *_: setattr(self.scroll, "scroll_y", 0), 0.1)
        return holder

    def send(self, preset=None):
        text = (preset or self.input.text).strip()
        if not text:
            return
        self.input.text = ""
        self.bubble(text, bot=False)
        self.pending = self.bubble("...", bot=True)
        threading.Thread(target=self.ask, args=(text,), daemon=True).start()

    def local_answer(self, text):
        try:
            return smart_answer(text, self.app_ref.data)
        except Exception:
            return "تعذر إيجاد إجابة الآن. حاول إعادة صياغة السؤال."

    def ask(self, text):
        key = self.app_ref.settings.get("api_key", "").strip()
        reply = None
        if key:
            try:
                msgs = self.history[-8:]
                while msgs and msgs[0]["role"] != "user":
                    msgs = msgs[1:]
                msgs = msgs + [{"role": "user", "content": text}]
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={"model": AI_MODEL, "max_tokens": 700, "system": SYSTEM_PROMPT, "messages": msgs},
                    timeout=40,
                )
                if resp.status_code == 200:
                    reply = resp.json()["content"][0]["text"].strip()
                    self.history.append({"role": "user", "content": text})
                    self.history.append({"role": "assistant", "content": reply})
                else:
                    reply = "تعذر الاتصال بالمساعد (رمز %d). تحقق من المفتاح.\n\n" % resp.status_code + self.local_answer(text)
            except Exception:
                reply = "لا يوجد اتصال بالإنترنت حالياً.\n\n" + self.local_answer(text)
        else:
            reply = self.local_answer(text)
        Clock.schedule_once(lambda *_: self.show_reply(reply), 0)

    def show_reply(self, reply):
        try:
            self.msgs.remove_widget(self.pending)
        except Exception:
            pass
        self.bubble(reply, bot=True)


TILES = [
    ("sens", "الحساسية وثبات الإيم", "tune"),
    ("scodes", "أكواد الحساسية", "ticket-confirmation"),
    ("tactics", "الشروحات والتكتيكات", "crosshairs-gps"),
    ("quiz", "اختبار المواجهات", "help-circle"),
    ("weapons", "الأسلحة والحاسبة", "sword-cross"),
    ("maps", "الخرائط واللوت", "map"),
    ("upcoming", "التحديث القادم", "update"),
    ("leaks", "البكجات والتسريبات", "treasure-chest"),
    ("redeem", "أكواد الاسترداد", "gift"),
    ("chat", "المساعد الذكي", "robot"),
    ("links", "المصادر الرسمية", "link-variant"),
    ("settings", "الإعدادات", "cog"),
]

TILE_COLORS = ["#E08A4B", "#D9694A", "#3DDC84", "#4DA3FF", "#FF5C5C", "#B388FF", "#2DD4BF", "#FF8AD8", "#E5B25D", "#7C9CFF", "#9AA4B8", "#8E97AB"]

TITLES = {t[0]: t[1] for t in TILES}


class HomePage(MDScreen):
    def __init__(self, app, **kwargs):
        super().__init__(name="home", **kwargs)
        self.app_ref = app
        self.md_bg_color = BG
        scroll = MDScrollView(bar_width=0)
        body = MDBoxLayout(orientation="vertical", adaptive_height=True, padding=[dp(16), dp(28), dp(16), dp(32)], spacing=dp(16))
        body.add_widget(card([
            lab("PUBG MOBILE", size=36, color=GOLD, halign="center", raw=True, font=BRAND_FONT),
            lab("دليلك الاحترافي: حساسية، تكتيكات، أسلحة، وتسريبات", size=15, color=MUTED, halign="center"),
        ], color=CARD2, pad=22, accent=None))
        self.status_label = lab("", size=13, color=MUTED, halign="center")
        body.add_widget(self.status_label)
        grid = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(14))
        for index, (key, title, icon) in enumerate(TILES):
            accent = hexc(TILE_COLORS[index % len(TILE_COLORS)])
            tile = MDCard(
                orientation="vertical",
                padding=dp(14),
                spacing=dp(10),
                size_hint_y=None,
                height=dp(142),
                md_bg_color=CARD,
                radius=[dp(26)] * 4,
                elevation=0,
                ripple_behavior=True,
            )
            circle = MDCard(
                size_hint=(None, None),
                size=(dp(56), dp(56)),
                radius=[dp(28)] * 4,
                md_bg_color=tint(accent, 0.24),
                elevation=0,
                pos_hint={"center_x": 0.5},
            )
            circle.add_widget(MDIcon(icon=icon, halign="center", valign="middle", theme_text_color="Custom", text_color=accent, font_size=sp(28)))
            tile.add_widget(circle)
            tile_label = MDLabel(
                text=fmt(title, 14, width=13),
                halign="center",
                valign="middle",
                theme_text_color="Custom",
                text_color=TEXT,
            )
            style_label(tile_label, AR_FONT_B, 14)
            tile.add_widget(tile_label)
            tile.bind(on_release=lambda _t, k=key: app.go(k))
            grid.add_widget(tile)
        body.add_widget(grid)
        scroll.add_widget(body)
        root = MDBoxLayout(orientation="vertical")
        self.bar = MDTopAppBar(
            title="PUBG VIP",
            md_bg_color=BAR,
            specific_text_color=GOLD,
            anchor_title="right",
            elevation=0,
            right_action_items=[["menu", lambda *_: app.open_drawer()]],
        )
        Clock.schedule_once(self._style_bar, 0)
        root.add_widget(self.bar)
        root.add_widget(scroll)
        self.add_widget(root)

    def _style_bar(self, *_):
        try:
            self.bar.ids.label_title.font_name = BRAND_FONT
        except Exception:
            pass

    def set_status(self, text, color):
        self.status_label.text = fmt(text, 13)
        self.status_label.text_color = color


def build_drawer(app):
    drawer = MDNavigationDrawer(anchor="right", md_bg_color=BAR)
    box = MDBoxLayout(orientation="vertical", padding=[dp(14), dp(24), dp(14), dp(14)], spacing=dp(10))
    box.add_widget(lab("PUBG VIP", size=26, color=GOLD, halign="right", raw=True, font=BRAND_FONT, pad=120))
    box.add_widget(lab("القائمة الرئيسية", size=14, color=MUTED, pad=120))
    scroll = MDScrollView(bar_width=0)
    inner = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(8), padding=[0, dp(6), 0, dp(14)])
    entries = [("home", "الرئيسية", "home")] + list(TILES)
    for index, (key, title, icon) in enumerate(entries):
        accent = hexc(TILE_COLORS[(index - 1) % len(TILE_COLORS)]) if index else GOLD
        row = MDCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            padding=[dp(14), 0, dp(14), 0],
            spacing=dp(12),
            md_bg_color=CARD,
            radius=[dp(16)] * 4,
            elevation=0,
            ripple_behavior=True,
        )
        text_label = MDLabel(
            text=fmt(title, 15, width=24),
            halign="right",
            valign="middle",
            theme_text_color="Custom",
            text_color=TEXT,
        )
        style_label(text_label, AR_FONT_B, 15)
        row.add_widget(text_label)
        row.add_widget(MDIcon(icon=icon, halign="center", valign="middle", theme_text_color="Custom", text_color=accent, size_hint_x=None, width=dp(32), font_size=sp(24)))
        row.bind(on_release=lambda _r, k=key: app.go(k))
        inner.add_widget(row)
    scroll.add_widget(inner)
    box.add_widget(scroll)
    drawer.add_widget(box)
    return drawer


class PubgVipApp(MDApp):
    def build(self):
        self.title = "PUBG VIP"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Amber"
        Window.clearcolor = BG
        if platform not in ("android", "ios"):
            Window.size = (390, 780)
        self.status = "wait"
        self.settings = {"data_url": DEFAULT_DATA_URL, "api_key": ""}
        self.load_settings()
        self.data = self.load_cache()
        self.sm = MDScreenManager()
        self.home = HomePage(self)
        self.sm.add_widget(self.home)
        self.builders = {
            "sens": build_sens,
            "scodes": build_scodes,
            "tactics": build_tactics,
            "quiz": build_quiz,
            "weapons": build_weapons,
            "maps": build_maps,
            "upcoming": build_upcoming,
            "leaks": build_leaks,
            "redeem": build_redeem,
            "links": build_links,
            "settings": build_settings,
        }
        self.pages = {}
        for key, builder in self.builders.items():
            page = Page(key, TITLES[key], builder, self)
            self.pages[key] = page
            self.sm.add_widget(page)
        self.sm.add_widget(ChatPage(self))
        Clock.schedule_once(lambda *_: self.fetch_data(), 0.5)
        Clock.schedule_interval(lambda *_: self.fetch_data(), 1800)
        nav = MDNavigationLayout()
        nav.add_widget(self.sm)
        self.drawer = build_drawer(self)
        nav.add_widget(self.drawer)
        return nav

    def on_resume(self):
        self.fetch_data()

    def open_drawer(self):
        try:
            self.drawer.set_state("open")
        except Exception:
            pass

    def go(self, name):
        try:
            self.drawer.set_state("close")
        except Exception:
            pass
        self.sm.transition.direction = "left" if name != "home" else "right"
        self.sm.current = name

    def path(self, name):
        return os.path.join(self.user_data_dir, name)

    def load_settings(self):
        try:
            with open(self.path("settings.json"), "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                self.settings.update(saved)
        except Exception:
            pass

    def save_settings(self):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            with open(self.path("settings.json"), "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False)
        except Exception:
            pass

    def load_cache(self):
        for source in (self.path("cache.json"), os.path.join(BASE_DIR, "data.json")):
            try:
                with open(source, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if isinstance(cached, dict):
                    merged = dict(DEFAULT_DATA)
                    merged.update(cached)
                    return merged
            except Exception:
                continue
        return dict(DEFAULT_DATA)

    def save_cache(self, data):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            with open(self.path("cache.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def refresh_pages(self):
        for page in self.pages.values():
            page.refresh()
        texts = {
            "ok": ("تم تحديث البيانات من السحابة", GREEN),
            "off": ("وضع غير متصل: آخر نسخة محفوظة", RED),
            "nourl": ("اضبط رابط البيانات من الإعدادات", MUTED),
            "wait": ("جاري التحديث...", MUTED),
        }
        text, color = texts.get(self.status.split(":")[0], (self.status, MUTED))
        self.home.set_status(text, color)

    def fetch_data(self):
        self.status = "wait"
        self.refresh_pages()
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        url = str(self.settings.get("data_url", "")).strip()
        if not url or "YOUR-USERNAME" in url:
            Clock.schedule_once(lambda *_: self._finish("nourl", None), 0)
            return
        try:
            resp = requests.get(url, timeout=12)
            resp.raise_for_status()
            incoming = resp.json()
            if not isinstance(incoming, dict):
                raise ValueError("bad format")
            merged = dict(DEFAULT_DATA)
            merged.update(incoming)
            self.save_cache(merged)
            Clock.schedule_once(lambda *_: self._finish("ok", merged), 0)
        except Exception:
            Clock.schedule_once(lambda *_: self._finish("off", None), 0)

    def _finish(self, state, data):
        self.status = state
        if data is not None:
            self.data = data
        self.refresh_pages()


if __name__ == "__main__":
    PubgVipApp().run()
