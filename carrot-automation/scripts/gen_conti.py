# -*- coding: utf-8 -*-
"""
gen_conti.py — 가게 정보(store.json)를 읽어 N주치 콘텐츠 콘티 캘린더를 생성한다.

소상공인 자동화의 1단계. "오늘 뭐 올리지?"를 없애는 것이 목표다.
6개 콘텐츠 기둥(pillar)을 순환시켜 소재가 겹치지 않게 하고,
같은 소재를 당근/스레드/인스타 3개 채널 톤으로 각각 변형해 둔다.

출력: output/conti.json, output/conti.csv, output/conti.md
사용: python3 scripts/gen_conti.py --store config/store.json --settings config/settings.json
"""
import argparse, json, csv, os, random, sys
from datetime import date, timedelta

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]

# ---------------------------------------------------------------------------
# 콘텐츠 기둥(pillar) — 소상공인 로컬 마케팅의 6가지 반복 소재
# 하나만 계속 올리면(=할인만) 단골이 피로해진다. 섞어야 오래 간다.
# ---------------------------------------------------------------------------
PILLARS = [
    ("menu",      "신메뉴·대표메뉴 소개", "팔고 싶은 걸 직접 보여준다"),
    ("event",     "이번 주 혜택·이벤트", "당장 방문할 이유를 만든다"),
    ("story",     "사장님 이야기",        "가게를 신뢰하게 만든다"),
    ("review",    "단골 후기 소개",       "남의 말이 내 말보다 세다"),
    ("notice",    "운영 안내",            "헛걸음을 막아 불만을 줄인다"),
    ("local",     "동네 밀착 인사",       "'우리 동네 가게'로 각인시킨다"),
]


def _item(store, idx):
    items = store.get("signature_items") or [{"name": "대표 메뉴", "price": 0, "desc": ""}]
    return items[idx % len(items)]


def _price(v):
    return f"{v:,}원" if v else ""


# ---------------------------------------------------------------------------
# 기둥별 콘티 생성기
# 각 함수는 dict를 반환한다: hook(첫줄), body(본문), image_brief, video_scenes
# ---------------------------------------------------------------------------
def make_menu(store, i):
    it = _item(store, i)
    hood = store["neighborhood"]
    return {
        "hook": f"{hood}에서 이거 하나로 {random.choice([3, 5, 7, 10])}년 버텼습니다",
        "body": (
            f"{store['store_name']} 대표 메뉴 '{it['name']}' 소개드려요.\n\n"
            f"{it.get('desc','')}\n"
            f"가격은 {_price(it.get('price'))}이고, 점심에 제일 많이 나갑니다.\n\n"
            f"{store['open_hours']} 영업하고 {store['closed_day']}은 쉽니다.\n"
            f"{store['cta']}"
        ),
        "image_brief": f"{it['name']} 클로즈업, 김이 올라오는 순간, 자연광, 위에서 45도",
        "video_scenes": [
            f"{it['name']} 끓는 장면 (소리 살리기)",
            f"{it.get('desc','')}",
            f"{_price(it.get('price'))} · {store['neighborhood']}",
            f"{store['cta']}",
        ],
    }


EVENT_HOOKS = [
    "이번 주만 하는 거라 미리 알려드려요",
    "조용히 단골분들께만 먼저 알립니다",
    "이번 주 오시는 분들 손해 안 보시게",
    "수량이 정해져 있어 미리 공지드려요",
]


def make_event(store, i):
    it = _item(store, i + 1)
    return {
        "hook": EVENT_HOOKS[i % len(EVENT_HOOKS)],
        "body": (
            f"{store['store_name']} 이번 주 혜택입니다.\n\n"
            f"· '{it['name']}' 주문하시면 {random.choice(['음료 서비스','계란후라이 추가','공기밥 무한'])}\n"
            f"· 당근 소식 보고 오셨다고 말씀만 해주세요\n\n"
            f"준비된 수량이 있어서 소진되면 종료됩니다.\n"
            f"{store['open_hours']} / {store['closed_day']} 휴무"
        ),
        "image_brief": f"'이번 주만' 큼직한 텍스트 + {it['name']} 사진, 브랜드 컬러 배경",
        "video_scenes": ["이번 주만!", f"{it['name']} 주문 시 서비스", "당근 보고 왔다고 말씀만", store["cta"]],
    }


def make_story(store, i):
    topics = [
        ("새벽에 장 보러 가는 이유", "좋은 재료는 아침에 다 나갑니다. 그래서 새벽에 나갑니다."),
        ("가격을 못 올리는 이유", "단골 손님들 얼굴이 떠올라서요. 재료비 올라도 최대한 버텨봅니다."),
        ("이 가게를 시작한 계기", "제가 자취할 때 제대로 된 집밥 한 끼가 그렇게 그리웠거든요."),
        ("반찬을 매일 새로 하는 이유", "전날 것 내놓으면 제가 먼저 압니다. 손님은 더 잘 아시고요."),
    ]
    t, d = topics[i % len(topics)]
    return {
        "hook": t,
        "body": (
            f"{d}\n\n"
            f"{store['neighborhood']}에서 {store['store_name']} 하는 {store['owner_name']}입니다.\n"
            f"거창한 건 없고, 그냥 매일 같은 걸 같은 맛으로 내는 게 목표예요.\n\n"
            f"오시면 아는 척 해주세요. 반갑습니다."
        ),
        "image_brief": "사장님 손·주방 작업 장면 (얼굴 노출 부담되면 손만). 따뜻한 색감",
        "video_scenes": [t, d, f"{store['neighborhood']} {store['store_name']}", "오시면 아는 척 해주세요"],
    }


def make_review(store, i):
    quotes = store.get("review_quotes") or ["맛있게 잘 먹었습니다"]
    q = quotes[i % len(quotes)]
    return {
        "hook": f'"{q}"',
        "body": (
            f"손님이 남겨주신 후기예요. 이런 말 들으면 하루가 갑니다.\n\n"
            f"'{q}'\n\n"
            f"{store['store_name']}는 {store['open_hours']}, {store['closed_day']} 쉽니다.\n"
            f"{store['nearby_landmark']}에서 가까워요."
        ),
        "image_brief": f"후기 텍스트를 카드 중앙에 크게. 배경은 매장 내부 흐린 사진",
        "video_scenes": [f'"{q}"', "— 실제 손님 후기", f"{store['nearby_landmark']} 근처", store["cta"]],
    }


def make_notice(store, i):
    notices = [
        (f"{store['closed_day']} 휴무 안내", f"매주 {store['closed_day']}은 쉽니다. 헛걸음 마세요!"),
        ("브레이크타임 없습니다", f"{store['open_hours']} 내내 열려 있어요. 늦은 점심도 환영입니다."),
        (f"라스트오더 {store.get('last_order','마감 30분 전')}", "마감 직전 방문은 미리 전화 한 통 주시면 준비해둘게요."),
        ("포장 됩니다", "당근 채팅으로 미리 주문하시면 기다리지 않으셔도 돼요."),
    ]
    t, d = notices[i % len(notices)]
    return {
        "hook": t,
        "body": f"{d}\n\n{store['store_name']} ({store['nearby_landmark']})\n{store['open_hours']}\n{store['cta']}",
        "image_brief": f"'{t}' 텍스트 위주 안내 카드. 가독성 최우선, 큰 글씨",
        "video_scenes": [t, d, store["store_name"], store["cta"]],
    }


def make_local(store, i):
    seasons = [
        "날이 갑자기 추워졌어요. 따뜻한 국물 생각나는 날입니다.",
        "비 오네요. 이런 날은 손님이 뜸한데, 자리는 넉넉합니다.",
        "동네 산책하시다가 배고프면 들러주세요.",
        "퇴근길에 밥 해먹기 싫은 날 있잖아요. 그럴 때 오세요.",
    ]
    greetings = [
        f"{store['neighborhood']} 이웃분들께",
        f"{store['neighborhood']} 사시는 분들 보세요",
        f"{store['nearby_landmark']} 지나다니시는 분들께",
        f"{store['neighborhood']} 주민분들, 안녕하세요",
    ]
    return {
        "hook": greetings[i % len(greetings)],
        "body": (
            f"{seasons[i % len(seasons)]}\n\n"
            f"{store['nearby_landmark']} 바로 앞 {store['store_name']}입니다.\n"
            f"{store['open_hours']} / {store['closed_day']} 휴무\n\n"
            f"{store['cta']}"
        ),
        "image_brief": "매장 외관 또는 동네 풍경 + 간판이 보이게. 시간대는 해질녘",
        "video_scenes": [f"{store['neighborhood']} 이웃분들께", seasons[i % len(seasons)],
                         store["nearby_landmark"], store["cta"]],
    }


GENERATORS = {
    "menu": make_menu, "event": make_event, "story": make_story,
    "review": make_review, "notice": make_notice, "local": make_local,
}


# ---------------------------------------------------------------------------
# 채널별 변형 — 같은 소재, 다른 톤
# 당근: 담백·동네말투·해시태그 최소 (해시태그 도배는 당근에서 역효과)
# 스레드: 후킹 강하게, 짧게, 해시태그 2~3개
# 인스타: 줄바꿈 넉넉히, 해시태그 다수
# ---------------------------------------------------------------------------
def to_daangn(c, store):
    return f"{c['hook']}\n\n{c['body']}"


def to_threads(c, store):
    tags = " ".join("#" + k.replace(" ", "") for k in store.get("keywords", [])[:3])
    body = c["body"].split("\n\n")[0]
    text = f"{c['hook']}\n\n{body}\n\n{tags}"
    return text[:480]


def to_instagram(c, store):
    tags = " ".join("#" + k.replace(" ", "") for k in store.get("keywords", []))
    tags += f" #{store['neighborhood']} #{store['neighborhood']}맛집"
    return f"{c['hook']}\n.\n{c['body']}\n.\n{tags}"


# ---------------------------------------------------------------------------
def build(store, settings, start=None):
    weeks = settings.get("weeks", 4)
    per_week = settings.get("posts_per_week", 3)
    days = settings.get("publish_days", ["화", "목", "토"])[:per_week]
    time_ = settings.get("publish_time", "11:30")

    start = start or date.today()
    # 시작일이 속한 주의 월요일
    monday = start - timedelta(days=start.weekday())
    if monday < start:
        monday += timedelta(days=7)  # 이번 주가 이미 지났으면 다음 주부터

    posts, n = [], 0
    for w in range(weeks):
        for d in days:
            offset = WEEKDAY_KO.index(d)
            pub = monday + timedelta(days=7 * w + offset)
            key, label, why = PILLARS[n % len(PILLARS)]
            # 변형 인덱스는 '그 기둥이 몇 번째로 등장했는지'로 센다.
            # n을 그대로 쓰면 6주기마다 같은 메뉴·같은 후기가 반복된다.
            occ = n // len(PILLARS)
            c = GENERATORS[key](store, occ)
            posts.append({
                "id": f"P{n+1:03d}",
                "date": pub.isoformat(),
                "weekday": d,
                "time": time_,
                "pillar": key,
                "pillar_label": label,
                "pillar_why": why,
                "hook": c["hook"],
                "body": c["body"],
                "image_brief": c["image_brief"],
                "video_scenes": c["video_scenes"],
                "channels": {
                    "daangn": to_daangn(c, store),
                    "threads": to_threads(c, store),
                    "instagram": to_instagram(c, store),
                },
                "status": "draft",
            })
            n += 1
    return posts


def save(posts, store, outdir):
    os.makedirs(outdir, exist_ok=True)

    with open(os.path.join(outdir, "conti.json"), "w", encoding="utf-8") as f:
        json.dump({"store": store["store_name"], "generated": date.today().isoformat(),
                   "posts": posts}, f, ensure_ascii=False, indent=2)

    with open(os.path.join(outdir, "conti.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ID", "발행일", "요일", "시각", "기둥", "후킹문장", "당근 본문", "이미지 브리프", "상태"])
        for p in posts:
            w.writerow([p["id"], p["date"], p["weekday"], p["time"], p["pillar_label"],
                        p["hook"], p["channels"]["daangn"], p["image_brief"], p["status"]])

    with open(os.path.join(outdir, "conti.md"), "w", encoding="utf-8") as f:
        f.write(f"# {store['store_name']} 콘텐츠 콘티\n\n")
        f.write(f"- 생성일: {date.today().isoformat()}\n- 총 {len(posts)}건\n\n")
        f.write("| ID | 발행일 | 기둥 | 후킹 문장 | 상태 |\n|---|---|---|---|---|\n")
        for p in posts:
            f.write(f"| {p['id']} | {p['date']}({p['weekday']}) | {p['pillar_label']} | "
                    f"{p['hook'].replace(chr(10),' ')} | {p['status']} |\n")
    print(f"[gen_conti] {len(posts)}건 생성 → {outdir}/conti.json, conti.csv, conti.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="config/store.json")
    ap.add_argument("--settings", default="config/settings.json")
    ap.add_argument("--out", default="output")
    ap.add_argument("--seed", type=int, default=None, help="고정하면 같은 결과 재현")
    a = ap.parse_args()

    if a.seed is not None:
        random.seed(a.seed)

    for path in (a.store, a.settings):
        if not os.path.exists(path):
            ex = path.replace(".json", ".example.json")
            print(f"[오류] {path} 가 없습니다. `cp {ex} {path}` 후 내용을 채워주세요.", file=sys.stderr)
            sys.exit(1)

    store = json.load(open(a.store, encoding="utf-8"))
    settings = json.load(open(a.settings, encoding="utf-8"))
    save(build(store, settings), store, a.out)


if __name__ == "__main__":
    main()
