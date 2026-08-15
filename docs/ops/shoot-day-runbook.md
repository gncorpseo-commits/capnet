# 촬영일 런북 (3분 영상)

**목적:** 스토리보드([`demo-video-storyboard.md`](./demo-video-storyboard.md))를 **명령 순서**로 고정.  
**갱신:** 2026-08-15  
> **리허설 1회 완료 (2026-08-14).** 아래 타임라인 명령을 순서대로 돌려 전부 재현했다 —
> `demo.sh` PASSED `acc=0.8500` · sanity 3종 FAILED · 위반 **6종 REJECTED** ·
> `proof_ab.sh` A/B 둘 다 완결 · 증적 줄 출력. 그 과정에서 **`demo.ps1`·`smoke_w1.ps1` 이
> `arch` 없이 Agent 를 등록해 HTTP 400 이 나는 것**을 찾아 고쳤다 (G5 이후 회귀).
> 촬영은 PowerShell 로 하므로 `.sh` 만 도는 검증 3종에는 안 걸리던 구멍이었다.

**촬영일: 2026-08-23 (확정).** 8/24 편집·업로드 → URL 확보. 밀 수 없다 — 영상이 보고서를 막는다.  
**A/B: 화면은 촬영 가능, 자막은 미확정** (2026-08-08 `scripts/proof_ab.sh`). Agent A·B가 각각 실게이트를 통과했고, 동일 case를 `requestedAgentId`로 교차 배정해 둘 다 완결됐다 — **교체가 된다**는 사실은 그대로다. 다만 **편차 수치를 자막에 쓸 수 없다**(§2-A). 150–160초만 A/B에 쓰고, 160–170초는 **증적·경계**로 돌렸다.  
**SD-008:** 데모 골든 N=40은 **홀드아웃 분할** (`selection.split=holdout`). 커밋 가중치 A는 아직 `train_images=27000`(전수) — 게이트 자막은 「홀드아웃 케이스 · 가중치는 전수 학습(재학습 전)」 또는 HOLDOUT=1 재학습 후 「홀드아웃」만. 누출 유출 문구("학습 데이터 기준"만)는 쓰지 않는다.

---

## 0. 촬영 30분 전

```powershell
cd C:\Users\wjsto\pjt\capnet
docker compose down -v          # ← -v 가 없으면 촬영 30분 전에 막힌다. 아래 참조
docker compose up --build -d
docker compose logs migrate --tail 5    # "완료 — 17개 적용" 을 눈으로 확인하고 넘어간다
# health
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8001/health
```

> **`-v` 를 빠뜨리면 `migrate` 가 `0005` 에서 멈춘다.** 2026-08-15 에 실제로 겪었다.
> `docker compose down` 은 컨테이너·네트워크만 지우고 **볼륨은 남긴다.** 그러면 postgres 가
> 기존 데이터 디렉터리로 뜨고, `initdb`(= `schema.sql` + `seed.sql`)가 **아예 돌지 않는다.**
> 옛 볼륨에 남아 있던 placeholder 증서를 `0005` 의 가드가 잡아 이렇게 멈춘다:
>
> ```text
> 실패 0005_seed_agent_not_routable.sql: placeholder 가중치 Agent 에 라우팅 증서가 아직 5 건 남아 있다
> ```
>
> 가드가 옳다 — 통과시키면 dummy 라우팅이 되살아난다(SD-015). 고칠 것은 볼륨이다.
> 이미 이 상태라면 `docker compose down -v` 후 다시 기동한다.

- 터미널: 어두운 테마 · 폰트 **18pt+** · 창 가로로 넓게  
- OBS/클립챔프: 1080p · 자막 레이어 준비  
- `apps/node/weights/eurosat_scratch.safetensors` 존재 확인

---

## 1. 타임라인 ↔ 명령

| 초 | 보여줄 것 | 명령 / 화면 |
|----|-----------|-------------|
| 0–10 | 로고·한 줄 | 슬라이드 (녹화 시작) |
| 10–20 | 문제 한 장 | 슬라이드 |
| 20–45 | compose 기동 + **생존 상태** | `compose up` 후 `curl :8000/v1/nodes-liveness` — 어느 기기가 살아 있고 얼마나 바쁜지 |
| 45–75 | 실게이트 + **사이클** | `scripts/demo.ps1` — **PASSED · dummy=false** 정지. **사용자는 Core만 호출한다** — 노드 주소가 명령 어디에도 없다는 점을 짚는다 |
| (컷) | sanity | `scripts/sanity.ps1` — 3종 FAILED (짧게 잘라 넣기 가능) |
| 75–105 | Task 완주 | `demo.ps1` 후반 Task 성공 출력 |
| 105–135 | 위반 1–3 | `scripts/demo_violations.ps1` — `NOTICE REJECTED` / 제약명 **천천히** |
| 135–150 | 위반 4–6 | 같은 스크립트 나머지 · 표 슬라이드 병치 |
| 150–160 | **A/B 교체 (UC-7)** | **PowerShell 판이 없다** — WSL 에서 `bash scripts/proof_ab.sh` 로 **미리 녹화한 클립**을 끼운다. 자막은 **§2-A 를 그대로** 쓴다 (「같은 답」이라고 말하지 않는다) |
| **160–170** | **증적 + 경계** | `demo.ps1` 마지막 **두 줄**. 증적(assignment·node·agent·status) 아래에 **경계** 줄이 붙는다 — 아래 참조 |
| 170–180 | GitHub | https://github.com/gncorpseo-commits/capnet · README 5분 기동 |

> **촬영은 PowerShell 이다.** 이 표에 `bash scripts/…` 가 섞여 있었다 (45–75 · 150–160).
> Windows 에는 `bash` 가 없어 촬영 중에 그대로 막힌다 — `.sh` 만 도는 검증 3종에는 안 걸리던
> 모양이고, `arch` 누락(G5)·`demo.ps1` finish 400(#76)과 **같은 종류의 사고**다.
>
> 45–75 는 `demo.ps1` 로 바꿨다(있다). **150–160 은 바꿀 수 없다 — `proof_ab.ps1` 이 없다.**
> `scripts/` 의 PowerShell 은 열 개뿐이고 그중 A/B 를 사슬 위에서 도는 것은 없다
> (`compare_ab.ps1` 은 점수 JSON 두 개를 비교하는 **사슬 밖** 도구다). 그래서 그 칸만
> **미리 녹화한 클립**으로 처리한다. 촬영 중에 WSL 로 전환하지 않는다 — 화면이 바뀌면
> 「같은 환경에서 이어진다」가 깨진다.

**160–170 에 화면에 나와야 하는 두 줄** (2026-08-15 `clean_room` · `prod_room` 실측, 양쪽 동일):

```text
증적: assignment=185e97cc-… node=00000000-…-030 agent=430779ee-… status=SUCCEEDED
경계: 신뢰도메인 task=team -> node=team · 티어 capability=M <= node_max=M
```

**둘째 줄이 제품 주장 그 자체다.** 첫 줄은 「무엇이 돌았나」이고, 둘째 줄은 「**왜 거기서 돌아도
되는가**」다 — 그 네 값은 앱이 계산한 게 아니라 배정 시점에 DB 가 복합 FK 로 검증해 박아 둔
스냅샷이다. 자막 3번(「DB 가 라우팅을 거절합니다」)의 **긍정형 증거**이므로 같이 잡는다.

---

## 2. 자막 번인 문장 (복붙)

1. 능력만 요구하면 됩니다. 어떤 AI가, 어느 기계에서 도는지는 몰라도 됩니다.  
2. 그런데 "몰라도 된다"는 "아무 데서나 돈다"가 아닙니다.  
3. 승인하지 않은 신뢰 도메인으로는 **DB가 라우팅을 거절**합니다.  
4. 사용자는 Core만 호출합니다. 노드 주소를 알지 못하고, 알 필요도 없습니다.  
5. 노드도 Core가 배정하지 않은 일은 거부합니다.  
6. 그리고 누가·무엇으로·언제 실행했는지 **증적이 남습니다**.  
7. **어느 등급에서 어느 등급으로 갔는지도 함께 남습니다** — 배정 시점에 DB가 검증한 값입니다.  
8. 위반은 앱 if가 아니라 PostgreSQL이 REJECTED.  
9. CapNet OSS — compose로 재현.

7번은 **160–170초 「경계」 줄과 붙여서** 쓴다. 3번이 「거절한다」는 부정형 주장이고,
7번은 같은 규칙이 **통과시킨 경우**를 보여 준다 — 둘이 한 쌍이라야 「막기만 하는 게 아니라
판정한다」가 된다.

### 2-A. A/B 구간(150–160) 자막 — **미확정**

여기 문장은 아직 **정하지 않았다.** 스토리보드에 남아 있는 「n=300 · |Δacc|≈0.047 · Within」은
**누출된 골든셋으로 잰 값**이라 무효다(roadmap §1.2). 홀드아웃 n=300 재측정은 **0.0967 ·
EXCEEDS** 이고, 애초에 D17 이후 **등가성은 계약 보장이 아니라 관측값**이다.

그러므로 이 구간 자막은 「같은 답이 나온다」·「편차 0.05 이내」로 **쓸 수 없다.**
문구 확정은 제품 주장이라 Decision 대기 — `docs/bridge/inbox-cursor.md` 참조.
**미확정 상태로 촬영일을 맞지 않는다.**

---

## 3. 촬영 후

- [ ] mp4 H.264 1080p · ≤200MB · ≤3분  
- [ ] 음소거로 1회 재생해 자막만으로 이해되는지 확인  
- [ ] YouTube **비공개** 업로드 → URL을 `contest-report-form-draft.md` `[TODO: YouTube URL]`에 기입  
- [ ] 원본 파일도 로컬 보관 (포털이 파일 요구할 때)

---

## 4. 양식 이식 (영상과 병렬 가능)

1. 주최 양식 `…결과보고서_접수번호(팀명).docx|hwp` 열기  
2. 회색 가이드 페이지 삭제  
3. [`contest-report-form-draft.md`](./contest-report-form-draft.md) 문장 복사 (본문 ≤5p)  
4. 붙임1 SBOM · 붙임2 유형3 + raw 가중치 URL  
5. PDF 동시 저장 → 포털 zip

---

## 촬영 전 기계 점검

```bash
bash scripts/run_tests.sh                 # 단위 68 + 골든셋 정합 + 출품 점검 21
bash scripts/clean_room.sh                # 빈 볼륨 9종 — 촬영 환경과 같은 조건
bash scripts/prod_room.sh                 # 강제 프로파일 27종
python3 scripts/check_submission.py       # 패키징 직전 (워킹트리 깨끗함 포함)
bash scripts/migrate.sh status            # 스키마 세대 확인 (17)
```

**2026-08-15 실측 (`main` = `ec9db6b`):** `run_tests` **68** · `check_submission` **21/21** ·
`clean_room` **9/9** · `prod_room` **27/27** · 골든 `acc=0.8500` `f1=0.8344`.
`clean_room`·`prod_room` 은 `.sh` 라 **WSL 에서** 돌린다 — 촬영 전날 한 번이면 된다.

`check_submission.py` 가 보는 것: 금지 산출물 미동봉 · 필수 가중치 유지 · 라이선스 4종 ·
사전학습 미사용 선언(meta) · 의존성 THIRD-PARTY 등재 · 시크릿 · 상대 링크 · 골든셋 정본 1개 ·
골든셋 sha 정합 · 패키지 크기. **영상·촬영·포털은 이 검사 밖이다.**
