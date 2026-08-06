# Lessons learned

항목 나열이 아니라 **다음에 같은 실수를 줄이는 원칙**만 둔다.  
세부 사례는 [`register.md`](./register.md).

**갱신:** 2026-08-07

1. **산출물 존재 ≠ 검증 가능.** 파일만 채우고 생성 경로를 생략하면 2차 라이선스·재현에서 약해진다. SBOM·NOTICE·임계는 도구/실측과 같은 커밋에 묶는다.
2. **호스트 도구가 없으면 먼저 설치를 묻는다.** Docker 안 Python ≠ 호스트 PATH. Store stub `python.exe`를 “설치됨”으로 읽지 않는다.
3. **Scope Decision과 Technical Debt를 같은 문장에 쓰지 않는다.** A/B 보류는 범위, 수동 SBOM은 빚이다. CapNet은 투명성이 제품이므로 분류가 자산이다.
4. **가정 임계를 실측 위에 두지 않는다.** 바를 낮출 때는 보고서에 보정 이유를 쓰고, dummy PASSED를 품질로 주장하지 않는다.
5. **DDL·스키마 약화·승인 전 credential 구현은 “빠름”의 대상이 아니다.** 막히면 멈추고 묻는다.
