# -*- coding: utf-8 -*-
"""
run_pipeline.py — 콘티 → 카드 → 영상 → 발행패키지 를 한 번에 실행한다.

이 한 줄이 강의의 결론이다:
    python3 scripts/run_pipeline.py
가게 정보 하나 채워두면, 한 달치 콘텐츠가 폴더로 떨어진다.

영상 생성은 무거우므로 기본은 앞 3건만 만든다 (--videos 로 조절).
"""
import argparse, os, subprocess, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run(step, args):
    print(f"\n── {step} " + "─" * (60 - len(step)))
    r = subprocess.run([sys.executable, os.path.join(HERE, step)] + args, cwd=ROOT)
    if r.returncode != 0:
        print(f"[중단] {step} 실패", file=sys.stderr)
        sys.exit(r.returncode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", type=int, default=3, help="영상을 만들 포스트 개수 (0이면 건너뜀)")
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()

    for f in ("config/store.json", "config/settings.json"):
        if not os.path.exists(os.path.join(ROOT, f)):
            print(f"[오류] {f} 없음. `cp {f.replace('.json','.example.json')} {f}` 먼저 실행하세요.",
                  file=sys.stderr)
            sys.exit(1)

    run("gen_conti.py", ["--seed", str(a.seed)] if a.seed is not None else [])
    run("make_card.py", [])

    if a.videos > 0:
        conti = json.load(open(os.path.join(ROOT, "output/conti.json"), encoding="utf-8"))
        ids = ",".join(p["id"] for p in conti["posts"][:a.videos])
        run("make_short.py", ["--only", ids])

    run("make_package.py", [])
    print("\n✅ 완료. output/packages/ 폴더를 사장님께 전달하세요.")


if __name__ == "__main__":
    main()
