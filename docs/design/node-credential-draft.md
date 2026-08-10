# node_credential 설계 (구현됨)

> **상태 (2026-08-11):** **구현 완료** — `migrations/0007` · `apps/core/app/credential.py` ·
> `tests/integration/check_node_credential.py` (17종). SD-002 closed.
> DDL 은 `schema.sql` 이 아니라 **마이그레이션으로** 추가했다 (기획서 §16 동결 이후의 정식 경로).
>
> **열린 질문(§6) 확정:** ①opaque 토큰 + DB sha256 (JWT 는 등급 claim 여지로 배제)
> ②전 Node · **강제는 플래그**(`REQUIRE_NODE_CREDENTIAL`, 기본 꺼짐) ③`expires_at` 선택 ·
> 회전은 폐기 후 재발급 ④`api_key` 와 통합하지 않음
>
> 아래는 승인 시점의 초안 원문이다. 구현이 이를 따랐다.

**갱신:** 2026-08-06 (초안) · 2026-08-11 (구현)  
**근거:** Node는 자기 등급을 주장할 수 없다 (CLAUDE · D4 계열). Core가 부여한 증서만 신뢰.

---

## 1. 문제

지금은 Node 등록이 Core 관리자 API(`POST /v1/nodes`)로만 이뤄지고, 런타임은 `CORE_URL`만 알면 lease를 실행한다.  
본편에서 Node가 늘어나면:

1. 어떤 프로세스가 어떤 `node.id`인지 **증명**해야 하고  
2. `trust_domain` / `compute_tier_max` / `is_gate_runner`를 **Node가 보내지 못하게** 막아야 한다.

`node_credential`은 그 증서 테이블·발급·검증 경로의 이름이다. Contest MVP에는 **없음** (의도).

---

## 2. 비목표 (지금)

- 스키마 마이그레이션·시드 변경
- mTLS / JWT 라이브러리 도입 확정
- public Node 셀프 온보딩
- 출품 Must에 포함

---

## 3. 제안 모델 (초안 — 승인 전 DDL 금지)

```text
app_user (admin) ──발급──► node_credential ──속함──► node
                              │
                              ├─ credential_id (UUID)
                              ├─ node_id (FK)
                              ├─ secret_hash (BYTEA)   # 평문 시크릿은 한 번만 반환
                              ├─ key_prefix (TEXT)     # 로그·조회용
                              ├─ issued_at / expires_at / revoked_at
                              └─ UNIQUE(node_id) WHERE revoked_at IS NULL  (활성 1개)
```

**원칙**

| # | 규칙 |
|---|------|
| C1 | 등록 시 `trust_domain`·`compute_tier_max`·`is_gate_runner`는 **Core만** 씀. credential API에 등급 필드 없음 |
| C2 | Node 요청 헤더/바디의 등급 필드는 **무시 또는 400**. 스냅샷은 DB `node` 행 |
| C3 | 시크릿 평문은 발급 응답 **1회**. 저장은 해시만 |
| C4 | claim·execute·gate 러너 식별은 credential → `node_id` 해석 후 기존 FK 사슬 |
| C5 | 스키마 제약을 약화하지 않음. 추가는 허용, 기존 CHECK/FK 삭제·`NOT VALID` 금지 |

---

## 4. API 스케치 (구현 전)

| 방법 | 경로 | 역할 |
|------|------|------|
| POST | `/v1/nodes/{id}/credentials` | admin 발급 → `{prefix, secret}` 1회 |
| POST | `/v1/nodes/{id}/credentials/revoke` | 폐기 |
| (Node) | `Authorization: CapNet-Node <prefix>.<secret>` | Core가 해시 검증 후 `node_id` 바인딩 |

데모 폴링·`/v1/execute`는 당분간 **credential 없이** 동작 (로컬 compose). 본편에서만 강제 플래그.

---

## 5. 마이그레이션 절차 (승인 후)

1. 이 문서 리뷰 · 팀 승인  
2. `schema.sql`에 테이블 **추가**만 (기존 제약 수정 금지)  
3. Core 검증 미들웨어  
4. compose Node에 시크릿 주입 (`.env`, 커밋 금지)  
5. smoke: 위조 등급 필드 거부 · 폐기 시크릿 거부

---

## 6. 열린 질문

1. 시크릿 형식: opaque token vs JWT (추천: opaque + DB 해시, JWT는 등급 claim 금지 전제)  
2. gate-runner만 강제할지, 모든 Node에 강제할지  
3. 만료·회전 주기  
4. `api_key`(사용자)와 테이블 통합 여부 — **비추** (주체·권한이 다름)

---

## 7. 한 줄

**설계는 여기까지. DDL·구현은 별도 승인 이슈.** Contest 출품과 A/B Must와 무관하게 미룰 수 있다.
