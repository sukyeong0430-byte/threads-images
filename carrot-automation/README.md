# 당근 마케팅 자동화 시스템

소상공인이 당근(구 당근마켓)에서 꾸준히 콘텐츠를 올릴 수 있게 만드는 자동화 파이프라인.
**강의 교보재 겸 실제 동작하는 도구**입니다.

## 30초 요약

당근에는 **외부 발행 API가 없고**, 매크로는 운영정책 위반(최대 5년 이용정지)입니다.
그래서 이 시스템은 *자동 발행*을 하지 않습니다. 대신 **발행 직전까지 전부 자동화**해서
사장님이 하는 일을 2시간 → 1분으로 줄입니다. 자세한 근거는
[docs/01_당근_자동화_현실점검.md](docs/01_당근_자동화_현실점검.md).

## 빠른 시작

```bash
# 1. 준비물
pip install pillow
apt-get install ffmpeg fonts-nanum     # macOS: brew install ffmpeg

# 2. 내 가게 정보 채우기
cp config/store.example.json config/store.json
cp config/settings.example.json config/settings.json
vi config/store.json                   # 가게명·메뉴·동네·후기 입력

# 3. 한 번에 실행
python3 scripts/run_pipeline.py
```

결과:

```
output/
├── conti.json / conti.csv / conti.md    # 한 달치 콘티 캘린더 12건
├── cards/P001_card.jpg ...              # 1080×1080 카드 이미지
├── shorts/P001_short.mp4 ...            # 1080×1920 쇼츠 영상
└── packages/2026-09-22_P001/            # 사장님께 보낼 폴더
    ├── 당근_본문.txt                     # 앱에 그대로 붙여넣기
    ├── 스레드_본문.txt / 인스타_본문.txt
    ├── threads.json                      # Threads 자동발행용
    ├── card.jpg / short.mp4
    └── README.md                         # 발행 체크리스트
```

## 스크립트

| 스크립트 | 하는 일 |
|---|---|
| `gen_conti.py` | 가게 정보 → 6개 기둥 순환 콘티 캘린더 (채널별 톤 변형 포함) |
| `make_card.py` | 후킹 문장 → 정사각 카드 이미지 (실사진 있으면 배경 합성) |
| `make_short.py` | 장면 4컷 → 세로 쇼츠 (켄번스 확대 + 크로스페이드) |
| `make_package.py` | 발행 패키지 폴더 생성 |
| `run_pipeline.py` | 위 전부 순서대로 실행 |

옵션 예시:

```bash
python3 scripts/gen_conti.py --seed 7        # 결과 재현
python3 scripts/make_short.py --only P003    # 특정 건만 영상 생성
python3 scripts/run_pipeline.py --videos 0   # 영상 건너뛰고 빠르게
```

## 문서

- [01. 당근 자동화 현실점검](docs/01_당근_자동화_현실점검.md) — 무엇이 되고 안 되는가
- [02. 시스템 아키텍처](docs/02_시스템_아키텍처.md) — 왜 이렇게 설계했나
- [03. 강의 커리큘럼](docs/03_강의_커리큘럼.md) — 4주 과정 / 1일 특강

## 주의

- `config/store.json`, `config/settings.json`, `output/` 은 `.gitignore` 대상입니다.
- API 토큰은 절대 커밋하지 마세요.
- 당근 계정 자동 조작 도구는 이 저장소에 포함하지 않으며, 추가하지 마세요.
