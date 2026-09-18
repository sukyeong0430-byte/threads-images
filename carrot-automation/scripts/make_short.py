# -*- coding: utf-8 -*-
"""
make_short.py — 콘티의 video_scenes를 세로 쇼츠 영상(1080x1920)으로 만든다.

편집 프로그램 없이, 사장님 사진 몇 장(또는 아예 없이)으로
릴스/쇼츠/당근 소식용 짧은 영상을 뽑는 것이 목적이다.

프레임을 파이썬(PIL)에서 직접 그려 ffmpeg에 넘긴다.
ffmpeg 필터(zoompan/xfade)를 쓰지 않는 이유는, 수강생이
"어느 줄이 무슨 효과인지" 코드에서 바로 읽을 수 있게 하기 위해서다.

출력: output/shorts/P001_short.mp4
사용: python3 scripts/make_short.py --only P001
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = "/usr/share/fonts/truetype/nanum"
FONT_BOLD = os.path.join(FONT_DIR, "NanumSquareRoundB.ttf")
FONT_REG = os.path.join(FONT_DIR, "NanumSquareRoundR.ttf")

FPS = 24
ZOOM = 1.15          # 켄번스(천천히 확대) 효과의 시작 배율
XFADE_SEC = 0.4      # 장면 전환 크로스페이드 길이


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def wrap_by_width(draw, text, fnt, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = word if not cur else cur + " " + word
            if draw.textlength(trial, font=fnt) <= max_w:
                cur = trial
                continue
            if cur:
                lines.append(cur); cur = ""
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


def scene_base(text, store, size, photo=None):
    """장면 하나의 '원본' 이미지(출력보다 ZOOM배 큰 캔버스)를 그린다."""
    W, H = int(size[0] * ZOOM), int(size[1] * ZOOM)
    brand = hex2rgb(store.get("brand_color", "#FF6F0F"))

    if photo and os.path.exists(photo):
        img = Image.open(photo).convert("RGB")
        # 세로 비율에 맞춰 꽉 채우도록 크롭
        target = W / H
        src = img.width / img.height
        if src > target:
            nw = int(img.height * target)
            img = img.crop(((img.width - nw) // 2, 0, (img.width - nw) // 2 + nw, img.height))
        else:
            nh = int(img.width / target)
            img = img.crop((0, (img.height - nh) // 2, img.width, (img.height - nh) // 2 + nh))
        img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2))
        img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), 0.5)
    else:
        img = Image.new("RGB", (W, H), brand)

    d = ImageDraw.Draw(img)
    pad = int(W * 0.10)

    # 자막: 화면 중앙, 길이에 따라 크기 자동 조절
    size_px = int(W * 0.085)
    while size_px > int(W * 0.045):
        fnt = ImageFont.truetype(FONT_BOLD, size_px)
        lines = wrap_by_width(d, text, fnt, W - pad * 2)
        if len(lines) * size_px * 1.35 <= H * 0.5:
            break
        size_px -= 4
    lh = int(size_px * 1.35)
    y = int(H * 0.45) - (len(lines) * lh) // 2
    for ln in lines:
        # 사진 위에서도 읽히도록 얇은 그림자를 깐다
        d.text((pad + 3, y + 3), ln, font=fnt, fill=(0, 0, 0))
        d.text((pad, y), ln, font=fnt, fill=(255, 255, 255))
        y += lh

    # 하단 워터마크.
    # 릴스/쇼츠는 화면 아래 15%를 플랫폼 UI(좋아요·계정명)가 덮는다.
    # 그 위(세이프 영역 안)에 둬야 잘리지 않는다.
    wf = ImageFont.truetype(FONT_REG, int(W * 0.032))
    d.text((pad, int(H * 0.85)), f"{store['neighborhood']} · {store['store_name']}",
           font=wf, fill=(255, 255, 255), anchor="ls")
    return img


def frame_at(base, size, t):
    """t(0~1)에 따라 천천히 확대되는 프레임 한 장을 만든다."""
    W, H = size
    scale = ZOOM - (ZOOM - 1.0) * t          # 잘라내는 영역이 점점 작아짐 = 확대
    cw, ch = int(W * scale), int(H * scale)
    left = (base.width - cw) // 2
    top = (base.height - ch) // 2
    return base.crop((left, top, left + cw, top + ch)).resize((W, H), Image.BILINEAR)


def build_video(post, store, size, sec_per_scene, outdir, photo_dir=None):
    scenes = [s for s in post["video_scenes"] if s and s.strip()]
    if not scenes:
        return None

    photo = None
    if photo_dir:
        cand = os.path.join(photo_dir, f"{post['id']}.jpg")
        photo = cand if os.path.exists(cand) else None

    bases = [scene_base(s, store, size, photo) for s in scenes]
    n = int(FPS * sec_per_scene)
    xf = int(FPS * XFADE_SEC)

    tmp = tempfile.mkdtemp(prefix="short_")
    idx = 0
    try:
        for i, base in enumerate(bases):
            last = (i == len(bases) - 1)
            # 마지막 장면을 빼고는 꼬리 xf 프레임을 다음 장면이 크로스페이드로 가져간다
            emit = n if last else n - xf
            for f in range(emit):
                t = f / max(1, n - 1)
                img = frame_at(base, size, t)
                if i > 0 and f < xf:
                    prev_t = (n - xf + f) / max(1, n - 1)
                    prev = frame_at(bases[i - 1], size, prev_t)
                    img = Image.blend(prev, img, f / xf)
                img.save(os.path.join(tmp, f"{idx:05d}.jpg"), "JPEG", quality=90)
                idx += 1

        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, f"{post['id']}_short.mp4")
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.jpg"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
            # 인스타/유튜브가 재인코딩 없이 받아들이는 안전한 설정
            "-movflags", "+faststart", out,
        ]
        subprocess.run(cmd, check=True)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conti", default="output/conti.json")
    ap.add_argument("--store", default="config/store.json")
    ap.add_argument("--settings", default="config/settings.json")
    ap.add_argument("--out", default="output/shorts")
    ap.add_argument("--photo-dir", default="assets/photos")
    ap.add_argument("--only", default=None, help="특정 ID만 (쉼표로 여러 개). 예: P001,P002")
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        print("[오류] ffmpeg가 없습니다. `apt-get install ffmpeg` 또는 brew install ffmpeg", file=sys.stderr)
        sys.exit(1)

    conti = json.load(open(a.conti, encoding="utf-8"))
    store = json.load(open(a.store, encoding="utf-8"))
    settings = json.load(open(a.settings, encoding="utf-8"))
    size = tuple(settings.get("short_size", [1080, 1920]))
    sec = settings.get("short_seconds_per_scene", 2.5)

    targets = set(a.only.split(",")) if a.only else None
    made = []
    for p in conti["posts"]:
        if targets and p["id"] not in targets:
            continue
        out = build_video(p, store, size, sec, a.out, a.photo_dir)
        if out:
            made.append(out)
            print(f"  · {p['id']} → {out}")
    print(f"[make_short] {len(made)}개 생성 → {a.out}/")


if __name__ == "__main__":
    main()
