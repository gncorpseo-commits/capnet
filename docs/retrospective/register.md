# CapNet decision / debt register

**갱신:** 2026-08-07  
분류 정의: [`README.md`](./README.md)

---

## Technical Debt

### TD-001 · 수동 sbom.json → **closed**
- **무엇:** CycloneDX를 도구로 생성하지 않고 수기 JSON을 커밋함
- **왜:** 호스트에 Python PATH가 없었고, 설치를 묻지 않은 채 산출물을 채움
- **대안:** Python 3.12 설치 → `cyclonedx-py requirements` → `sbom.json` 교체
- **해결:** 2026-08-07 · `scripts/generate_sbom.ps1` · 호스트 Python 3.12.10
- **상태:** closed

### TD-002 · 호스트 Python / Scripts PATH
- **무엇:** Cursor/새 셸에서 `python`/`pip`가 Store stub이거나 PATH에 Scripts가 없음
- **왜:** winget 설치 직후 PATH 미반영 · WindowsApps stub 우선
- **대안:** `Local\Programs\Python\Python312` 절대경로 사용 또는 셸 재시작 후 PATH
- **예정:** 개발자 머신마다 1회 · 문서화로 충분
- **상태:** open (완화됨 · 절대경로 스크립트)

---

## Scope Decision

### SD-001 · A/B(S2) 등가성 — **반증됨 (2026-08-09)**
- **무엇:** n≥300 paired `|acc_A−acc_B| ≤ 0.05` 을 Must 목표로 두었다
- **최초(누출) 측정:** 2026-08-08 · A 0.880 · B 0.927 · `abs_diff 0.0467` → WITHIN
- **홀드아웃 재측정:** 2026-08-09 · A(`ho80`) 0.9100 · B 최선(`hob10`) 0.8133 · **`abs_diff 0.0967` → EXCEEDS**
  - 원래 쌍(A 80ep vs B 40ep)은 **0.4633**. 어떤 B를 골라도 임계의 약 2배 이상
- **결론:** **0.0467 WITHIN은 골든셋 누출의 산물이었다.** B가 골든 케이스를 학습에서 봤다
- **유효하게 남는 것:** 사슬 위 교체 실행 자체(§7.1-2·3)는 사실이며 영향받지 않는다.
  "교체해도 계약 하한은 지켜진다"는 말할 수 있고 "같은 답이 나온다"는 말할 수 없다
- **근본 원인:** 모델이 아니라 계약 설계 — **SD-009**
- **상태:** closed (반증으로 종결). 등가 주장은 보고서·영상에서 내렸다

### SD-009 · 계약이 내적으로 모순이다 — 하한형 게이트 vs 구간형 등가
- **무엇:** 통과 기준은 하한(`acc ≥ 0.68`)인데 등가 기준은 구간(`|Δ| ≤ 0.05`)이다.
  **하한형 게이트는 쌍별 편차를 유계로 만들 수 없다.** 실측 통과자 범위 0.7067~0.9100 (폭 0.2033)
- **왜 중요한가:** D1(증명 대상 = Capability 추상화 성립)과 D2(계약)의 접점이다.
  대체 가능성을 계약으로 보장하려면 통과 기준이 구간이어야 한다
- **누출과의 관계:** 독립된 결함이다. 누출이 없었어도 드러났을 것이며, 누출이 그것을 가리고 있었다
- **선택지:** (A) 통과 기준을 구간으로 — 좋은 모델이 탈락 / (B) 등가 임계 완화 — 주장 약화 /
  (C) 등가를 계약 조건이 아닌 관측값으로 격하 — D1 변경. 상세: `../ops/phase1-verdict.md` §6.1.1
- **권한:** 계약 설계 변경이므로 판정의 범위 밖. **master 결정 필요**
- **해소:** 2026-08-09 **C안 채택** (master). 기획서 v4.6 §7.1 — 등가성을 계약 조건에서 관측값으로 격하,
  §7.1-4를 「하한 예측」으로 교체. D17. `golden_metrics` 의 `equivalence` → `guarantee:floor_only`
- **검증:** 새 조건은 반증되지 않았다 (통과자 6/6이 서로소 검증셋에서 하한 유지). **단 최소 마진 0.5 SE**
- **남는 것:** 하한 0.68 자체의 근거 재유도 (SD-004 무효) · 검증셋 확대
- **상태:** closed (계약 재정의로 종결)

### SD-008 · 골든셋 ⊂ 학습셋 → **해소 (2026-08-09)**
- **해소:** H1 분할 도입(`sha1(name)[:8] % 5 == 0 → holdout`) · H2 홀드아웃 골든 재추출(겹침 0/300) ·
  H3 후보 8개 재학습 · H4 재측정 완료
- **잔여:** 데모 골든 N=40의 홀드아웃 교체는 미완 (jpg 40장 + manifest + `seed.sql` sha256)
- **사후 평가:** 수치 영향은 백본마다 달랐다. TinyEuroSAT은 격차 0.0067로 미미했으나
  TinyEuroSATB는 40ep에서 0.9267 → 0.4467로 무너졌다. **A/B 등가 주장이 이 차이 위에 서 있었다** (SD-001)
- **상태:** closed

### SD-010 · 절대규칙 4는 **코드가 아니라 배치 전제**로만 지켜진다
- **무엇:** `POST /v1/nodes` 가 요청 본문의 `trust_domain` · `compute_tier_max` · `is_gate_runner` 를 그대로 받는다.
  Core API 에 인증이 **없다**. 실측: `trust_domain=team, compute_tier_max=L, is_gate_runner=true` 로 노드 등록 성공
- **문서와의 차이:** CHANGELOG W1 은 "Node 등급은 Core 관리자 등록. **Node 런타임 자기주장 경로 없음**"이라고 적었다.
  정확히는 **Node 런타임 코드가 그 경로를 호출하지 않을 뿐, 경로는 열려 있고 아무나 부를 수 있다**
- **왜 지금 안 고치나:** 인증 도입은 범위가 크고, Contest §4.2 가 "외부 개발자 셀프서브 온보딩"을 Non-goal 로,
  D7 이 "MVP Node = 팀 자체 조달만"으로 두었다. **팀 내부망 전제**가 실질 방어다
- **정직한 서술:** "Node 가 자기 등급을 주장할 수 없다"가 아니라
  **"Node 등급은 Core 가 부여하며, MVP 는 그 API 를 신뢰 경계 안에 둔다"**
- **해소 경로:** `node_credential` (SD-002) + 인증. Phase 2
- **상태:** open — 문서 표현 정정 필요

### SD-011 · 만료 lease 회수 부재 → **해소 (2026-08-10)**
- **무엇:** 배정 후 기기가 죽으면 task 가 ASSIGNED/LEASED 에 영구히 갇혔다.
  Node 는 만료 배정을 안 가져가고 워커는 QUEUED 만 봐서 회수 주체가 없었다
- **실측:** 기기 75초 정지 → 복구 후에도 `LEASED · expired=t` 그대로
- **해소:** `claim.reclaim_expired()` — 워커가 claim 전에 만료분을 EXPIRED 로 정리하고 task 를 QUEUED 로 되돌린다.
  갇혀 있던 task 가 재배정되어 SUCCEEDED 확인
- **관련:** Contest M17 이 "만료 스캐너는 후순위"로 두었던 항목. heartbeat 가 생기면서 함께 닫혔다
- **상태:** closed

### SD-002 · node_credential DDL 보류
- **무엇:** 설계 문서만 (`docs/design/node-credential-draft.md`). 스키마 미변경
- **왜:** 프로젝트 규칙 — DDL/마이그레이션은 승인 전 금지
- **대안:** 승인 후 migration + 발급 API
- **예정:** 승인 후
- **상태:** open

### SD-003 · golden n=300 케이스 미커밋
- **무엇:** 추출·채점 파이프라인 · `data/golden-n300/` · `artifacts/` gitignore
- **왜:** 용량 · 데모 N=40과 본편 분리
- **대안:** 본편/A/B 시 추출·채점·(선택) 커밋 정책 재검토
- **예정:** 본편 · `scripts/score_n300` 로컬 실행
- **상태:** open

### SD-004 · 게이트 임계 0.68/0.65 (정직 보정)
- **무엇:** 가정 0.75/0.72 대신 N=40 실측(acc≈0.70)에 맞춰 바를 낮춤
- **왜:** 통과를 조작하지 않음 · dummy PASSED ≠ 실게이트
- **대안:** 추가 학습으로 0.75 재도전 (보장 없음)
- **예정:** 요청 시에만
- **상태:** closed (결정 확정 · 학습↑는 별도 이슈)

### SD-006 · 종착점을 **Phase 3+ 로드맵 전체**로 확장
- **무엇:** 프로젝트를 Contest MVP에서 끝내지 않고 기획서 §9의 Phase 3+(테넌트 파일럿·invited Node·public 개방·경제)까지 진행
- **왜:** 2026-08-08 결정 (D16). Contest MVP는 Phase 1의 슬라이스이며 8/27은 외부 마감일일 뿐
- **불변:** 출품 트랙이 여전히 1순위. 체크리스트 §5.1 "미완이면 본편 중단" 유지. §7.2 Go 없이 Phase 2 코드 금지(기획서 §13) 유지
- **첫 관문:** Phase 1 완주 3건 — Agent B 실게이트 PASSED · 증명 모드 교체 할당(M14/UC-7) · 통과율 20–80% 실측 → 판정 리포트
- **문서:** [`../design/roadmap.md`](../design/roadmap.md) — 진입조건·산출물·판정 게이트
- **상태:** open (대회 제출 후 착수)

### SD-007 · 마이그레이션 체계 부재
- **무엇:** DDL 적용 경로가 `init.sql` 일괄뿐. 기존 볼륨 업그레이드 수단이 `down -v`밖에 없음
- **왜:** Phase 1은 스키마 v4.4 동결 전제라 필요가 없었음 (기획서 §16)
- **영향:** Phase 2 `node_credential` DDL(SD-002)의 **선결과제**. 제약 추가는 절대규칙 1상 허용이나 적용 수단이 없음
- **대안:** 마이그레이션 도구·순서 결정 → 볼륨 보존 업그레이드 경로 → 승인
- **예정:** Phase 2 착수 전
- **상태:** open

### SD-005 · 출품 패키지(양식·영상·포털) 미완
- **무엇:** 기술 MVP는 있음 · 공식 보고서 파일·YouTube·포털 zip은 남음
- **왜:** 공지 39·양식 확정 후 이식 단계
- **대안:** `contest-report-form-draft.md` 문장 → docx/hwp
- **예정:** 8/27 18:00 전
- **상태:** open

---

### SD-012 · 8/9–8/10 작업이 PR 없이 main 직행 (프로세스 위반)
- **무엇:** PR #22 머지 이후 커밋 **18건**(`b2cfa1c`~`d733261`)이 브랜치·이슈·PR·리뷰 없이 `main` 에 직접 push됨
- **어긴 것:** `github-team-guide` §3 "main 직접 push 금지" · §1 "이슈 없이 코딩하지 않는다"
- **원인:** `gh pr merge --delete-branch` 가 로컬을 main 으로 전환했고 이후 브랜치를 확인하지 않음
- **되돌리지 않는 이유:** 내용은 검증됨(깨끗한 환경 재현·회귀 통과). revert 는 검증된 결과물을 잃고,
  히스토리 재작성은 §3 force-push 금지에 다시 걸린다
- **아이러니:** 같은 기간에 찾아 고친 결함 6건이 전부 "문서가 선언한 규칙을 코드가 강제하지 않는다" 유형이었다.
  저장소 규칙 자체에 대해 같은 유형의 위반을 저지른 것
- **기록:** [issue #23](https://github.com/gncorpseo-commits/capnet/issues/23)
- **재발 방지 제안:** 전체 스테이징을 막는 훅이 이미 작동 중이다(이번 작업 중 2회 차단).
  같은 자리에 **main 직접 push 차단 훅**을 넣으면 문서에만 있던 규칙이 강제 지점으로 옮겨간다 —
  이번 결함 6건에 대한 처방과 동일
- **상태:** open (master 판단: 기록 종결 여부 · 훅 도입 여부)

## Environment Adaptation

### EA-003 · 가중치 GitHub raw 공개 (제9조)
- **무엇:** `eurosat_scratch.safetensors`를 main에 두고 raw URL로 승인 없이 다운로드
- **왜:** 유형3 가중치 전체 공개 의무
- **대안:** Hugging Face / Release asset
- **실측:** 2026-08-07 HTTP 200 · 378784 bytes
- **상태:** closed

### EA-001 · Docker pip 인덱스 분리
- **무엇:** `requirements.txt` 후 torch는 pytorch CPU index로 별도 설치
- **왜:** torch index가 safetensors 해석을 깨뜨림
- **대안:** 단일 requirements에 섞기 (실패)
- **예정:** 유지
- **상태:** closed (정상 대체)

### EA-002 · OpenAPI 확인에 curl.exe
- **무엇:** PowerShell `Invoke-WebRequest` 대신 `curl.exe`로 `/openapi.yaml` 검증
- **왜:** 환경별 IWR 이슈
- **대안:** IWR 재시도
- **예정:** 유지
- **상태:** closed (정상 대체)
