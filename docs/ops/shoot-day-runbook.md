# 촬영일 런북 (3분 영상)

**목적:** 스토리보드([`demo-video-storyboard.md`](./demo-video-storyboard.md))를 **명령 순서**로 고정.  
**갱신:** 2026-09-04  
> **리허설 1회 완료 (2026-08-14).** 명령 순서 재현 · `demo` PASSED `acc=0.8500` · sanity 3종 FAILED ·
> 위반 6종 REJECTED · A/B 완결 · 증적 줄.  
> **리허설 보강 (2026-08-21).** Windows 본편은 **`pwsh`(PowerShell 7)** 로 통일 · `proof_ab.ps1` 포팅 ·
> UI·생존 API·구간별 해설·EuroSAT/골든셋·용어를 이 문서에 모음. 한글 깨짐은 5.1+UTF-8 스크립트 조합 —
> `pwsh` 로 해소 실측.

**촬영일: 2026-08-23 (확정).** 8/24 편집·업로드 → URL 확보.  
**A/B:** `scripts/proof_ab.ps1` — 본편 PowerShell. 자막은 **§2-A만** (같은 답·편차 수치 금지).  
**SD-008:** 데모 골든 N=40은 홀드아웃 분할. 게이트 자막에 「학습 데이터 기준」만 쓰지 않는다.

---

## 0. 촬영 30분 전

```powershell
cd C:\Users\wjsto\pjt\capnet
docker compose down -v          # ← -v 가 없으면 촬영 30분 전에 막힌다. 아래 참조
docker compose up --build -d
docker compose logs migrate --tail 5    # "완료 — 18개 적용" 또는 "적용할 것 없음"
docker compose ps                       # core·node Up · postgres healthy · migrate 는 Exited(0) OK
# health
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8001/health
```

> **명령은 `docker compose`(공백).** `compose` alone · `doccker` 는 Windows 에서 「내부 명령이 아닙니다」.
>
> **`-v` 를 빠뜨리면 `migrate` 가 `0005` 에서 멈춘다.** `down` 만 하면 볼륨이 남아 initdb 가 안 돌고,
> placeholder 증서 가드에 걸린다. `down -v` 후 다시 `up`.
>
> **`ERR_CONNECTION_REFUSED` on :8000** — `up` 끝나기 전·Core 미기동. `docker compose ps` 에 core `Up` 확인 후
> 브라우저 새로고침.

### 0-A. 왜 Docker · 무엇을 올리나 (내레이션용)

| 단계 | 하는 일 | 왜 |
|------|---------|-----|
| Docker Compose | 앱을 PC에 직접 설치하지 않고 **컨테이너**로 Core·Node·Postgres를 한 명세로 기동 | 심사·재현이 같음. Python/Postgres 버전을 맞출 필요 없음 |
| `down -v` | 컨테이너 + **DB 볼륨** 삭제 | 시연 전 **깨끗이** — 옛 DB면 migrate/시드가 꼬임 |
| `up --build -d` | 이미지 빌드 후 백그라운드 기동 | postgres → migrate → core:8000 → Node 3대 |
| migrate | 스키마 세대·제약을 DB에 적용 | 잘못된 조합은 나중에 **DB가** 거절 |
| health | API가 실제로 응답하는지 | 포트만 열린 것과 구분 |

컨테이너 = 앱+의존성을 상자에 고정. Compose = 여러 상자를 네트워크·순서로 묶음.  
제품이 Docker인 것이 아니라 **배포·재현 수단**이다.

### 0-B. 터미널 · 한글 (촬영 전 필수)

- **Windows Terminal** + **PowerShell 7 (`pwsh`)** 권장. 글꼴 **Cascadia Mono**.
- 스크립트(`demo.ps1` 등)는 UTF-8(BOM 없음). **Windows PowerShell 5.1**은 CP949로 읽어 `증적`→`以묎컻` 처럼 깨진다.
- `chcp 65001` 만으로는 부족할 때가 많다 → **`pwsh -File …`** 으로 실행 (2026-08-21 실측 해소).
- 버전 확인: `$PSVersionTable.PSVersion` · `pwsh -NoLogo -Command '$PSVersionTable.PSVersion'`
- Raster Fonts 금지. □ 는 글꼴 · `以묎컻` 는 인코딩.

### 0-C. UI URL (선택 컷 · 생존 확인)

| URL | 용도 |
|-----|------|
| http://127.0.0.1:8000/ui/nodes.html | 함대 · 생존·증서 |
| http://127.0.0.1:8000/ui/call.html | 능력 호출 (Agent 미지정 · Core 중개) |
| http://127.0.0.1:8000/health | Core |
| http://127.0.0.1:8001/health | Node m-team (gate-runner) |

강제 모드가 아니면 UI 키 없이 데모 compose 로 열린다. 촬영 본편은 터미널이 본체, UI는 「능력만 요청」 보조 컷.

- 터미널: 어두운 테마 · 폰트 **18pt+** · 창 가로로 넓게  
- OBS: 1080p · 자막 레이어. **전체 화면 위주** · 2분할은 call↔증적 잇는 짧은 컷만  
- `apps/node/weights/eurosat_scratch.safetensors` · `_b` (A/B용) 존재 확인

---

## 1. 타임라인 ↔ 명령 (본편 복붙)

작업 디렉터리: `cd C:\Users\wjsto\pjt\capnet`  
스크립트는 **`pwsh -ExecutionPolicy Bypass -File …`** (아래는 짧게 `pwsh -File`).

| 초 | 보여줄 것 | 명령 / 화면 |
|----|-----------|-------------|
| 0–10 | 로고·한 줄 | 슬라이드. 예: **능력을 요청한다.** |
| 10–20 | 문제 한 장 | 슬라이드. REST 1대 vs 자원 여러 대 · Capability 요청 (IP 몰라도 ≠ 아무 데서나) |
| 20–45 | compose + **생존** | `docker compose ps` 후 아래 §1-B. UI `nodes.html` 가능 |
| 45–75 | 실게이트 + 사이클 | `pwsh -File scripts\demo.ps1` — **PASSED · acc=0.8500** 에서 잠깐 정지. Node URL 없음 |
| (컷) | sanity | `pwsh -File scripts\sanity.ps1` — 3종 **FAILED** = 성공 |
| 75–105 | Task 완주 | **같은 demo.ps1 후반** (재실행 불필요). `label=` · `demo OK` |
| 105–150 | 위반 6종 | `pwsh -File scripts\demo_violations.ps1` — `NOTICE REJECTED` ×6 · 제약명 천천히 |
| 150–160 | A/B (UC-7) | `pwsh -File scripts\proof_ab.ps1` — 자막 **§2-A만** |
| 160–170 | 증적 + 경계 | **새 명령 아님** — demo.ps1 **맨 끝 두 줄**을 크게 (편집 컷). 필요 시 demo만 재실행 |
| 170–180 | GitHub | https://github.com/gncorpseo-commits/capnet · **README** 보이게 |

> **160–170은 demo를 두 번 설명하는 것이 아니다.** 45–105에서 이미 나온 출력의 **뒷부분만**
> 자막·화면을 「증적·경계」에 맞춰 다시 보여주는 편집 구간이다.

### 1-B. 생존 상태 (20–45초)

```powershell
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/v1/nodes-liveness | ConvertTo-Json -Depth 5
```

어느 기기가 살아 있는지(`is_fresh`)·바쁜지(`availability`).  
(구) `curl :8000/v1/nodes-liveness` 와 동일 목적.

### 1-C. 구간별 성공 신호

| 스크립트 | 성공 신호 |
|----------|-----------|
| `demo.ps1` | `PASSED` `acc=0.8500` · `demo OK` · `label=` · **증적**·**경계** 두 줄 |
| `sanity.ps1` | constant/random/invalid 모두 `status=FAILED` · `sanity OK` |
| `demo_violations.ps1` | `NOTICE: TESTn REJECTED` **6건** · `ROLLBACK` |
| `proof_ab.ps1` | A·B `PASSED` · `A(…) →` / `B(…) →` · 주의문. `AGREE`/`DISAGREE`는 **1건 관측**일 뿐 |

**160–170 화면에 나와야 하는 두 줄** (형태):

```text
증적: assignment=… node=… agent=… status=SUCCEEDED
경계: 신뢰도메인 task=team -> node=team · 티어 capability=M <= node_max=M
```

첫 줄 = 무엇이 돌았나 · 둘째 줄 = 왜 거기서 돌아도 되는가 (배정 시 DB 스냅샷).

---

## 1-D. 데모 데이터 · 골든셋 · 라벨 (자막·내레이션)

정본: [`../spec/golden/image-classify-v1.md`](../spec/golden/image-classify-v1.md).

**EuroSAT** — 위성 RGB를 땅 이용 유형으로 나누는 공개 데이터. 능력 `image.classify@1`은 **10라벨 closed set**.

| 라벨 | 쉬운 말 |
|------|---------|
| `annual_crop` | 연작·한해살이 작물 밭 |
| `forest` | 숲 |
| `herbaceous_vegetation` | 초본 식생 |
| `highway` | 큰 도로 |
| `industrial` | 공업 |
| `pasture` | 목초지 |
| `permanent_crop` | 다년생 작물 |
| `residential` | 주거 |
| `river` | 강 |
| `sea_lake` | 바다·호수 |

`proof_ab` / `demo` 의 `label=annual_crop` = 그 케이스 한 장의 분류 결과(예: `ic1-0001` 정답도 annual_crop).

**골든셋** — 정답이 붙은 시험 이미지 묶음. Agent를 라우팅하기 전 **게이트 채점지**.  
데모 N=40 · team **gate-runner**에서만 채점 · 문턱은 능력에 **선언**(acc≥0.68 등, 측정 자동최적 아님).  
사전학습 가중치 없음(scratch).

**짧은 자막 예**

> 데모는 EuroSAT 위성 사진을 10가지 땅 유형으로 나눕니다.  
> 골든셋은 정답이 있는 시험 이미지입니다. 선언한 하한을 넘겨야 함대에 배정됩니다.

---

## 1-E. 스크립트가 하는 일 (리허설 Q&A)

### demo.ps1

Core health → scratch Agent 등록 → gate-runner에서 골든셋 채점 → 실게이트 finish(`dummy=false`) →
바인딩 → Task(Core 중개, Node 주소로 실행하지 않음) → 결과·**증적**·**경계**.

### sanity.ps1

**같은** `score_gate` 채점기. mode를 **미리** constant(항상 같은 라벨) / random / invalid(허용 밖 라벨)로
고정한 뒤 문턱 미달 → **FAILED**. FAILED가 성공. Task/DB 배정 경로 아님 · 촬영 컷용 바닥 검사.  
문턱 = `golden_metrics`에 **선언한 합격선**(declared service level).

### demo_violations.ps1 (M25)

Postgres에 잘못된 INSERT/UPDATE 6번 → **FK가 REJECTED** → `ROLLBACK`. 앱 if 아님.

| # | 한 줄 |
|---|--------|
| 1 | 게이트 **미통과** Agent로 **assignment**(배정 행) INSERT → 거절 |
| 2 | **team** Task를 **public** Node 스냅샷으로 배정 → 거절 (`team`/`tenant`/`public` — private 이름 없음) |
| 3 | **L** 능력을 **S** Node에 → 거절. 티어는 S&lt;M&lt;L(작음&lt;중간&lt;큼). Low/Medium/Special 아님 |
| 4 | **lease**(짧은 실행 허가) 있는 채 Node 티어 강등 → 거절 |
| 5 | READY인데 가중치 **sha256 지문**만 교체 → 거절 (전자서명 아님 · 파일 무결성 지문) |
| 6 | PASSED **gate_run**을 사후 훼손하고 통과 증서만 남기기 → 거절 |

**assignment** = Task를 특정 Node·Agent에 맡긴 DB 행.  
**스냅샷** = 배정 순간의 도메인·티어를 그 행에 복사한 값.

### proof_ab.ps1 (UC-7)

A·B 각각 실게이트 PASSED → 동일 `caseId`를 `requestedAgentId`로 교차 Task → 둘 다 COMPLETED.  
**증명:** 사슬 위에서 Agent **교체 배정**이 된다.  
**비증명:** 항상 같은 라벨 · 편차&lt;0.05. 화면에 `AGREE`가 나와도 자막은 §2-A.

---

## 1-A. 촬영에 **넣지 않는** 것 (2026-08-16)

단계 5–6 으로 실행기가 늘었다. `scripts/` 에 데모가 넷 더 있다 —
`text_demo.sh` · `embed_demo.sh` · `series_demo.sh` · `image_embed_demo.sh`.

**넷 다 촬영에 넣지 않는다.** 이유는 셋이다.

1. **3분에 안 들어간다.** 지금 타임라인이 이미 180초를 다 쓴다
2. **전부 `.sh` 다.** 촬영은 PowerShell 이고, 이 넷은 PowerShell 판이 없다
3. **품질을 주장하지 않는 능력들이다** (`quality_profile='none'`). 화면에 띄우면
   시청자는 성능을 본 것으로 읽는다 — 자막으로 막기 어려운 오해다

영상의 주장은 그대로다: **능력만 요구 · 승인 도메인 안 라우팅 · 실행 증적.**
「능력이 여럿이다」는 보고서에서 글로 말하고, 영상은 한 능력으로 사슬을 보인다.

> 심사위원이 저장소를 열면 이 데모들이 보인다. 그건 문제가 아니다 —
> 각 스크립트가 **스스로 「무엇을 주장하지 않는지」를 마지막 줄에 출력**한다.

---

> CapCut에서 자르기·텍스트 넣는 법: [`capcut-edit-guide.md`](./capcut-edit-guide.md)

## 2. 자막 번인 문장 (복붙)

1. 능력만 요구하면 됩니다. 어떤 AI가, 어느 기계에서 도는지는 몰라도 됩니다.  
2. 그런데 "몰라도 된다"는 "아무 데서나 돈다"가 아닙니다.  
3. 승인하지 않은 신뢰 도메인으로는 **DB가 라우팅을 거절**합니다.  
4. 앱은 GPU 주소를 통신 계약으로 삼지 않습니다. 계약은 Capability입니다. (구: 「주소를 몰라도」만 — 실무 반박 주의)  
5. 노드도 Core가 배정하지 않은 일은 거부합니다.  
6. 그리고 누가·무엇으로·언제 실행했는지 **증적이 남습니다**.  
7. **어느 등급에서 어느 등급으로 갔는지도 함께 남습니다** — 배정 시점에 DB가 검증한 값입니다.  
8. 위반은 앱 if가 아니라 PostgreSQL이 REJECTED.  
9. CapNet OSS — compose로 재현. (GitHub README 컷)

7번은 **160–170초 「경계」 줄과 붙여서** 쓴다.

### 2-A. A/B 구간(150–160) 자막 — **확정 (안 B)**

> **A-1.** 같은 능력으로 **다른 에이전트에 교체 배정**됩니다. 계약을 통과한 것만 후보가 됩니다.  
> **A-2.** 다만 **두 에이전트가 같은 답을 낸다고는 말하지 않습니다.**

**A-2 를 빼지 않는다.** 시간 모자라면 **A/B 구간 전체**를 들어낸다.

#### 금지

| 금지 문구 | 왜 |
|---|---|
| Within · 편차 0.05 이내 | 하한형 게이트가 쌍 편차를 유계로 못 만듦 (SD-009) |
| \|Δacc\|≈0.047 · n300 \|diff\|≤0.05 | 누출 골든셋 수치 |
| 같은 답 · 동일한 결과 · 대체 가능 | 등가는 계약 보장 아님 (D17) |

`proof_ab.ps1` / `.sh` 가 보여 주는 것은 **교체 배정이 사슬 위에서 완결된다**뿐.  
**게이트 acc 숫자를 비교 자막으로 쓰지 않는다.**

---

## 3. 촬영 후

- [ ] mp4 H.264 1080p · ≤200MB · ≤3분  
- [ ] 음소거로 1회 재생해 자막만으로 이해되는지 확인  
- [x] YouTube **일부 공개** 업로드 → https://youtu.be/RjFiGpmLTbk  
- [ ] 원본 파일도 로컬 보관

---

## 4. 양식 이식 (영상과 병렬 가능)

1. 주최 양식 열기 · 회색 가이드 삭제  
2. [`contest-report-form-draft.md`](./contest-report-form-draft.md) 복사 (본문 ≤5p)  
3. 붙임1 SBOM · 붙임2 유형3 + raw 가중치 URL  
4. PDF · 포털 zip

---

## 촬영 전 기계 점검

```bash
bash scripts/run_tests.sh                 # 단위 + 골든셋 정합 + 출품 점검
bash scripts/clean_room.sh                # 빈 볼륨 — 촬영 환경과 같은 조건
bash scripts/prod_room.sh                 # 강제 프로파일
python3 scripts/check_submission.py       # 패키징 직전 (워킹트리 깨끗함 포함)
bash scripts/migrate.sh status            # 스키마 세대 확인 (18)
```

`clean_room`·`prod_room` 은 `.sh` 라 **WSL 에서** 돌린다 — 촬영 전날 한 번이면 된다.

> **검사 수는 계속 늘어난다.** 단계 6 실행기를 하나 얹을 때마다 단위 검사가 붙기 때문이다.
> **숫자가 위와 달라도 그 자체는 이상이 아니다** — 봐야 할 것은
> 「전부 통과」와 `acc=0.8500` 이다. 이 표를 「같아야 하는 값」으로 읽지 않는다.
>
> **둘 다 2026-09-04 에 이 WSL 에서 실제로 돌았다** — 8·9회차는 `docker info` 가 실패해
> 두 번 「못 봤다」로 남겼던 자리다.
>
> | 무엇 | 결과 | 비고 |
> |---|---|---|
> | `clean_room` | **통과 9 · 실패 0** | 실게이트 `acc=0.8500 f1=0.8344` |
> | `prod_room` | **통과 51 · 실패 0** | 옛 「27/27」은 낡았다 — #205 가 라우트를 5→24 로 늘렸다 |
>
> 첫 실행은 **49/2** 였다. 프로브가 `node_id` 를 빼먹어 두 라우트가 422 로 떨어진 것이고,
> 채우니 둘 다 401 이다 — **인증은 멀쩡했고 프로브가 그 둘을 재지 못했다.**

`check_submission.py` 가 보는 것: 금지 산출물·필수 가중치·라이선스·SBOM·시크릿·골든셋 등.
**영상·촬영·포털은 이 검사 밖이다.**
