# 제품 배포 런북 — 정문을 닫고 올린다

> 이 문서는 **제품 배포**용이다. 데모·심사용 기동은 [`../../README.md`](../../README.md) 빠른 시작을 본다.
> 최초 작성: 2026-08-12 · 실측: 격리 프로젝트·빈 볼륨 e2e 14항목

`compose.yaml` 단독은 **열려 있다** — 관리 API 인증 꺼짐, postgres 호스트 노출, 마이그레이션 자동 적용.
그 기본값으로 남의 데이터를 받으면 안 된다. `compose.prod.yaml` 오버레이가 그 셋을 전부 뒤집는다.

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

| | 데모 (`compose.yaml`) | 제품 (`+ compose.prod.yaml`) |
|---|---|---|
| 관리 API 인증 | 꺼짐 — 쓰기 12개가 열려 있다 | **강제** (`REQUIRE_API_KEY=1`) |
| Node 증서 | 꺼짐 — 사칭 가능 | **강제** (`REQUIRE_NODE_CREDENTIAL=1`) |
| postgres | 호스트 5432 공개 | **비공개** |
| 마이그레이션 | 일회성 서비스가 자동 적용 | **끔** — 운영자가 시점을 잡는다 |
| DB 비밀번호 | 기본값 `capnet` | **`.env` 필수** (없으면 기동 거부) |
| seed Node 3대 | 뜬다 | **안 뜬다** (`profiles: demo`) |

---

## 1. 순서 (이 순서를 지킨다)

**닭-달걀이 하나 있다.** 인증을 켠 상태에서는 API 로 첫 키를 만들 수 없다 — 키를 만들려면 키가 필요하다.
그래서 첫 키만 **CLI**(DB 자격증명을 이미 가진 사람)로 만든다. `scripts/migrate.sh` 와 같은 자리다.

### 1) `.env` 를 채운다

```bash
cp .env.example .env
# POSTGRES_PASSWORD 는 반드시 바꾼다
openssl rand -base64 32
```

`POSTGRES_USER` · `POSTGRES_PASSWORD` · `POSTGRES_DB` · `DATABASE_URL` 이 없으면 compose 가 기동을 거부한다.
의도된 것이다 — 기본 비밀번호로 제품이 뜨는 경로를 없앴다.

> `DATABASE_URL` 의 비밀번호는 **URL 인코딩**한다. `$` 는 `%24`, `@` 는 `%40`.

### 2) DB 를 올리고 스키마를 적용한다

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d postgres
scripts/migrate.sh up        # 자동 적용이 꺼져 있으므로 직접 돌린다
scripts/migrate.sh verify    # "verify OK — N개 파일 · N개 적용 · 체크섬 일치"
```

새 볼륨이면 initdb 가 `docs/spec/schema.sql` 을 먼저 넣고, 그 위에 `migrations/` 가 올라간다.
자세한 것은 [`migrations.md`](./migrations.md).

### 3) Core 를 올린다 (아직 키가 없다 — 잠긴 상태가 정상이다)

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d core
curl -s localhost:8000/v1/ops/status | python3 -m json.tool
```

이때 `"ok": false` 와 `"관리 API 키가 없다 — 강제를 켜면 잠긴다"` 경고가 나온다. **맞는 상태다.**

### 4) 첫 admin 키를 발급한다 (CLI)

```bash
docker compose -f compose.yaml -f compose.prod.yaml \
  run --rm --no-deps core python -m app.apikey_cli issue --role admin --label bootstrap
```

평문은 **이때 한 번만** 나온다. DB 에는 sha256 만 남는다. 파일로 저장하고 권한을 조인다:

```bash
umask 077
printf '%s' 'ck_xxxxxxxx.yyy' > data/admin.key   # *.key 는 .gitignore 대상
```

이후 운영 스크립트는 키를 환경에서 받는다:

```bash
export CAPNET_API_KEY_FILE=./data/admin.key      # 또는 CAPNET_API_KEY=...
```

> 인자로 넘기지 않는다 — `ps` 에 남는다. 환경변수보다 파일이 낫다 — `docker inspect` 에 안 뜬다.

### 5) 기기를 등록하고 증서를 준다

```bash
scripts/node_onboard.sh --name gpu-01 --tier M --domain team
```

`data/node-secrets/gpu-01.credential` (0600) 이 떨어지고, Node 런타임에 넣을 환경변수가 출력된다.
등급(`trust_domain` · `compute_tier_max`)은 **Core 가 부여한다** — Node 가 주장하는 값을 믿지 않는다 (절대규칙 4).

기기 쪽에서:

```bash
NODE_CREDENTIAL_FILE=/run/secrets/node.credential   # 파일로 넣는다
CORE_URL=https://core.example.com
```

### 6) Agent 사슬을 세운다

```bash
scripts/node_bind.sh --node <uuid> --weights eurosat_scratch.safetensors
```

Agent 등록 → 실게이트 PASSED → 증서 → Node 바인딩. 이 사슬이 서기 전에는 **배정이 가지 않는다.**
게이트는 team gate-runner 에서만 돈다 (절대규칙 8).

### 7) 확인

```bash
curl -s localhost:8000/v1/ops/status \
  -H "Authorization: CapNet-Key $(cat data/admin.key)" | python3 -m json.tool
```

- `enforcement.api_key` · `enforcement.node_credential` 이 **둘 다 true**
- `nodes_without_credential` 이 **0**
- `api_keys_active` 가 1 이상
- `drift_routable` · `arch_unbound_routable` 이 **0**

합계가 아니라 **기기 단위**로 「왜 이 기기가 실행 가능한가」를 보려면 (S2):

```bash
curl -s localhost:8000/v1/ops/safety \
  -H "Authorization: CapNet-Key $(cat data/admin.key)" | python3 -m json.tool
```

- `by_task_domain.team.nodes_routable` — **내 team 요청을 실제로 돌릴 수 있는 기기 수**
- 기기마다 `accepts_task_domains`(받을 수 있는 요청 도메인) · `routable_pairs`
  (지금 배정될 수 있는 Agent·능력 쌍) · `risks`
- `routable_pairs` 는 `claim` 의 후보 조건을 그대로 센다 — **조회면과 배정이 갈라지지 않는다**

`developer` 이상이 필요하다. 증서는 `key_prefix`·만료·마지막 사용만 나간다.

---

## 2. 실측 (2026-08-12 · 빈 볼륨 · 격리 프로젝트)

| # | 확인한 것 | 결과 |
|---|-----------|------|
| 1 | postgres 호스트 미노출 | ✅ |
| 2 | `CAPNET_AUTO_MIGRATE=0` 이면 스키마 안 올라감 | ✅ `schema_migration` 없음 |
| 3 | 운영자 수동 `migrate up` → `verify` | ✅ 9개 적용·체크섬 일치 |
| 4 | `/health` 는 인증 없이 200 | ✅ (죽었는지 보려면 열려 있어야 한다) |
| 5 | 무인증 `POST /v1/nodes` · `/v1/agents` | ✅ **401** |
| 6 | 가짜 키 | ✅ **401** |
| 7 | CLI 로 첫 admin 키 발급 | ✅ |
| 8 | admin 키로 쓰기 | ✅ |
| 9 | 증서 발급 → 파일 주입 | ✅ |
| 10 | 증서 없는 Node 의 `assignments` | ✅ **401** (사칭 차단) |
| 11 | 증서 넣은 Node 하트비트 | ✅ `fresh` |
| 12 | 강제 모드에서 `demo.sh` 완주 | ✅ `PASSED acc=0.8500` · 증적 SUCCEEDED |

---

## 3. 백업 — 무엇을 넣고 무엇을 빼나

볼륨이 둘이고 **정책이 다릅니다.**

| 볼륨 | 내용 | 백업 |
|------|------|------|
| `capnet_pg` | 증적 DB — 해시·누가·어디로·언제 | **포함.** 이게 제품 가치다 |
| `capnet_inputs` | 입력 **바이트** | **제외하거나 단기 보존.** 어차피 종결 후 7일에 GC 가 지운다 |

입력 바이트를 장기 백업하면 「바이트는 휘발성」이라는 보존 정책이 백업 쪽에서 무너집니다 —
지운 데이터가 백업에 남습니다. 증적(`task_input` 행)은 DB 에 있으므로 바이트를 빼도
「어디로 갔는지」에는 그대로 답할 수 있습니다.

## 4. 입력 보존·GC

| 항목 | 값 |
|------|-----|
| 크기 | 기본 **32MiB** · `capability.max_input_bytes` 로 조정 · 절대 상한 **256MiB** |
| 바이트 보존 | 종결(`finished_at`) 후 **7일** |
| 고아 입력 | 업로드 후 **24시간** (task 에 연결되지 않은 것) |
| 미완료 task | **72시간** 후 `TIMEOUT` 종결 → 그때부터 7일 |
| GC 주기 | `CORE_GC_INTERVAL_S` 기본 300초 · 배치 `CORE_GC_BATCH` 기본 50 |

**받을 형식을 선언하지 않은 능력은 업로드를 받지 않습니다** (0012 · D8′). 계약에
`input_schema.mediaTypes` 배열이 있어야 하고, 없으면 `POST /v1/inputs` 가 400 입니다.
`caseId` 데모 경로는 이 규칙 밖입니다 — 업로드가 없습니다.

```sql
-- 능력별 선언 확인
SELECT code, version, input_schema->'mediaTypes' AS media_types, max_input_bytes
  FROM capability ORDER BY code, version;
```

업로드는 **받는 즉시 디스크로 흘립니다.** 200MB 를 올려도 Core 의 최대 상주 메모리가
늘지 않는 것을 실측했습니다 (`VmHWM` 증가 0MB). 그래서 `core` 에 별도 `mem_limit` 을
걸지 않았습니다 — 상한(256MiB)이 메모리가 아니라 디스크에만 걸립니다.

무엇이 왜 언제 지워지는지는 SQL 로 봅니다:

```sql
SELECT reason, due_at, byte_size FROM task_input_purge_due ORDER BY due_at;
```

즉시 삭제가 필요하면 (사고·고객 요청):

```bash
curl -X POST localhost:8000/v1/inputs/<id>/purge -H "Authorization: CapNet-Key $(cat data/admin.key)"
```

**바이트만 지워지고 행·해시는 남습니다.**

> **한도는 입력이 하나라도 들어온 뒤에는 못 바꿉니다.** `task_input` 이 `capability
> (id, max_input_bytes)` 를 복합 FK 로 참조하므로 PostgreSQL 이 UPDATE 를 거절합니다.
> 이미 수집한 입력이 「어떤 계약 아래 들어왔는지」가 사후에 바뀌지 않게 하려는 것이고,
> 한도를 바꾸려면 새 `@version` 능력을 등록합니다.

## 5. 알려진 한계

- **기기가 데이터를 남기지 않는다는 보장은 없다.** 추론은 평문을 요구하고, TEE 없이는 원리적으로 불가하다.
  제품이 보장하는 것은 «승인 도메인 밖으로 라우팅되지 않는다 · 실행 증적이 남는다» 까지다.
- **조회면에도 역할이 걸린다** (read-auth). 함대·작업·증서 조회는 `developer`/`admin` 키가 필요하고,
  `GET /v1/tasks/{id}` 는 **자기 작업만** 보인다(남의 것은 404).
  **최소 UI 는 이제 강제 모드에서도 쓸 수 있다** — 화면의 키 입력줄에 키를 넣는다.
  키는 브라우저 `sessionStorage` 에만 두고 서버는 저장하지 않는다.
  자동화·운영 스크립트는 계속 `scripts/` + `ccurl`(키 주입)이다.
- **조직 경계는 섰다** (D24 · `0017`). 작업은 **같은 조직 기기 또는 팀 공용 기기(`org_id IS NULL`)**
  에서만 돌고, 판정은 `ck_assignment_org` 와 복합 FK 가 한다. 조회도 조직으로 걸린다 —
  남의 조직 작업은 404, 함대 목록은 자기 조직 + 공용만.
  **남은 것:** 조직을 안 쓰는 배포는 그대로 돈다(`org_id` NULL 허용 · `NOT NULL` 승격 없음).
  조직별 쿼터·요금은 없다 (경제는 비기초 — D19).
- **본문 검증이 인증보다 먼저 돈다.** 잘못된 스키마로 부르면 인증 없이도 `422` 가 온다 (쓰기는 일어나지 않는다).
  스키마 유효성 오라클이 되므로, 공개망에 둘 때는 앞단에서 rate limit 을 건다.
- **Node 증서 회전은 런북이 생겼다** → [`operate-node.md` §2](./operate-node.md). 다만 **무중단은 안 된다** —
  Node 당 활성 증서가 하나라(부분 UNIQUE) 새 증서를 먼저 발급해 겹칠 수 없다. 짧은 중단을 인정하고 돈다.
- **관리 API 키 회전 순서는 아직 미정.** `apikey_cli revoke --prefix` 로 폐기는 되지만,
  운영 스크립트가 키를 파일에서 읽으므로 교체 시점을 맞추는 순서가 문서에 없다.
- **백업·복구 절차 없음.** `capnet_pg` 볼륨 스냅샷 정책을 정해야 한다.
- **TLS 종단 없음.** Core 는 평문 HTTP 로 뜬다. 공개망에서는 앞에 리버스 프록시를 둔다.
