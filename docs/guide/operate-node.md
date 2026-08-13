# Node 운영 — 등록부터 능력 호출까지

> v제품-1 운영화. 「기기를 함대에 넣고, 능력으로 일을 시킨다」의 실제 절차.
> 갱신: 2026-08-11 (초판)
>
> 관련: [`migrations.md`](./migrations.md) · [`../design/product-distribution.md`](../design/product-distribution.md) ·
> [`../design/node-credential-draft.md`](../design/node-credential-draft.md)

---

## 0. UI 로 할 수도 있다

Core 가 최소 UI 를 서빙한다 (P2-3 호출면). `http://<core>:8000/ui/nodes.html`

| 화면 | 무엇 |
|---|---|
| **Node** (`/ui/nodes.html`) | 등록 · 함대 상태(생존·증서) · 증서 발급/폐기 |
| **능력 호출** (`/ui/call.html`) | Capability 로 요청 · 결과와 **증적** · dummy 경고 |

외부 자산(CDN·폰트)을 쓰지 않는다 — 내부망·오프라인에서 그대로 뜬다. 새 의존성도 없다.
UI 가 못 하는 것은 **Agent 게이트·바인딩**이다 (가중치가 기기에 있어야 하므로 터미널 작업).

---

## 0.1 한 장 요약

```bash
scripts/node_onboard.sh --name gpu-01 --domain team --tier M   # 등록 + 증서
scripts/node_bind.sh --node <uuid> --weights eurosat_scratch.safetensors   # 게이트 + 바인딩
scripts/call.sh ic1-0001                                        # 능력 호출
```

세 단계가 각각 무엇을 세우는지가 이 문서의 내용이다.

---

## 1. 왜 세 단계인가

Node 를 등록**만** 하면 일이 가지 않는다. 배정에는 사슬이 다 서야 한다.

```text
Agent 등록 → 실게이트 PASSED → 증서(agent_capability_passed) → Node 바인딩(agent_node_ready)
                                                                          ↓
Task(능력·신뢰도메인) ──► Core 워커가 배정 ──► assignment ──► Node 가 가져가 실행
```

`claim` 은 이 사슬이 **전부** 선 조합만 고른다. 하나라도 없으면 그 Node 로는 일이 가지 않는다 —
그리고 그건 버그가 아니라 계약이다.

---

## 2-A. 초대로 들어오기 (`invited` · G2)

관리 키가 **없는 사람**이 자기 기기를 넣는 경로다. 러닝크루 시나리오가 이것이다.

> **등급은 초대장에 박힌다.** 신청자는 고르지 않는다 (절대규칙 4).
> 소진 요청 본문에는 `trust_domain` 필드가 **아예 없다.**

**관리자 — 초대 발행** (평문은 이때 한 번만 나온다)

```bash
curl -sf -X POST $CORE/v1/nodes/invites \
  -H "Authorization: CapNet-Key $(cat data/admin.key)" \
  -H 'content-type: application/json' \
  -d '{"trust_domain":"tenant","compute_tier_max":"M","label":"러닝크루 3기","ttl_days":7}'
```

| 기본값 | |
|---|---|
| `trust_domain` | `tenant` — **`team` 은 초대로 만들 수 없다** (DB 가 거절) |
| `compute_tier_max` | `M` |
| `ttl_days` | **7** (사람이 들고 다닌다 — 증서보다 길다) |
| `max_redemptions` | **1** — 초대장 하나가 기기 하나. 열 명이면 열 장을 발행한다 |

**초대받은 사람 — 소진** (관리 키가 **필요 없다**)

```bash
curl -sf -X POST $CORE/v1/nodes/redeem \
  -H "Authorization: CapNet-Invite ci_xxxxxxxx.yyy" \
  -H 'content-type: application/json' \
  -d '{"name":"crew-laptop-1","device_type":"PC_GPU"}'
```

Node 와 **증서를 함께** 받는다 (원스텝). 증서 평문도 이때 한 번만 나온다 —
`data/node-secrets/<name>.credential` 에 0600 으로 떨구고 §2 의 취급 규칙을 따른다.

**초대 관리**

```bash
curl -s $CORE/v1/nodes/invites -H "Authorization: CapNet-Key $KEY"        # 상태 목록
curl -sf -X POST $CORE/v1/nodes/invites/<id>/revoke \
  -H "Authorization: CapNet-Key $KEY" -H 'content-type: application/json' \
  -d '{"reason":"오발행"}'
```

상태는 `USABLE` · `EXPIRED` · `REDEEMED` · `REVOKED` 넷이다.

> **이 경로만 관리 키 없이 열린다.** 그래서 완화가 겹쳐 있다 — 만료 · 1회용 · 폐기 ·
> `audit_log` 증적, 그리고 소진 판정은 **DB 의 조건부 UPDATE** 가 한다.
> 초대로 들어온 기기는 `ck_gate_runner_team` 때문에 **채점자가 될 수 없다** (절대규칙 8).

---

## 2. 등록 + 증서 (`node_onboard.sh`)

```bash
scripts/node_onboard.sh --name gpu-01   --domain team   --tier M
scripts/node_onboard.sh --name tenant-a --domain tenant --tier M   # source=invited 자동
```

무엇이 일어나나

1. `POST /v1/nodes` — **등급은 Core 가 부여한다.** Node 는 자기 등급을 주장할 수 없다 (절대규칙 4)
2. `POST /v1/nodes/{id}/credentials` — 평문 시크릿은 **이때 한 번만** 나온다 (C3)
3. 시크릿을 `data/node-secrets/<name>.credential` 에 0600 으로 떨군다 (gitignore 대상)
4. Node 런타임에 넣을 환경변수를 출력한다

### 등급 조합 제약

`ck_trust_provision_align` 이 막는다 — 문서가 아니라 DB 가 판정한다.

| trust_domain | 허용 provision_source |
|---|---|
| `team` | `team` |
| `tenant` | `team` · `invited` |
| `public` | 아무거나 |

그리고 `is_gate_runner` 는 `provision_source='team'` 에서만 참일 수 있다 (`ck_gate_runner_team`).

### 시크릿 취급

- **파일로 주입한다** (`NODE_CREDENTIAL_FILE`). 환경변수 직접 주입(`NODE_CREDENTIAL`)도 되지만,
  프로세스 목록·`docker inspect` 에 노출된다
- 잃어버리면 **복구할 수 없다.** 폐기 후 재발급한다
- 회전 = 폐기 → 재발급. Node 당 활성 증서는 하나다 (부분 UNIQUE)

### 증서 회전 런북

> **무중단 회전은 지금 구조에서 안 된다.** `node_credential_active_idx` 가 Node 당 활성 증서를
> **하나로** 강제하므로 새 증서를 먼저 발급해 겹칠 수 없다. 겹치게 하려면 스키마가 바뀐다 —
> 그건 별 Decision 이다. 아래는 **짧은 중단을 인정하고** 안전하게 도는 순서다.

Node 런타임은 증서를 **임포트 시점에 한 번** 읽는다 (`_load_credential`). 파일만 바꾸면
바뀌지 않는다 — 재기동이 필요하다.

```bash
export CORE=http://127.0.0.1:8000
export NODE_ID=<uuid>
K=(-H "Authorization: CapNet-Key $(cat data/admin.key)")
```

**1) 새 일이 가지 않게 한다.** Node 를 멈추면 heartbeat 이 끊기고,
`claim` 은 신선하지 않은 기기를 고르지 않는다 (`REQUIRE_LIVE_NODE=1` 기본).

```bash
docker compose -f compose.yaml -f compose.prod.yaml stop node-m-team
```

**2) 「일이 안 간다」가 실제로 성립하길 기다린다.** 멈춘 **직후에는 아직 `is_fresh=true`** 다 —
마지막 heartbeat 이 아직 신선하기 때문이다. `heartbeat_timeout_s`(기본 45초)가 지나야 내려간다.
그 전에는 `claim` 이 이 기기를 여전히 고를 수 있다. **`is_fresh=false` 와 `leases_live=0` 을
둘 다 확인한다.**

진행 중이던 lease 는 최대 60초 뒤 만료되고, 워커가 회수해 task 는 `QUEUED` 로 돌아가
**다른 기기가 시도**한다 (일이 사라지지 않는다).

```bash
curl -s "${K[@]}" $CORE/v1/ops/safety \
  | python3 -c 'import json,sys,os
d=json.load(sys.stdin)
n=[x for x in d["nodes"] if x["node_id"]==os.environ["NODE_ID"]][0]
print("leases_live=", n["leases_live"], "is_fresh=", n["is_fresh"])'
```

`leases_live=0` **그리고** `is_fresh=false` 가 될 때까지 기다린다.

> 실측 (2026-08-14 · 제품 프로파일): 멈춘 직후 `leases_live=0 is_fresh=True` 였다.
> 그 상태에서 폐기하면 45초 창 안에 배정이 갈 수 있고, 그 배정은 401 로 깨진다.

**3) 폐기 → 재발급.** 평문은 이때 한 번만 나온다.

```bash
curl -sf -X POST "${K[@]}" $CORE/v1/nodes/$NODE_ID/credentials/revoke \
  -H 'content-type: application/json' -d '{"reason":"rotation"}' >/dev/null

umask 077
curl -sf -X POST "${K[@]}" $CORE/v1/nodes/$NODE_ID/credentials \
  -H 'content-type: application/json' -d '{"label":"rotated"}' \
  | python3 -c 'import json,sys; sys.stdout.write(json.load(sys.stdin)["secret"])' \
  > data/node-secrets/node-m-team.credential
```

**4) 재기동.**

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d node-m-team
```

**5) 확인 — 한 곳에서 본다** (S2). `credential_valid=true` · `is_fresh=true` ·
`risks` 가 비어 있어야 한다.

```bash
curl -s "${K[@]}" $CORE/v1/ops/safety \
  | python3 -c 'import json,sys,os
d=json.load(sys.stdin)
n=[x for x in d["nodes"] if x["node_id"]==os.environ["NODE_ID"]][0]
print(n["credential_valid"], n["is_fresh"], n["key_prefix"], n["risks"])'
```

**폐기만 하고 재발급을 잊으면** 강제 모드에서 그 Node 는 401 을 받는다 — 조용히 놀지 않고
`/v1/ops/safety` 의 `risks` 에 뜬다. 그게 3단계와 5단계를 붙여 둔 이유다.

> 순서를 지키지 않으면(먼저 폐기하고 Node 를 안 멈추면) 진행 중이던 배정이 401 로 깨진다.
> task 는 재시도로 살아나지만 `attempt_no` 를 헛되이 쓴다 (상한 기본 5).

---

## 3. 게이트 + 바인딩 (`node_bind.sh`)

```bash
scripts/node_bind.sh --node <uuid> --weights eurosat_scratch.safetensors
```

1. 러너가 들고 있는 가중치의 sha256 을 읽는다 (선언이 아니라 실측)
2. Agent 를 등록한다
3. **team gate-runner 에서** 실게이트를 돌린다 (절대규칙 8 — 제출자 Node 에서 돌리면 게이팅이 무력화된다)
4. 통과했을 때만 대상 Node 에 바인딩한다

미통과면 바인딩하지 않고 종료한다 (exit 2). 미통과 Agent 에는 배정이 **가지 않는다** — FK 가 막는다.

---

## 4. 능력 호출 (`call.sh`)

```bash
scripts/call.sh ic1-0001
scripts/call.sh ic1-0007 --capability image.classify --version 2   # tenant 계약
```

**Agent 를 지정하지 않는다.** 「모델 이름이 아니라 Capability 로 요청한다」가 제품의 주장이고
(`product-distribution.md` §4), 이 스크립트가 그 경로다. 어느 기기가 실행할지는 Core 가 정한다.

출력에 증적이 함께 나온다 — `node` · `agent` · `weights_sha256`.
`dummy=true` 면 **실제 추론이 아니다**(placeholder 가중치). 그 경우 exit 2 로 떨어진다.

> `demo.sh` 와 다르다. `demo.sh` 는 Agent 를 만들고 **지정해서** 부른다 (증명용 · UC-7).

---

## 5. 증서 강제 켜기

Core 에 `REQUIRE_NODE_CREDENTIAL=1` 을 준다. 그러면 증서 없는 Node 호출은 **401** 이다.

**켜기 전에 모든 Node 에 증서가 주입돼 있어야 한다.** 확인:

```bash
curl -s $CORE/v1/nodes-credentials    # credential_valid 가 전부 true 인지
curl -s http://<node>:8001/health     # credential_present 가 true 인지
```

기본은 꺼짐이다 — 데모·로컬 compose 는 증서 없이 돈다. 다만 **꺼져 있어도 토큰이 오면 항상 검증한다.**
「강제가 꺼져 있으니 잘못된 증서도 통과」하는 구간은 없다.

| 상황 | 기본 | 강제 |
|---|---|---|
| 증서 없음 | 200 | **401** |
| 올바른 증서 | 200 | 200 |
| 위조·폐기·만료 | **401** | **401** |
| 다른 Node 사칭 | **403** | **403** |

---

## 6. 자주 막히는 곳

| 증상 | 원인 | 확인 |
|---|---|---|
| Task 가 QUEUED 에서 안 움직인다 | 사슬이 덜 섰다 (게이트·바인딩·증서 중 하나) | `nodes-liveness` · `agent_capability_passed` |
| 배정은 되는데 `dummy=true` | placeholder 가중치 | Node `/health` 의 `weights_sha256` |
| tenant Task 가 계약을 못 쓴다 | `capability.trust_domain_min` 이 `team` | `image.classify@2`(min=tenant) 를 쓴다 |
| 등록이 400 | 등급 조합 위반 | §2 표 · `ck_trust_provision_align` |
| heartbeat 401 | 증서 없음/폐기/만료 | `nodes-credentials` |
| heartbeat 403 | **다른 Node 의 증서** | `NODE_ID` 와 증서 주인이 같은지 |

---

## 7. 아직 없는 것 (정직하게)

- **자동 재시도 정책** — 만료 lease 는 회수되지만(SD-011), 재할당 횟수·백오프 정책은 없다
- **모니터링** — `nodes-liveness`·`nodes-credentials` 조회면뿐이다. 알림·대시보드 없음
- **셀프 온보딩** — Node 가 스스로 등록하는 경로는 없다. 의도다 (D7 · 기획서 §4.2 Non-goal)
- **시크릿 배포 자동화** — 파일을 사람이 옮긴다. 비밀 관리자 연동은 별건이다
