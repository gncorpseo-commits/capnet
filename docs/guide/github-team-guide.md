# CapNet 팀 GitHub 사용 표준 가이드

**문서 ID:** GN_20260803_github_guide  
**버전:** 1.3 · 2026-08-08  
**저장소:** https://github.com/gncorpseo-commits/capnet  
**대상:** 팀 지엔 (`finn` / `toma` / `pl` / `master`)  
**관련:** [Contest MVP](https://github.com/gncorpseo-commits/capnet/blob/main/docs/ops/Contest_MVP_2026.md) · [STATE.md](https://github.com/gncorpseo-commits/capnet/blob/main/STATE.md) · [context-handoff](https://github.com/gncorpseo-commits/capnet/blob/main/docs/context-handoff.md) · [INDEX](https://github.com/gncorpseo-commits/capnet/blob/main/docs/INDEX.md)  
**저장소 사본:** 동일 내용 → 레포 `docs/guide/github-team-guide.md` · `CONTRIBUTING.md`

---

## 0. 한 줄 규칙

> **이슈 없이 코딩하지 않는다 → `finn/*` · `toma/*` · `pl/*` 브랜치에서 작업 → PR → 명목상 상호 승인 → `master`가 `main` 머지 최종 책임.**

---

## 1. 역할

| 역할 | GitHub / git | 책임 |
|------|--------------|------|
| **master** | 사람 역할 (브랜치 이름 아님) | 우선순위, PR 최종 머지, 출품 판단, 규칙 예외 승인 |
| **finn** | 커밋 `user.name=finn` | 맡은 이슈·PR, 다른 작업자 PR 명목 리뷰 |
| **toma** | 커밋 `user.name=toma` | 맡은 이슈·PR, 다른 작업자 PR 명목 리뷰 |
| **pl** | 커밋 `user.name=pl` | 맡은 이슈·PR, 다른 작업자 PR 명목 리뷰 (**finn/toma와 동급**) |

- 작업 author 풀: **finn · toma · pl** (셋 동급). **master**는 merge·최종 판단만.
- 기본 브랜치 이름은 **`main`** (`master` 역할과 혼동 금지).
- GitHub **로그인 계정이 하나**여도 된다. Approve는 계정 단위이므로 **명목 승인(코멘트)** 으로 상호 리뷰를 기록한다.
- 계정이 둘이 되면 그때부터 실제 Approve + branch protection을 켠다.

---

## 2. 커밋 서명 (finn / toma / pl 스위칭)

전역 `git config --global` 은 **바꾸지 않는다** (서로 덮어씀).

### 방법 A — 커밋 한 번에만 지정 (권장)

```bash
git -c user.name=finn -c user.email=finn@users.noreply.github.com commit -m "메시지"
git -c user.name=toma -c user.email=toma@users.noreply.github.com commit -m "메시지"
git -c user.name=pl -c user.email=pl@users.noreply.github.com commit -m "메시지"
```

### 방법 B — 이 저장소에만 local config

```bash
# finn 세션
git config user.name finn
git config user.email finn@users.noreply.github.com

# toma 세션
git config user.name toma
git config user.email toma@users.noreply.github.com

# pl 세션
git config user.name pl
git config user.email pl@users.noreply.github.com
```

email은 GitHub가 인식하는 주소(또는 `...@users.noreply.github.com`)를 쓴다.

### 공동 작업 커밋 trailer

```text
Co-authored-by: toma <toma@users.noreply.github.com>
Co-authored-by: finn <finn@users.noreply.github.com>
Co-authored-by: pl <pl@users.noreply.github.com>
```

### 승인(Approve)은 name으로 안 바뀜

- `user.name=toma` ≠ GitHub 리뷰어 전환.
- 동일 계정이면 PR에 `LGTM (toma)` / `LGTM (finn)` / `LGTM (pl)` 코멘트로 **명목 승인**.
- 계정 2개일 때만 `gh auth switch` 후 실제 Approve.

---

## 3. 브랜치 명명

```text
main                 # 출품·데모 정본. 직접 push 금지(긴급은 master만)
finn/<topic>         # 예: finn/w1-compose-schema
toma/<topic>         # 예: toma/w1-node-runtime
pl/<topic>           # 예: pl/docs-readme-hygiene
docs/<topic>         # 문서만 (또는 pl/docs-… 권장)
hotfix/<topic>       # D-day 긴급 (사후 Issue 필수)
```

```bash
git checkout main
git pull origin main
git checkout -b finn/w1-compose-schema
```

- 기본: 이슈 1개 ≈ 브랜치 1개. **W1–W3.5 fast-track은 주 단위로 묶을 수 있다** (§6.4).
- `main` force-push 금지.

---

## 4. 이슈 (Issues)

1. 작업 전에 Issue 생성.
2. 제목 접두: `W1:` / `W2:` / `W3:` / `docs:` / `chore:`.
3. 본문에 목표·완료 정의·관련 문서 링크.
4. 담당: 본문에 `Assignee 명목: finn|toma|pl`.
5. PR에 `Closes #N` 또는 `Refs #N`.

### 웹에서 만들기

1. https://github.com/gncorpseo-commits/capnet/issues  
2. **New issue** → 제목·본문 → **Submit new issue**

### CLI

```bash
gh issue create --repo gncorpseo-commits/capnet \
  --title "W1: docker compose PG16 + Core 골격" \
  --body "STATE.md W1 목표 1. 완료: compose up 후 PG healthy."
```

### W1 기본 이슈 예시

- `W1: docker compose PG16 + Core 골격`
- `W1: schema 적재 + image.classify@1 seed`
- `W1: claim INSERT … SELECT 고정`

---

## 5. 커밋 메시지·스테이징

- 메시지: **왜** 위주, 1~2문장 (한글 OK).
- 스테이징: `git add -A` / `git add .` 는 훅에 막힐 수 있음 → **경로 명시**.

```bash
git add apps/core/README.md docs/history/CHANGELOG.md
git -c user.name=finn -c user.email=finn@users.noreply.github.com commit -m "W1: Core 골격 추가 — claim 패턴 문서를 먼저 고정하기 위함"
git push -u origin HEAD
```

### 커밋하면 안 되는 것

- `.env`, 시크릿, 키
- EuroSAT 원본 대용량, 사전학습 가중치
- 개인 PC 절대경로·내부 URL 하드코딩

의존성 추가 시 같은 작업에 `THIRD-PARTY-LICENSES.md` 한 줄 누적.

---

## 6. Pull Request → 명목 승인 → 머지

### 6.1 PR 생성

```bash
git push -u origin HEAD
gh pr create --base main --title "W1: …" --body "$(cat <<'EOF'
## Summary
- 

## Issue
Closes #

## Author
finn

## Checklist
- [ ] W1이면 claim `INSERT … SELECT` 패턴을 깨지 않음
- [ ] 게이트 사슬 순서를 건너뛰지 않음
- [ ] 시크릿/대용량 데이터 없음
- [ ] 상대 명목 리뷰 요청함

## 명목 리뷰어
toma
EOF
)"
```

웹: 푸시 후 노란 배너 **Compare & pull request** → base=`main`.

### 6.2 명목 승인 (동일 계정)

리뷰어가 PR에 코멘트:

```text
LGTM (toma) — 체크리스트 확인함. master 머지 요청.
```

```text
LGTM (finn) — claim SQL 패턴 OK.
```

```text
LGTM (pl) — 문서·일정 체크 OK.
```

자기 PR을 자기 이름으로 승인하는 코멘트는 무효. **상대 역할 이름**으로 쓴다.

### 6.3 머지

- **master만** `main`에 머지 (또는 master가 위임한 한 명).
- 권장: **Squash and merge**.
- 머지 후 브랜치 삭제.
- 긴급 hotfix 후 Issue로 사유 기록.

### 6.4 Contest W1–W3.5 fast-track (승인 부담 줄이기)

출품 전까지는 **기록을 남기되 클릭을 줄인다.** 계정 1개면 명목 LGTM 연극을 매번 하지 않는다.

| 종류 | PR | LGTM | 머지 |
|------|-----|------|------|
| `docs:` / `chore:` / Wiki / STATE | 작은 PR OK | **생략** | master가 즉시 squash |
| Contest Must (compose·스키마·claim·게이트·M25) | **주 단위로 묶음** (이슈는 #2 #3 #4처럼 쪼개 두고 브랜치는 하나) | 스키마/claim처럼 핵심만, 또는 master 위임 시 생략 | `gh pr merge --squash --delete-branch` |
| 출품 후 / 계정 2개 | 기존 §6.2–6.3 | 실제 Approve | branch protection |

```bash
# 웹 버튼 대신 (master 위임·fast-track)
gh pr merge <번호> --squash --delete-branch
```

**묶음 예 (W1):** 브랜치 `finn/w1-compose-schema-claim` 하나 → Issues #2+#3+#4 → PR 1개 → squash merge.

금지하지 않는 것: Issue는 그대로 만든다. `main` 직접 push는 여전히 금지.

---

## 7. GitHub 기능별 사용법 (우리 팀 표준)

저장소 상단 탭 기준. **지금은 굵게 표시한 것만 일상 사용.**

### 7.1 Code (일상)

- 소스·문서 열람, 브랜치 전환, 파일 검색.
- **Clone:** `git clone https://github.com/gncorpseo-commits/capnet.git`
- **Release:** W3.5에 `v0.1.0-contest` 태그 + zip (출품용). 지금은 만들지 않아도 됨.

### 7.2 Issues (일상)

- 할 일·버그·결정 대기 기록.
- 라벨 예: `W1`, `W2`, `must`, `docs` (없으면 제목 접두로 대체).
- 닫기: PR `Closes #N` 또는 이슈에서 Close.

### 7.3 Pull requests (일상)

- 코드 유입의 **유일한** 정상 경로 (`main` 직접 push 금지).
- Files changed에서 리뷰 → Conversation에 `LGTM (finn|toma|pl)`.
- master가 Squash merge.

### 7.4 Actions (나중 · W3/Phase B)

- CI: compose 스모크·스키마 적용 등.
- **출품 전 과도한 파이프라인 꾸미기 금지.** 코드가 생긴 뒤 최소 1개.
- 실패 로그는 Actions 탭 → 해당 workflow run.

### 7.5 Projects (선택)

- Issue가 많아질 때 칸반용.
- 대회 중에는 Issues 목록만으로도 충분. 필수는 아님.

### 7.6 Wiki (일상 · 팀 규칙)

- **팀 프로세스·온보딩** 문서 (본 가이드).
- 설계 정본은 레포 `docs/design/` · `docs/spec/` (Wiki와 이중 진실 금지).
- 가이드를 고치면: Wiki **그리고** `docs/guide/github-team-guide.md` 를 같이 맞춘다.

#### Wiki 편집

1. Wiki 탭 → 페이지 → **Edit**.
2. 저장 후 Home 링크 클릭 테스트.

#### Home에 링크 달기

```markdown
# CapNet Wiki

- [팀 GitHub 사용 가이드](Team-GitHub-Guide)
- [팀 GitHub 사용 가이드 (공백 제목)](Team GitHub Guide)
```

페이지 제목이 `Team GitHub Guide`(공백)이면 위 두 링크 중 하나로 열리는 경우가 많다. **안 열리면 사이드바 페이지를 연 뒤 주소창 끝 segment를 괄호에 그대로 복사.**

#### Wiki 함정 (필수 숙지)

| 증상 | 원인 | 해결 |
|------|------|------|
| Home 링크가 **Create new page** | 링크 하이픈이 특수문자 `‐` (`%E2%80%90`) | 키보드 `-`로 다시 타이핑 |
| URL에 `%E2%80%90` | 워드/한글 복붙 하이픈 | 페이지 삭제 후 ASCII/`공백` 제목으로 재작성 |
| 같은 이름처럼 보이는 페이지 2개 | 유니코드 vs ASCII 하이픈 | 하나만 남기고 삭제 |

### 7.7 Security and quality (켜 두기)

- **Dependabot alerts:** Settings에서 On 권장 (의존성 쌓인 뒤 라이선스·취약점).
- CodeQL 등 본격 분석은 코드 이후.
- 시크릿이 push되면 즉시 rotate + 커밋 히스토리에서 제거.

### 7.8 Insights (참고)

- 커밋·PR 통계. 동일 계정이면 finn/toma/pl 기여가 한 계정으로 묶일 수 있음.
- author name으로 로컬 로그 구분: `git log --format='%an %s'`

### 7.9 Settings (master 위주)

| 항목 | 권장 |
|------|------|
| Collaborators | 팀원 초대 |
| Default branch | `main` |
| Features → Issues / Wiki | On |
| Features → Projects | 선택 |
| Branch protection on `main` | 가능하면 PR 필수. **동일 계정이면 required review는 실익 적음** → 명목 승인 규칙으로 대체 |
| Actions permissions | 팀만 write |

### 7.10 Agents (GitHub Agents)

- 실험용. **대회 구현 일정과 분리.**
- CapNet 코딩은 로컬/Cursor + 이 가이드 워크플로 우선.
- Agents로 `main` 직커밋하지 말 것.

---

## 8. 모듈·MSA와 브랜치 매핑

| 모듈 | 책임 | 브랜치 예 |
|------|------|-----------|
| 요청 모듈 | 능력 요청·결과 조회 | `toma/w3-request-cli` |
| 코어 모듈 | 중계·제어·보안·게이트·claim | `finn/w1-core` |
| 노드 에이전트 | lease → 추론 → 결과 | `toma/w2-node` |

통신은 API. 데모 기간 Node→Core **폴링 허용**, WebSocket은 이후.

---

## 9. 환경 (개발 · 검증 · 운영)

| 환경 | 용도 | 대회 중 |
|------|------|---------|
| 개발 (dev) | 로컬 compose | **주 작업장** |
| 검증 (staging) | 깨끗한 clone → demo | W3 재현 |
| 운영 (prod) | 실서비스 | 출품 후 |

출품 전 운영 인프라보다 **dev + 검증 재현** 우선.

---

## 10. 충돌·우선순위

1. Contest Must (`STATE.md`, claim `INSERT … SELECT`, 게이트 사슬, M25) > 새 기능.
2. 같은 파일 동시 수정: Issue에 “잠금” 코멘트 후 한 사람만.
3. 설계 논쟁(Open CapNet·유휴 등): 출품 후.
4. **master 판단이 최종.**

---

## 11. 일일 루틴

1. `main` pull.
2. Issue에서 오늘 할 `#` 선택 (W1–W3.5는 주 묶음 브랜치에 이어서 커밋해도 됨).
3. `finn/…` · `toma/…` · `pl/…` 브랜치에서 작업.
4. PR. `docs:`/`chore:`는 LGTM 생략(§6.4). Must는 주 1회 PR.
5. `gh pr merge --squash --delete-branch` (또는 웹 Squash and merge). STATE는 같은 PR에 넣는다.

---

## 12. 금지 요약

| 금지 | 이유 |
|------|------|
| Issue 없는 장시간 코딩 | 추적 불가 |
| `main` 직접 push (비긴급) | 데모 깨짐 |
| 전역 git user 덮어쓰기 | 서명 혼선 |
| 시크릿·대용량 데이터 커밋 | 라이선스·보안 |
| claim을 ORM 수기 스냅샷으로 | FK 붕괴·변별점 상실 |
| Wiki만 고치고 `docs/guide/github-team-guide.md` 방치 | 이중 진실 |

---

## 13. 클론 후 첫 설정 체크리스트

- [ ] `git clone` 완료
- [ ] `gh auth status` (CLI 쓸 경우)
- [ ] Wiki Home 링크 → 이 가이드 열리는지
- [ ] Issues에서 내 W1 이슈 확인
- [ ] 첫 브랜치 `finn/…` · `toma/…` · `pl/…` 생성
- [ ] 커밋 시 author가 finn/toma/pl인지 `git log -1` 확인

---

## 14. 관련 링크

| 대상 | URL |
|------|-----|
| Code | https://github.com/gncorpseo-commits/capnet |
| Issues | https://github.com/gncorpseo-commits/capnet/issues |
| Pull requests | https://github.com/gncorpseo-commits/capnet/pulls |
| Wiki Home | https://github.com/gncorpseo-commits/capnet/wiki |
| 이 가이드 (Wiki) | https://github.com/gncorpseo-commits/capnet/wiki/Team-GitHub-Guide |
| STATE | https://github.com/gncorpseo-commits/capnet/blob/main/STATE.md |

---

## 문서 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| 1.0 | 2026-08-03 | 초안 (Wiki 복붙, §2에서  Truncated) |
| 1.1 | 2026-08-03 | 전문 복구 · GitHub 기능 사용법 · Wiki 함정 · MSA/환경 · 체크리스트 |
| 1.2 | 2026-08-05 | §6.4 W1–W3.5 fast-track (docs/chore LGTM 생략 · 주 단위 PR · `gh pr merge --squash`) |
| 1.3 | 2026-08-08 | 작업 역할 **pl** 추가 (finn/toma와 동급 · `pl/<topic>` · `LGTM (pl)`) |
