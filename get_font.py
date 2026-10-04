"""Download an Arabic UI font at build time and keep it only if it has every glyph the app needs."""
import os
import sys
import urllib.request

from fontTools.ttLib import TTFont

REG = [
    "https://github.com/notofonts/arabic/raw/main/fonts/NotoSansArabic/hinted/ttf/NotoSansArabic-Regular.ttf",
    "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Regular.ttf",
    "https://github.com/google/fonts/raw/main/ofl/almarai/Almarai-Regular.ttf",
    "https://github.com/notofonts/arabic/raw/main/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Regular.ttf",
]
BOLD = [
    "https://github.com/notofonts/arabic/raw/main/fonts/NotoSansArabic/hinted/ttf/NotoSansArabic-Bold.ttf",
    "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Bold.ttf",
    "https://github.com/google/fonts/raw/main/ofl/almarai/Almarai-Bold.ttf",
    "https://github.com/notofonts/arabic/raw/main/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Bold.ttf",
]
NEED = [0x0627, 0x0628, 0xFE8D, 0xFE91, 0xFEE0, 0xFEFB, 0x0041, 0x0030]


def ok(path):
    try:
        cmap = TTFont(path).getBestCmap()
        return all(c in cmap for c in NEED)
    except Exception:
        return False


def fetch(urls, out):
    for url in urls:
        try:
            tmp = out + ".tmp"
            urllib.request.urlretrieve(url, tmp)
            if ok(tmp):
                os.replace(tmp, out)
                print("font ok:", url)
                return True
            print("font rejected (missing glyphs):", url)
        except Exception as exc:
            print("font failed:", url, exc)
        if os.path.exists(out + ".tmp"):
            os.remove(out + ".tmp")
    return False


r = fetch(REG, "arabic.ttf")
b = fetch(BOLD, "arabic_bold.ttf")
if r and not b:
    import shutil
    shutil.copy("arabic.ttf", "arabic_bold.ttf")
if not r:
    print("No font downloaded; the app will use the built-in font.")
sys.exit(0)
