# Contributing to CapNet

팀 지엔 협업은 **GitHub 사용 표준 가이드**를 따른다.

- **Wiki:** [Team GitHub Guide](https://github.com/gncorpseo-commits/capnet/wiki/Team-GitHub-Guide)
- **레포 사본:** [docs/guide/github-team-guide.md](docs/guide/github-team-guide.md)
- **문서 지도:** [docs/INDEX.md](docs/INDEX.md)

## 클론 후 1회: 훅 설치

```bash
git config core.hooksPath .githooks
```

`main`·`master` 직접 push 를 막는다. 팀 가이드 §3 이 문서로만 적어 두던 규칙을
강제 지점으로 옮긴 것이다 (issue #23 · SD-012 — 커밋 18건이 그대로 들어갔다).

긴급 시에만 `ALLOW_MAIN_PUSH=1 git push ...` 로 우회하고 **사후 Issue 를 남긴다.**


## 초단 요약

1. Issue 먼저 (`W1:` …).
2. 브랜치 `finn/<topic>` · `toma/<topic>` · `pl/<topic>` (`main` 직접 push 금지).
3. 커밋 author는 `finn` / `toma` / `pl` (전역 git config 금지 — `-c user.name=...` 권장).
4. PR → 상대 **명목 승인** `LGTM (finn|toma|pl)`. **W1–W3.5 fast-track:** `docs:`/`chore:`는 LGTM 생략, Must는 주 단위로 묶어 `gh pr merge --squash`.
5. **master**가 Squash merge (웹 또는 `gh pr merge --squash --delete-branch`).

Contest Must·claim `INSERT … SELECT`·게이트 사슬은 `STATE.md` / `docs/context-handoff.md` 참고.
