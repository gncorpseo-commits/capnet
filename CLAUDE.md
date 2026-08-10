# CapNet — 프로젝트 규칙

흩어져 있는 기기를 검증된 AI 실행 자원으로 묶는 오픈소스 실행 계층.
2026 오픈소스 개발자대회 출품작 (팀 지엔, 접수번호 915). MVP 목표일 **2026-08-27**.

스택: Python 3.11+ / FastAPI / PostgreSQL 16 / Docker Compose

---

## 절대 규칙

이것을 어기면 프로젝트의 핵심 주장이 무너진다. 우회하지 말고, 막히면 멈추고 물어본다.

1. **`docs/spec/schema.sql`의 제약을 약화하지 않는다.** 끄거나, 삭제하거나, `NOT VALID`로 우회하지 않는다. 제약 **추가**는 허용된다. 기존 제약을 건드려야 한다면 먼저 근거와 함께 제안한다.

2. **`assignment`·`gate_run` INSERT는 `INSERT ... SELECT`만 쓴다.** 스냅샷 컬럼을 애플리케이션이 계산해 넣지 않는다. ORM으로 객체를 만들어 저장하는 방식도 금지. 앱은 후보를 고르기만 하고 판정은 DB가 한다. 패턴은 `@docs/error/pitfalls.md`.

3. **`compute_tier`를 앱에서 직접 비교하지 않는다.** 텍스트 정렬은 `L < M < S`로 의도와 반대다. 반드시 `tier_compatible` 행렬과 복합 FK에 맡긴다.

4. **Node는 자기 등급을 주장할 수 없다.** `trust_domain`과 `compute_tier_max`는 Core가 부여한다. Node가 보낸 값을 그대로 신뢰해 기록하는 코드를 쓰지 않는다.

5. **가중치는 safetensors만 로드한다.** `.pt` / `.pth` / pickle 은 로드 자체가 임의 코드 실행이므로 거부한다.

6. **사전학습 가중치를 쓰거나 동봉하지 않는다.** EuroSAT scratch 학습만. 대회 2차 라이선스 검증 대비.

7. **입력은 allowlist된 `datasetId`만 받는다.** 자유 업로드 경로를 만들지 않는다.

8. **게이트는 team gate-runner Node에서만 실행한다.** 제출자 Node에서 골든셋을 돌리면 게이팅이 무력화된다.

## 작업 방식

- **탐색 → 계획 → 실행.** 바로 코드를 쓰지 않는다. 여러 파일을 고칠 때는 변경 목록을 먼저 제시하고 승인을 받는다.
- config 수정, 테이블 선택, 의존성 추가는 **먼저 묻는다.**
- 주석은 한국어로 쓴다.
- 큐 claim은 Core 워커만 한다. Node는 큐를 pull하지 않는다. `FOR UPDATE SKIP LOCKED` 필수.
- 작업을 마치면 `STATE.md`를 갱신한다.

## 저장소 규칙

- GitHub 원격 계정은 **gncorpseo-commits**. 커밋 서명 역할 풀은 **finn · toma · pl** (동급). merge는 **master**.
- 커밋 시 **로컬 `git config`를 바꾸지 말고** `-c`로만 서명한다. 이메일은 팀 noreply만 쓴다 (`finn@…` 등 개인 noreply는 타 계정에 붙을 수 있음):

  ```text
  git -c user.name=finn -c user.email=252522396+gncorpseo-commits@users.noreply.github.com commit -m "…"
  ```

  `user.name`만 finn/toma/pl로 바꾸고 email은 위와 동일. 상세는 `docs/guide/github-team-guide.md`.
- `git add -A` / `git add .` 는 전역 훅이 차단한다. **명시적 경로로만 스테이징한다.** 훅을 끄지 않는다.
- 버전 이력은 `docs/history/CHANGELOG.md` 단독. README에 중복해 적지 않는다.
- 세션 상태는 `STATE.md`, 결정·미결은 `docs/context-handoff.md`, 문서 지도는 `docs/INDEX.md`. 역할을 섞지 않는다.
- 의존성을 추가하는 커밋에서 `THIRD-PARTY-LICENSES.md`에 한 줄을 같이 넣는다. 예외 없음.

## 보안

- 시크릿을 코드에 하드코딩하지 않는다. 로그·커밋 메시지·출력에 노출하지 않는다.
- 다음은 실행 전 반드시 확인을 받는다: `git push --force`, 브랜치·파일 대량 삭제, DB 마이그레이션·시드 실행, 배포, 외부 API 실제 발송, `.env` 등 시크릿 파일 수정.

---

## 더 필요할 때

배경·결정 근거·함정은 자동으로 읽히지 않는다. 필요할 때 부른다.

    @docs/INDEX.md
    @docs/context-handoff.md
    @docs/error/pitfalls.md
