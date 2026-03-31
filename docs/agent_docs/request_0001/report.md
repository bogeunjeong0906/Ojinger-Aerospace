# request_0001 실행 보고

## 구현 요약

`.github/ref`에 격리되어 있던 프로젝트 전용 customization 내용을 표준 `.github` 경로로 이관했다.

생성한 파일:

- `.github/copilot-instructions.md`
- `.github/instructions/project/ojinger-kos-html-cheatsheet.instructions.md`
- `.github/skills/ojinger-kos-nonhtml-cheatsheet/SKILL.md`
- `.github/skills/ojinger-kos-quality-inspection/SKILL.md`

삭제한 파일:

- `.github/ref/copilot-instructions.md`
- `.github/ref/instructions/copilot-instructions.md`
- `.github/ref/instructions/kos-nonhtml-cheatsheet.instructions.md`
- `.github/ref/instructions/kos-quality-inspection.instructions.md`

## 내용 이관 대응표

| 기존 위치 | 신규 위치 | 비고 |
|-----------|-----------|------|
| `.github/ref/copilot-instructions.md` | `.github/copilot-instructions.md` | 프로젝트 전역 always-on 규칙으로 정리 |
| `.github/ref/instructions/copilot-instructions.md` | `.github/instructions/project/ojinger-kos-html-cheatsheet.instructions.md` | 역할이 드러나는 이름과 project 하위 경로로 이동 |
| `.github/ref/instructions/kos-nonhtml-cheatsheet.instructions.md` | `.github/skills/ojinger-kos-nonhtml-cheatsheet/SKILL.md` | 절차형 workflow를 skill로 전환 |
| `.github/ref/instructions/kos-quality-inspection.instructions.md` | `.github/skills/ojinger-kos-quality-inspection/SKILL.md` | 절차형 inspection workflow를 skill로 전환 |

## 적용한 구조 전략

- 전역 규칙은 `.github/copilot-instructions.md`에 집중했다.
- 프로젝트 전용 file instruction은 `.github/instructions/project/` 아래로 분리했다.
- 프로젝트 전용 skill은 `.github/skills/` 아래에서 `ojinger-` prefix로 구분했다.

이 방식으로 범용 에이전트용 customization과 프로젝트 전용 customization을 사람이 봐도 구분할 수 있게 만들었다.

## 계획 대비 편차

- 원래 계획은 HTML 변환 instruction을 `.github/instructions/kos-html-cheatsheet.instructions.md`에 두는 것이었다.
- 실행에서는 프로젝트 전용 구분 전략을 반영해 `.github/instructions/project/ojinger-kos-html-cheatsheet.instructions.md`로 배치했다.
- 원래 계획은 skill 이름에 prefix를 붙이지 않았지만, 실행에서는 프로젝트 전용 식별성을 높이기 위해 `ojinger-` prefix를 사용했다.

이 편차는 추가 연구에서 정리한 프로젝트 전용/범용 구분 요구를 반영한 것이다.

## 검증

- 신규 customization 파일들에 대해 Problems 검사를 수행했고 오류는 없었다.
- 새 경로가 표준 `.github` customization 경로 안에 들어가는지 확인했다.
- skill 디렉터리명과 `name` frontmatter가 일치하는지 확인했다.

## 남은 이슈

- `.github/ref` 내부 파일은 모두 삭제했다.
- 다만 빈 디렉터리 `.github/ref/` 및 `.github/ref/instructions/` 자체를 제거하려는 shell 명령은 현재 실행 정책에 의해 차단됐다.
- 따라서 기능적으로는 더 이상 참조될 파일이 남아 있지 않지만, 빈 디렉터리 정리는 후속으로 한 번 더 수행해야 한다.

## 자기 검토

- 전역 규칙과 절차형 workflow를 분리해 always-on instruction 과적재를 줄였다.
- GitHub 웹 문서 기준 repository-wide / path-specific 경로와 정합되는 배치를 사용했다.
- 기존 범용 skill과 instruction은 건드리지 않아 영향 범위를 최소화했다.