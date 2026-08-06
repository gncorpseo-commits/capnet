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

### SD-001 · A/B(S2) Must 미구현
- **무엇:** 두 scratch Agent 동등성 비교를 출품 Must로 올리지 않음
- **왜:** N=40으로는 편차 0.05 통계 판정 불가 · Contest “밀리면 버림” 1순위
- **대안:** Must 승격 시 백본 2종 + n≥300
- **예정:** 미결 기한 8/11 · 승격 전까지 구현 금지
- **상태:** open

### SD-002 · node_credential DDL 보류
- **무엇:** 설계 문서만 (`docs/design/node-credential-draft.md`). 스키마 미변경
- **왜:** 프로젝트 규칙 — DDL/마이그레이션은 승인 전 금지
- **대안:** 승인 후 migration + 발급 API
- **예정:** 승인 후
- **상태:** open

### SD-003 · golden n=300 케이스 미커밋
- **무엇:** 추출 파이프라인만 · `data/golden-n300/` gitignore
- **왜:** 용량 · 데모 N=40과 본편 분리
- **대안:** 본편/A/B 시 추출·채점·(선택) 커밋 정책 재검토
- **예정:** 본편
- **상태:** open

### SD-004 · 게이트 임계 0.68/0.65 (정직 보정)
- **무엇:** 가정 0.75/0.72 대신 N=40 실측(acc≈0.70)에 맞춰 바를 낮춤
- **왜:** 통과를 조작하지 않음 · dummy PASSED ≠ 실게이트
- **대안:** 추가 학습으로 0.75 재도전 (보장 없음)
- **예정:** 요청 시에만
- **상태:** closed (결정 확정 · 학습↑는 별도 이슈)

---

## Environment Adaptation

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
