# -*- coding: utf-8 -*-
"""
make_package.py — 발행 직전 '사람이 1분 쓰는 지점'을 위한 패키지를 만든다.

당근은 외부 발행 API가 없다. 그래서 자동화의 종착점은 '자동 발행'이 아니라
"사장님이 폰에서 30초 만에 붙여넣고 올릴 수 있는 상태"다.
이 스크립트는 포스트별 폴더에 붙여넣기용 텍스트 + 카드 + 영상 + 체크리스트를 모은다.

출력: output/packages/2026-09-22_P001/
사용: python3 scripts/make_package.py
"""
import argparse, json, os, shutil

CHECKLIST = """# {id} 발행 체크리스트

- 발행 예정: **{date} ({weekday}) {time}**
- 콘텐츠 기둥: {pillar_label} — {pillar_why}

## 1. 당근 (비즈프로필 → 소식)
1. 당근 앱 → 내 비즈프로필 → '소식 쓰기'
2. `당근_본문.txt` 내용 붙여넣기
3. `card.jpg` (또는 직접 찍은 사진) 첨부
4. 게시

> 당근은 외부 발행 API가 없습니다. 이 단계만 사람이 합니다.
> 매크로·자동 등록 프로그램은 운영정책 위반이라 계정이 정지될 수 있으니 쓰지 마세요.

## 2. Threads / 인스타 (자동 발행 가능)
- Threads: `python3 ../threads-auto-publish/scripts/publish.py --file threads.json`
- 인스타 릴스: `short.mp4` 업로드 + `인스타_본문.txt`

## 3. 발행 후
- [ ] conti.json 의 status 를 `published` 로 변경
- [ ] 3일 뒤 조회수/채팅문의 수 기록

## 촬영 가이드(직접 사진 찍을 경우)
{image_brief}
"""


def build(post, conti_dir, outroot):
    folder = os.path.join(outroot, f"{post['date']}_{post['id']}")
    os.makedirs(folder, exist_ok=True)

    # 채널별 붙여넣기용 텍스트
    names = {"daangn": "당근_본문.txt", "threads": "스레드_본문.txt", "instagram": "인스타_본문.txt"}
    for ch, fname in names.items():
        with open(os.path.join(folder, fname), "w", encoding="utf-8") as f:
            f.write(post["channels"][ch])

    # threads-auto-publish 스킬이 바로 먹을 수 있는 형식
    with open(os.path.join(folder, "threads.json"), "w", encoding="utf-8") as f:
        json.dump([{"text": post["channels"]["threads"]}], f, ensure_ascii=False, indent=2)

    # 이미지/영상 복사 (있으면)
    for src, dst in [
        (os.path.join(conti_dir, "cards", f"{post['id']}_card.jpg"), "card.jpg"),
        (os.path.join(conti_dir, "shorts", f"{post['id']}_short.mp4"), "short.mp4"),
    ]:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(folder, dst))

    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as f:
        f.write(CHECKLIST.format(**post))
    return folder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conti", default="output/conti.json")
    ap.add_argument("--assets-dir", default="output", help="cards/, shorts/ 가 있는 폴더")
    ap.add_argument("--out", default="output/packages")
    a = ap.parse_args()

    conti = json.load(open(a.conti, encoding="utf-8"))
    made = [build(p, a.assets_dir, a.out) for p in conti["posts"]]
    print(f"[make_package] {len(made)}개 패키지 생성 → {a.out}/")
    print("   사장님께는 이 폴더만 통째로 보내면 됩니다 (구글드라이브/카톡).")


if __name__ == "__main__":
    main()
