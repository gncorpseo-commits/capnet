-- 0012 · 입력 MIME 선언 (리뷰 Decision 2 · D8′)
--
-- 무엇이 문제였나
--   `POST /v1/inputs` 는 계약이 `input_schema.mediaTypes` 를 선언한 경우에만 MIME 을 대조하고,
--   **선언이 없으면 통과**시켰다. 「계약이 안 정했으면 코드가 정하지 않는다」는 뜻이었는데,
--   결과는 **아무 MIME 이나 받는 구멍**이다 — D8′(비통제 수집 금지)와 어긋난다.
--
-- 결정 (리뷰)
--   미선언이면 업로드를 **400 으로 거절한다.** 그러면 기존 능력이 선언을 갖고 있어야 한다.
--   `image.classify` 는 골든셋이 JPEG 이고 실측한 것도 JPEG 뿐이라 **`image/jpeg` 만** 선언한다.
--   PNG 등을 넣으려면 그 형식으로 실제 추론을 돌려 본 뒤 계약에 추가한다 (측정 없이 주장 없음).
--
--   `caseId` 데모 경로는 이 규칙 밖이다 — 업로드가 없고 Node 로컬 골든셋을 쓴다.
--
-- 왜 @2 로 올리지 않나
--   D3(전처리는 계약의 일부, 바꾸려면 `@2`)는 **채점·실행 조건을 바꿀 때**의 규칙이다.
--   여기서 하는 것은 이미 사실인 것(골든셋이 JPEG 이다)을 **명시**하는 추가이고,
--   전처리·골든셋 해시·임계값은 하나도 건드리지 않는다. 새 형식을 **허용**하려면 그때 버전을 올린다.
--
-- 데이터 변경만 — DDL 없음. jsonb 병합이라 멱등하다.

UPDATE capability
   SET input_schema = input_schema || '{"mediaTypes":["image/jpeg"]}'::jsonb
 WHERE code = 'image.classify'
   AND input_schema -> 'mediaTypes' IS NULL;

COMMENT ON COLUMN capability.input_schema IS
    '입력 계약. `mediaTypes` 배열이 있으면 업로드 MIME 을 그 목록과 대조한다 — '
    '**선언이 없으면 업로드를 거절한다** (0012 · D8′). caseId 데모 경로는 해당 없음.';
