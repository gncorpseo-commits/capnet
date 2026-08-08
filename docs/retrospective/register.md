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

### SD-001 · A/B(S2) Must **달성** (실측 Within · 공개 시 조건 명시)
- **무엇:** n≥300 paired `|acc_A−acc_B|≤0.05`를 Contest/본편 **Must 목표**로 두고 달성
- **실측:** 2026-08-08 · A(`TinyEuroSAT` **80ep**) n300 acc=0.880 · B(`TinyEuroSATB` **40ep**) 0.927 · **abs_diff≈0.0467 WITHIN**
- **주의:** train epoch는 A/B 불일치(80 vs 40). SE≈0.019로 임계와 비슷 — 해석·보고서에 명시. 사전학습 없음
- **범위 한정 (2026-08-08 추가):** 이 측정은 **게이트 사슬 밖**이다. `score_n300`이 `app.score_gate`를 직접 실행하고 `compare_ab`가 점수 JSON 2개를 비교한다 — `gate_run`→`agent_capability_passed`→`assignment`를 타지 않는다. 따라서 "두 가중치의 정확도가 비슷하다"는 성립하나 **"계약을 통과한 Agent를 CapNet이 교체해도 등가"**(기획서 §7.1)는 아직 아니다
- **출품:** 양식에 Must 한 줄 + 한계(epoch·SE·사슬 밖) 동시 기재. **UC-7 영상 촬영은 불가** — 지정 실행 배관은 있으나 Agent B가 게이트를 통과한 적이 없어 띄울 교체 할당이 없다. 150–170초는 게이트 사슬 다이어그램으로 간다
- **상태:** closed (실측 Within · 문서 반영 진행). §7.1 사슬 안 증명은 **SD-006 / roadmap P1-1·P1-2**로 이월

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

### SD-008 · 골든셋 ⊂ 학습셋 (홀드아웃 없음) — **Phase 1 판정 보류 원인**
- **무엇:** 데모 N=40 **40/40**, 본편 n=300 **300/300** 케이스가 학습셋 안에 있다
- **왜 생겼나:** `train_scratch.py`가 zip 전수 27,000장을 학습하고(주석 "scratch 전수"), `extract_golden.py`가 **같은 zip**에서 케이스를 뽑는다. 분할·제외 로직이 없다
- **귀결:** 게이트 점수(0.525–0.927)는 **학습 데이터 재현 점수**이며 일반화 성능이 아니다. D2(채점 가능한 계약)는 홀드아웃 위에서만 성립한다
- **영향 없음:** 게이트 사슬·M25·sanity floor·Product Track 구조 (판정 리포트 §6.2)
- **증거:** `python3 scripts/check_golden_leakage.py` (exit 2)
- **해소 조건:** H1 분할 도입 · H2 골든 재추출 · H3 후보 8개 재학습(CPU 3–4h) · H4 재측정 — [`../ops/phase1-verdict.md`](../ops/phase1-verdict.md) §6.3
- **대회:** 제출을 막지 않는다. 보고서 §8에 명시 필요. H1–H4를 8/27 전에 할지는 **master 판단**
- **상태:** open (Phase 2 착수 차단)

### SD-005 · 출품 패키지(양식·영상·포털) 미완
- **무엇:** 기술 MVP는 있음 · 공식 보고서 파일·YouTube·포털 zip은 남음
- **왜:** 공지 39·양식 확정 후 이식 단계
- **대안:** `contest-report-form-draft.md` 문장 → docx/hwp
- **예정:** 8/27 18:00 전
- **상태:** open

---

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
