-- 0018 · freeform 능력에 골든 품질 프로파일을 붙이지 못하게 한다 (Decision 2-F)
--
-- 무엇이 문제였나
--   D20(`0010`)이 `quality_profile ∈ {golden, none}` 을 만들 때, 「골든을 붙일 수 있는
--   출력 종류」를 묶는 제약은 넣지 않았다. `ck_capability_mvp_scoreable` 이 있지만
--   그건 **`mvp_eligible` 만** 묶는다 — 즉 MVP 통계 대상이 아니면 아무 제한이 없었다.
--
--   실측(코드 확인): `output_kind='freeform'` + `quality_profile='golden'` 이
--   **DB 에서도 앱에서도 통과한다.** `apps/core/app/capability.py` 에 막는 분기가 없고,
--   `freeform` 이라는 문자열은 `_OUTPUT_KINDS` 열거에만 등장한다.
--
--   그래서 `text.summarize` 같은 능력에 골든셋 40건과 `min_accuracy` 를 달고
--   **「품질 하한을 보장한다」고 쓸 수 있었다.** 그런데 freeform 출력에는 채점 함수가 없다.
--   요약문이 「맞다/틀리다」로 갈리지 않기 때문이다 — 골든셋 정의서 §6 의 채점 규칙
--   (결정적·부분점수 없음·퍼지 매칭 금지)이 애초에 성립하지 않는 출력 종류다.
--
--   즉 **잴 수 없는 것에 점수를 붙이고 그 점수로 보장을 파는 경로**가 열려 있었다.
--   이건 골든셋의 알려진 세 구멍(표본·분포·게이밍)과 다른 종류의 문제다.
--   그 셋은 「측정이 약하다」이고, 이건 「측정이 아예 없는데 있는 척한다」이다.
--
-- 왜 지금인가
--   능력 카탈로그를 52 로 넓히면 freeform 이 **16개** 생긴다(`docs/spec/capability-catalog.md`).
--   지금까지 능력이 사실상 `image.classify` 하나였기 때문에 이 구멍이 드러나지 않았을 뿐이다.
--   등록 경로를 열기 **전에** 막는다.
--
-- 무엇을 막지 않는가
--   `structured` 는 **막지 않는다.** 임베딩·검출·랭킹은 채점 가능한 출력이 있다
--   (코사인 유사도·IoU·nDCG). 지금 채점기가 없다는 것과 원리적으로 못 잰다는 것은 다르다.
--   막는 것은 `freeform` 하나뿐이며, 그 근거는 「정답 집합을 정의할 수 없다」이다.
--
-- 추가만 (절대규칙 1) — CHECK 1. 삭제·완화 없음.
--   기존 행에 위반이 없다는 것을 먼저 확인하고 건다. 데모 능력(`image.classify` ·
--   `image.classify@2`)은 `closed_set_labels` 라 영향이 없다.

DO $$
DECLARE
    bad INT;
BEGIN
    SELECT count(*) INTO bad
      FROM capability
     WHERE quality_profile = 'golden'
       AND output_kind = 'freeform';

    IF bad > 0 THEN
        -- 여기 걸리면 데이터를 먼저 정리해야 한다. 제약을 NOT VALID 로 우회하지 않는다.
        RAISE EXCEPTION
            'freeform 능력에 golden 프로파일이 % 건 있다 — 먼저 quality_profile 을 none 으로 내린다', bad;
    END IF;
END $$;

ALTER TABLE capability
    ADD CONSTRAINT ck_capability_golden_scoreable
    CHECK (quality_profile <> 'golden' OR output_kind <> 'freeform');

COMMENT ON CONSTRAINT ck_capability_golden_scoreable ON capability IS
    '골든 프로파일은 채점 가능한 출력에만 (Decision 2-F). freeform 은 정답 집합을 정의할 수 없어 제외한다.';
