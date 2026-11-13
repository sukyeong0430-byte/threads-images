#!/usr/bin/env python3
"""Build index.html for the narrated (no-face) reel from a line table.
Usage: build.py [durations.json]  -- durations.json maps line id -> seconds (from real narration)."""
import json, re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = 0.25      # pause after each line
LEAD = 0.35     # scene lead-in before first line
TAIL = 0.45     # scene tail after last line

# id, caption html (대본 기준), est seconds, emphasis
SCENES = [
 ("hook", [("h1", "ChatGPT 새 기능, <b>다 따라갈 필요</b> 없어요", 2.9),
           ("h2", "엄마와 선생님이 당장 쓸 <b>4가지</b>만 알려드릴게요", 3.4)]),
 ("word", [("w1", "첫 번째, <b>워드</b>예요", 1.6),
           ("w2", "워드 안에 ChatGPT가 <b>공식으로</b> 들어왔어요", 3.3),
           ("w3", "가정통신문을 열고 <b>읽기 쉽게</b> 바꿔 달라고 하면", 3.6),
           ("w4", "창을 옮길 필요 없이 <b>그 자리에서</b> 고쳐져요", 3.2),
           ("w5", "<b>무료 플랜</b>도 됩니다", 1.6)]),
 ("dots", [("d1", "두 번째, <b>Dots</b>예요", 1.6),
           ("d2", "<b>24시간</b> 일하는 에이전트인데요", 2.6),
           ("d3", "캘린더를 연결해 두면 일정을 <b>계속</b> 지켜보다가", 3.6),
           ("d4", "학원 시간과 약속이 겹치면 <b>폰으로</b> 먼저 알려줘요", 3.8)]),
 ("space", [("s1", "세 번째, <b>Space</b>예요", 1.7),
            ("s2", "ChatGPT가 들어 있는 문서를 동료와 <b>같이 쓰는</b> 공간이에요", 4.2),
            ("s3", "수업 계획서를 공유하면 <b>같은 화면</b>에서 함께 고치고", 3.6),
            ("s4", "남은 할 일도 <b>나눠</b> 줘요", 1.9)]),
 ("stick", [("k1", "네 번째, <b>스티커팩</b>이에요", 2.0),
            ("k2", "셀카 한 장 올리고 <b>스타일</b>만 고르면", 2.7),
            ("k3", "내 얼굴로 <b>표정 스티커</b>가 만들어져요", 2.9)]),
 ("cta", [("c1", "설정 방법은 <b>PDF</b>로 정리해 뒀어요", 2.8),
          ("c2", "댓글에 <b>‘가이드’</b>라고 남겨 주시면", 2.6),
          ("c3", "바로 보내드릴게요", 1.6)]),
]
dur = {}
if len(sys.argv) > 1:
    dur = json.load(open(sys.argv[1]))
voice = bool(dur)

T = {}      # line id -> (start, dur)
SC = {}     # scene -> (start, dur)
t = 0.0
for sid, lines in SCENES:
    s0 = t; t += LEAD
    for lid, _, est in lines:
        d = dur.get(lid, est)
        T[lid] = (round(t, 3), d); t += d + GAP
    t += TAIL - GAP
    SC[sid] = (round(s0, 3), round(t - s0, 3))
TOTAL = round(t + 0.6, 2)
SC["cta"] = (SC["cta"][0], round(TOTAL - SC["cta"][0], 3))

css = re.search(r"<style>(.*?)</style>", open(os.path.join(ROOT, "tools", "base.css.html")).read(), re.S).group(1)
css += """
      .caps { top: 1210px; height: 170px; }
      .cap { height: 170px; padding: 0 30px; font-size: 52px; line-height: 1.28; display: flex; align-items: center; justify-content: center; }
      .cap span.t { display: block; text-align: center; word-break: keep-all; }
      .cap b { margin: 0 0.16em; }
      #hook .bg { background: var(--navy); }
      #hk-small { position: absolute; left: 80px; top: 230px; font-size: 60px; font-weight: 800; color: #ffa25c; }
      #hk-big { position: absolute; left: 80px; top: 320px; width: 920px; font-size: 132px; line-height: 1.1; font-weight: 900; letter-spacing: -0.03em; color: #fff; }
      #hk-big span { display: block; }
      .hchip { position: absolute; left: 80px; width: 920px; height: 118px; border-radius: 28px; background: #fff; display: flex; align-items: center; padding: 0 34px; font-size: 54px; font-weight: 800; color: var(--navy); }
      .hchip i { font-style: normal; width: 70px; height: 70px; border-radius: 50%; background: var(--orange); color: var(--navy); font-size: 40px; font-weight: 900; display: flex; align-items: center; justify-content: center; margin-right: 26px; }
      .hchip em { font-style: normal; font-weight: 500; font-size: 36px; color: #4a5266; margin-left: 18px; }
      #hook .cap { background: rgba(255,255,255,0.96); }
      #k-photo svg { display: block; border-radius: 16px; }
      .st svg { position: absolute; left: 17px; top: 6px; }
      #c-title { width: 920px; }
"""

def cap(lid, html):
    return f'<div class="cap" id="cap-{lid}"><span class="t">{html}</span></div>'
def caps(sid):
    return '<div class="caps">\n            ' + "\n            ".join(cap(l, h) for l, h, _ in dict(SCENES)[sid]) + '\n          </div>'
def face(size, mouth, eyes="open", bg="#ffe2c9", extra=""):
    e = {"open": '<circle cx="38" cy="52" r="5" fill="#1b2a4a"/><circle cx="62" cy="52" r="5" fill="#1b2a4a"/>',
         "smile": '<path d="M32 53q6-7 12 0M56 53q6-7 12 0" fill="none" stroke="#1b2a4a" stroke-width="4" stroke-linecap="round"/>',
         "wide": '<circle cx="38" cy="52" r="7" fill="#fff" stroke="#1b2a4a" stroke-width="3"/><circle cx="62" cy="52" r="7" fill="#fff" stroke="#1b2a4a" stroke-width="3"/><circle cx="38" cy="52" r="3" fill="#1b2a4a"/><circle cx="62" cy="52" r="3" fill="#1b2a4a"/>',
         "wink": '<circle cx="38" cy="52" r="5" fill="#1b2a4a"/><path d="M56 53q6-6 12 0" fill="none" stroke="#1b2a4a" stroke-width="4" stroke-linecap="round"/>',
         "sleep": '<path d="M32 52h12M56 52h12" stroke="#1b2a4a" stroke-width="4" stroke-linecap="round"/>'}[eyes]
    m = {"smile": '<path d="M38 68q12 12 24 0" fill="none" stroke="#b3341a" stroke-width="5" stroke-linecap="round"/>',
         "grin": '<path d="M36 66h28q-2 16-14 16t-14-16z" fill="#b3341a"/>',
         "o": '<ellipse cx="50" cy="72" rx="7" ry="9" fill="#b3341a"/>',
         "flat": '<path d="M40 72h20" stroke="#b3341a" stroke-width="5" stroke-linecap="round"/>',
         "small": '<path d="M43 70q7 6 14 0" fill="none" stroke="#b3341a" stroke-width="5" stroke-linecap="round"/>'}[mouth]
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100"><rect width="100" height="100" fill="{bg}"/>'
            '<path d="M14 62q-8-50 36-52q44 2 36 52q-2 14-10 18l-52 0q-8-4-10-18z" fill="#3a2a26"/>'
            '<circle cx="50" cy="56" r="28" fill="#ffd9b8"/><path d="M22 50q6-26 28-24q22-2 28 24q-14-16-28-12q-14-4-28 12z" fill="#3a2a26"/>'
            '<circle cx="30" cy="64" r="5" fill="#ffb3a0" opacity=".7"/><circle cx="70" cy="64" r="5" fill="#ffb3a0" opacity=".7"/>'
            f'{e}{m}{extra}</svg>')
tick = '<div class="tick" id="{id}"><svg width="28" height="28" viewBox="0 0 28 28"><path d="M5 14l6 6 12-13" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" /></svg></div>'
stk = [("최고!", "grin", "smile", "#ffe2c9"), ("헉", "o", "wide", "#dfeaff"), ("좋아요", "smile", "wink", "#e3f5e1"),
       ("ㅋㅋㅋ", "grin", "smile", "#f3e3ff"), ("감사", "small", "smile", "#fff3c4"), ("화이팅", "grin", "open", "#ffdede"),
       ("퇴근", "smile", "open", "#d9f3f5"), ("오케이", "small", "wink", "#ffe2c9"), ("졸려", "flat", "sleep", "#e9e6ff")]
stick_html = "\n              ".join(
    f'<div class="st" style="left: {24 + 157 * (i % 3)}px; top: {24 + 170 * (i // 3)}px; background: {bg}">'
    f'{face(104, m, e, bg).replace("<svg ", "<svg style=\"border-radius:50%\" ")}<em>{lab}</em></div>' for i, (lab, m, e, bg) in enumerate(stk))

def scene(sid, z, inner):
    s, d = SC[sid]
    return f'''      <div id="{sid}" class="clip scene" data-start="{s}" data-duration="{d}" data-track-index="1" data-track-kind="graphics" style="z-index: {z}">
        <div class="bg"></div>
        <div class="inner" id="{sid}-in">
{inner}
          {caps(sid)}
        </div>
      </div>
'''
body = scene("hook", 2, '''          <div id="hk-small">ChatGPT 새 기능</div>
          <div id="hk-big"><span>다 따라갈</span><span>필요 없어요</span></div>
          <div class="hchip" id="hc1" style="top: 640px"><i>1</i>Word<em>가정통신문 다듬기</em></div>
          <div class="hchip" id="hc2" style="top: 776px"><i>2</i>Dots<em>일정 겹침 알림</em></div>
          <div class="hchip" id="hc3" style="top: 912px"><i>3</i>Space<em>같이 쓰는 문서</em></div>
          <div class="hchip" id="hc4" style="top: 1048px"><i>4</i>스티커팩<em>셀카 한 장</em></div>''')
body += scene("word", 3, '''          <div class="badge"><b>1</b>/ 4</div>
          <div class="title"><span>가정통신문도 워드에서</span><span class="o">바로 ChatGPT</span></div>
          <div class="mock">
            <div class="card" id="w-win" data-layout-allow-overflow>
              <div id="w-top">가정통신문.docx — Word</div>
              <div id="w-doc">
                <h4>11월 가정통신문</h4>
                <div class="bar" style="width: 470px"></div>
                <div class="bar" style="width: 400px"></div>
                <div id="w-hl">
                  <div id="w-old" data-layout-allow-overlap data-layout-allow-occlusion>금번 현장체험학습과 관련하여 하기와 같이 안내드리오니…</div>
                  <div id="w-new" data-layout-allow-overlap>체험학습 준비물은 도시락과 물, 두 가지예요.</div>
                </div>
                <div class="bar" style="width: 450px"></div>
                <div class="bar" style="width: 330px"></div>
                <div class="bar" style="width: 420px"></div>
              </div>
              <div id="w-side" data-layout-allow-overflow>
                <h5><span class="gdot"></span>ChatGPT</h5>
                <div id="w-ask">학부모님이 읽기 쉽게 바꿔줘</div>
                <div id="w-ans">문서에 <b>바로 반영</b>했어요.</div>
              </div>
            </div>
          </div>
          <div class="chip" id="w-chip">무료 플랜도 사용 가능</div>''')
body += scene("dots", 4, '''          <div class="badge"><b>2</b>/ 4</div>
          <div class="title"><span>24시간 일하는</span><span class="o">에이전트, Dots</span></div>
          <div class="mock">
            <div class="card" id="d-cal">
              <h5>오늘 일정 <span id="d-run">지켜보는 중</span></h5>
              <div class="ev"><i>2:00</i>4교시 수업</div>
              <div class="ev"><i>4:30</i>학부모 상담</div>
              <div id="d-evwrap">
                <div class="ev"><i>6:00</i>피아노 학원</div>
                <div class="ev"><i>6:30</i>저녁 약속</div>
                <div id="d-clash" data-layout-allow-occlusion><span>일정 겹침</span></div>
              </div>
            </div>
            <div class="card" id="d-phone">
              <div id="d-time">4:52</div>
              <div id="d-date">11월 13일 금요일</div>
              <div id="d-noti">
                <h6><span class="gdot"></span>Dots · 지금</h6>
                <p>피아노 학원과 저녁 약속이 겹쳐요. 옮길까요?</p>
              </div>
            </div>
          </div>
          <div class="chip">요금제별로 순차 제공 중</div>''')
body += scene("space", 5, f'''          <div class="badge"><b>3</b>/ 4</div>
          <div class="title"><span>동료와 같이 쓰는</span><span class="o">ChatGPT Space</span></div>
          <div class="mock">
            <div class="card" id="s-win" data-layout-allow-overflow>
              <div id="s-head">
                <h5>2학기 수업 계획서</h5>
                <div id="s-av">
                  <div class="av" id="s-a1" style="background: #7a4fd0">김</div>
                  <div class="av" id="s-a2" style="background: #1e7a46">박</div>
                  <div class="av" id="s-a3" style="background: #2b579a">서</div>
                </div>
              </div>
              <div class="todo"><div class="box">{tick.format(id="s-t1")}</div>주제 정하기</div>
              <div class="todo"><div class="box">{tick.format(id="s-t2")}</div>활동 순서 짜기</div>
              <div class="todo"><div class="box"></div>준비물 목록 만들기</div>
              <div class="todo" style="border: 0"><div class="box"></div>가정통신문 보내기</div>
              <div id="s-ask"><b>@ChatGPT</b>남은 할 일 나눠줘</div>
              <div class="cur" id="s-k1" data-layout-allow-occlusion><svg width="30" height="30" viewBox="0 0 30 30"><path d="M3 3l9 24 4-10 10-4z" fill="#7a4fd0" stroke="#fff" stroke-width="2" /></svg><span style="background: #7a4fd0">김쌤</span></div>
              <div class="cur" id="s-k2" data-layout-allow-occlusion><svg width="30" height="30" viewBox="0 0 30 30"><path d="M3 3l9 24 4-10 10-4z" fill="#1e7a46" stroke="#fff" stroke-width="2" /></svg><span style="background: #1e7a46">박쌤</span></div>
            </div>
          </div>
          <div class="chip">Pro · Business · Enterprise</div>''')
body += scene("stick", 6, f'''          <div class="badge"><b>4</b>/ 4</div>
          <div class="title"><span>사진 한 장으로</span><span class="o">내 얼굴 스티커팩</span></div>
          <div class="mock">
            <div class="card" id="k-photo">{face(290, "small", "open", "#dfe8f5")}<p>셀카 1장</p></div>
            <svg id="k-arrow" width="90" height="70" viewBox="0 0 90 70"><path id="k-apath" d="M6 35h66M52 12l24 23-24 23" fill="none" stroke="#f27a2b" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" /></svg>
            <div class="card" id="k-grid" data-layout-ignore>
              {stick_html}
            </div>
          </div>
          <div class="chip">이미지 메뉴 › 스티커</div>''')
gi = "\n            ".join(f'<div class="gi"><div class="box">{tick.format(id="c-t%d" % (i + 1))}</div>{a} <i>{b}</i></div>'
                           for i, (a, b) in enumerate([("Word", "추가 기능 설치"), ("Dots", "캘린더 연결"), ("Space", "동료 초대"), ("스티커", "사진 선택")]))
s, d = SC["cta"]
body += f'''      <div id="cta" class="clip scene" data-start="{s}" data-duration="{d}" data-track-index="1" data-track-kind="graphics" style="z-index: 7">
        <div class="bg"></div>
        <div class="inner" id="cta-in">
          <div id="c-title"><span>4가지 설정법,</span><span class="o">PDF로 정리했어요</span></div>
          <div class="card" id="c-guide">
            <h5>무료 PDF 가이드</h5>
            <h4>ChatGPT 새 기능 설정법</h4>
            {gi}
          </div>
          <div id="c-pop">댓글에 ‘가이드’</div>
          <div id="c-sub">남겨주시면 바로 보내드릴게요</div>
        </div>
      </div>
'''
# audio
A = [f'<audio id="bgm" class="clip" src="assets/audio/bgm_long.wav" data-start="0" data-duration="{TOTAL}" data-volume="{0.16 if voice else 0.5}" data-track-index="10"></audio>']
n = 11
def sfx(name, at, vol):
    global n
    A.append(f'<audio id="sfx{n}" class="clip" src="assets/audio/{name}.mp3" data-start="{round(at, 2)}" data-volume="{vol}" data-track-index="{n}"></audio>'); n += 1
for sid in ["word", "dots", "space", "stick", "cta"]:
    sfx("whoosh-short", SC[sid][0] - 0.1, 0.22)
sfx("pop", T["h1"][0], 0.4)
sfx("notification", T["d4"][0] + 1.6, 0.35)
sfx("pop", T["c2"][0], 0.4)
if voice:
    for sid, lines in SCENES:
        for lid, _, _ in lines:
            A.append(f'<audio id="vo-{lid}" class="clip" src="assets/audio/vo/{lid}.wav" data-start="{T[lid][0]}" data-duration="{T[lid][1]}" data-volume="1" data-track-index="{n}"></audio>'); n += 1

js = f'''
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      const T = {json.dumps({k: v[0] for k, v in T.items()})};
      const D = {json.dumps({k: v[1] for k, v in T.items()})};
      const S = {json.dumps({k: v[0] for k, v in SC.items()})};
      const SCN = {json.dumps([[sid, [l[0] for l in lines]] for sid, lines in SCENES])};
      const IN = (sel, t) => tl.fromTo(sel, {{ opacity: 0, y: 50 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }}, t);
      const pop = (sel, t) => {{
        tl.fromTo(sel, {{ scale: 0.3, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, ease: "back.out(3)" }}, t);
        tl.to(sel, {{ rotation: -2, duration: 0.06 }}, t + 0.4);
        tl.to(sel, {{ rotation: 0, duration: 0.3, ease: "elastic.out(1.2,0.3)" }}, t + 0.46);
      }};
      SCN.forEach(([sid, ids]) => ids.forEach((id, i) => {{
        tl.fromTo("#cap-" + id, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, T[id]);
        if (i < ids.length - 1) tl.to("#cap-" + id, {{ opacity: 0, duration: 0.12 }}, T[ids[i + 1]] - 0.12);
      }}));
      /* hook */
      tl.fromTo("#hk-small", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.25 }}, 0.02);
      tl.fromTo("#hk-big span", {{ scale: 0.3, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, stagger: 0.14, ease: "back.out(2.4)", transformOrigin: "0% 50%" }}, T.h1);
      tl.fromTo(".hchip", {{ opacity: 0, x: -60 }}, {{ opacity: 1, x: 0, duration: 0.35, stagger: Math.min(0.5, D.h2 / 5), ease: "power3.out" }}, T.h2 + 0.2);
      /* word */
      IN("#word-in", S.word);
      tl.fromTo("#w-side", {{ x: 380 }}, {{ x: 0, duration: 0.5, ease: "power3.out" }}, T.w2 + 0.3);
      tl.fromTo("#w-ask", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.3 }}, T.w3 + 0.8);
      tl.fromTo("#w-new", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35 }}, T.w4 + 0.6);
      tl.fromTo("#w-old", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.3 }}, T.w4 + 0.6);
      tl.fromTo("#w-ans", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.3 }}, T.w4 + 1.0);
      tl.fromTo("#w-chip", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, T.w5);
      /* dots */
      IN("#dots-in", S.dots);
      tl.fromTo("#d-phone", {{ opacity: 0, x: 60 }}, {{ opacity: 1, x: 0, duration: 0.4 }}, T.d2 + 0.2);
      tl.fromTo("#d-run", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, T.d3 + 0.8);
      tl.fromTo("#d-clash", {{ opacity: 0, scale: 1.08 }}, {{ opacity: 1, scale: 1, duration: 0.3 }}, T.d4 + 0.5);
      tl.fromTo("#d-noti", {{ opacity: 0, y: -60 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: "back.out(1.6)" }}, T.d4 + 1.6);
      /* space */
      IN("#space-in", S.space);
      tl.fromTo("#s-a2", {{ scale: 0 }}, {{ scale: 1, duration: 0.3, ease: "back.out(2)" }}, T.s2 + 1.6);
      tl.fromTo("#s-a3", {{ scale: 0 }}, {{ scale: 1, duration: 0.3, ease: "back.out(2)" }}, T.s2 + 1.9);
      tl.fromTo("#s-k1", {{ x: 700, y: 120, opacity: 0 }}, {{ x: 360, y: 190, opacity: 1, duration: 0.8, ease: "power2.inOut" }}, T.s2 + 1.6);
      tl.fromTo("#s-t1", {{ scale: 0 }}, {{ scale: 1, duration: 0.25, ease: "back.out(3)" }}, T.s3 + 0.4);
      tl.to("#s-k1", {{ x: 480, y: 265, duration: 0.8, ease: "power2.inOut" }}, T.s3 + 0.8);
      tl.fromTo("#s-k2", {{ x: 860, y: 520, opacity: 0 }}, {{ x: 600, y: 340, opacity: 1, duration: 0.8, ease: "power2.inOut" }}, T.s3 + 0.2);
      tl.fromTo("#s-t2", {{ scale: 0 }}, {{ scale: 1, duration: 0.25, ease: "back.out(3)" }}, T.s3 + 1.8);
      tl.to("#s-k2", {{ x: 660, y: 410, duration: 0.9, ease: "power2.inOut" }}, T.s3 + 2.0);
      tl.fromTo("#s-ask", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.3 }}, T.s4);
      /* sticker */
      IN("#stick-in", S.stick);
      tl.fromTo("#k-apath", {{ strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.5 }}, T.k2 + 1.2);
      tl.fromTo("#k-grid .st", {{ scale: 0, rotation: -12 }}, {{ scale: 1, rotation: 0, duration: 0.35, stagger: Math.min(0.2, D.k3 / 12), ease: "back.out(2.2)" }}, T.k3);
      /* cta */
      IN("#cta-in", S.cta);
      tl.fromTo("#c-guide .tick", {{ scale: 0 }}, {{ scale: 1, duration: 0.25, stagger: 0.3, ease: "back.out(3)" }}, T.c1 + 0.6);
      pop("#c-pop", T.c2);
      tl.fromTo("#c-sub", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, T.c3);
      window.__timelines["main"] = tl;
      tl.seek(0);
'''
html = f'''<!doctype html>
<html lang="ko" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="assets/gsap.min.js"></script>
    <style>{css}    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
{body}
      {chr(10).join("      " + a for a in A).strip()}
    </div>
    <script>{js}    </script>
  </body>
</html>
'''
open(os.path.join(ROOT, "index.html"), "w").write(html)
json.dump({"total": TOTAL, "lines": T, "scenes": SC}, open(os.path.join(ROOT, "tools", "timing.json"), "w"), indent=1)
print("total", TOTAL, "voice", voice)
