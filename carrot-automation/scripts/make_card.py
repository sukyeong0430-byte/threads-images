# -*- coding: utf-8 -*-
"""
make_card.py — 콘티(conti.json)를 읽어 포스트별 카드 이미지를 만든다.

사장님이 포토샵 없이, 사진 한 장 없이도 올릴 게 생기게 하는 것이 목적이다.
실제 음식 사진이 있으면 --photo-dir 로 넣어 배경으로 깔 수 있고,
없으면 브랜드 컬러 단색 카드로 만든다.

출력: output/cards/P001_card.jpg ...
사용: python3 scripts/make_card.py
"""
import argparse, json, os, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = "/usr/share/fonts/truetype/nanum"
FONT_BOLD = os.path.join(FONT_DIR, "NanumSquareRoundB.ttf")
FONT_REG = os.path.join(FONT_DIR, "NanumSquareRoundR.ttf")
FONT_EB = os.path.join(FONT_DIR, "NanumSquareRoundEB.ttf")

PILLAR_BADGE = {
    "menu": "오늘의 메뉴", "event": "이번 주 혜택", "story": "사장님 이야기",
    "review": "단골 후기", "notice": "안내", "local": "동네 소식",
}


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap_by_width(draw, text, fnt, max_w):
    """실제 픽셀 폭으로 줄바꿈한다.

    한글은 공백이 드물지만, 공백이 있는 자리에서 끊는 편이 훨씬 읽기 좋다
    ("이거 하/나로" 같은 어절 중간 절단 방지). 어절 단위로 먼저 시도하고,
    한 어절이 통째로 한 줄보다 길 때만 글자 단위로 쪼갠다.
    """
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = word if not cur else cur + " " + word
            if draw.textlength(trial, font=fnt) <= max_w:
                cur = trial
                continue
            if cur:
                lines.append(cur)
                cur = ""
            # 어절 하나가 한 줄을 넘으면 글자 단위로 강제 분할
            if draw.textlength(word, font=fnt) <= max_w:
                cur = word
            else:
                for ch in word:
                    if draw.textlength(cur + ch, font=fnt) <= max_w:
                        cur += ch
                    else:
                        lines.append(cur); cur = ch
        lines.append(cur)
    return lines


def fit_text(draw, text, path, max_w, max_h, start=96, min_size=44):
    """박스 안에 들어갈 때까지 폰트 크기를 줄여가며 (font, lines)를 찾는다."""
    size = start
    while size >= min_size:
        fnt = font(path, size)
        lines = wrap_by_width(draw, text, fnt, max_w)
        lh = int(size * 1.35)
        if len(lines) * lh <= max_h:
            return fnt, lines, lh
        size -= 4
    fnt = font(path, min_size)
    return fnt, wrap_by_width(draw, text, fnt, max_w), int(min_size * 1.35)


def make_background(size, color, photo=None):
    W, H = size
    if photo and os.path.exists(photo):
        img = Image.open(photo).convert("RGB")
        # 가운데를 정사각으로 크롭한 뒤 어둡게 깔아 글자가 읽히게 만든다
        s = min(img.size)
        left = (img.width - s) // 2
        top = (img.height - s) // 2
        img = img.crop((left, top, left + s, top + s)).resize((W, H), Image.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(3))
        overlay = Image.new("RGB", (W, H), (0, 0, 0))
        return Image.blend(img, overlay, 0.45)
    return Image.new("RGB", (W, H), color)


def render(post, store, size, outdir, photo=None):
    W, H = size
    brand = hex2rgb(store.get("brand_color", "#FF6F0F"))
    img = make_background(size, brand, photo)
    d = ImageDraw.Draw(img)

    pad = int(W * 0.09)

    # 상단 배지
    badge = PILLAR_BADGE.get(post["pillar"], "소식")
    bf = font(FONT_BOLD, int(W * 0.033))
    bw = d.textlength(badge, font=bf)
    bh = int(W * 0.033 * 1.9)
    d.rounded_rectangle([pad, pad, pad + bw + int(W * 0.05), pad + bh],
                        radius=bh // 2, fill=(255, 255, 255))
    d.text((pad + int(W * 0.025), pad + bh * 0.24), badge, font=bf, fill=brand)

    # 메인 후킹 문장
    body_top = pad + bh + int(H * 0.06)
    body_bottom = H - pad - int(H * 0.13)
    fnt, lines, lh = fit_text(d, post["hook"].strip('"'), FONT_EB if os.path.exists(FONT_EB) else FONT_BOLD,
                              W - pad * 2, body_bottom - body_top, start=int(W * 0.095))
    # 글자 수에 따라 줄 수가 달라지므로 블록을 세로 중앙에 맞춘다
    y = body_top + max(0, (body_bottom - body_top - len(lines) * lh) // 2)
    for ln in lines:
        d.text((pad, y), ln, font=fnt, fill=(255, 255, 255))
        y += lh

    # 하단 구분선 + 가게 정보
    line_y = H - pad - int(H * 0.09)
    d.line([(pad, line_y), (W - pad, line_y)], fill=(255, 255, 255, 120), width=3)
    sf = font(FONT_BOLD, int(W * 0.036))
    rf = font(FONT_REG, int(W * 0.03))
    d.text((pad, line_y + int(H * 0.018)), store["store_name"], font=sf, fill=(255, 255, 255))
    sub = f"{store['neighborhood']} · {store.get('nearby_landmark','')}"
    d.text((pad, line_y + int(H * 0.018) + int(W * 0.045)), sub, font=rf, fill=(255, 255, 255))

    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{post['id']}_card.jpg")
    img.save(path, "JPEG", quality=92)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conti", default="output/conti.json")
    ap.add_argument("--store", default="config/store.json")
    ap.add_argument("--settings", default="config/settings.json")
    ap.add_argument("--out", default="output/cards")
    ap.add_argument("--photo-dir", default="assets/photos",
                    help="{ID}.jpg 이름의 사진이 있으면 배경으로 사용")
    a = ap.parse_args()

    conti = json.load(open(a.conti, encoding="utf-8"))
    store = json.load(open(a.store, encoding="utf-8"))
    settings = json.load(open(a.settings, encoding="utf-8"))
    size = tuple(settings.get("card_size", [1080, 1080]))

    made = 0
    for p in conti["posts"]:
        photo = os.path.join(a.photo_dir, f"{p['id']}.jpg")
        path = render(p, store, size, a.out, photo if os.path.exists(photo) else None)
        made += 1
    print(f"[make_card] {made}장 생성 → {a.out}/")


if __name__ == "__main__":
    main()
