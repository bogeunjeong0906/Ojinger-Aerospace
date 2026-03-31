# request_0001 계획

## 계획 목적

`.github/ref`에 분리되어 있는 프로젝트 맞춤 지침을 VS Code 표준 customization 구조로 이전하면서, 항상 적용되어야 할 규칙과 특정 워크플로에만 필요한 절차를 분리한다.

## 실행 원칙

- 전역 규칙은 짧고 안정적으로 유지한다.
- 파일 대상이 명확한 규칙만 `.instructions.md`로 자동 적용한다.
- 다단계 절차와 검증 흐름은 skill로 이동한다.
- 이관과 동등성 검토가 끝나면 `ref`를 삭제한다.
- touched file 기준 Problems 게이트를 전후로 확인한다.

## 대상 구조

### 생성 또는 갱신 예정 파일

- `.github/copilot-instructions.md`
- `.github/instructions/kos-html-cheatsheet.instructions.md`
- `.github/skills/kos-nonhtml-cheatsheet/SKILL.md`
- `.github/skills/kos-quality-inspection/SKILL.md`

### 유지 예정 파일

- `.github/instructions/markdown-docs.instructions.md`
- `.github/instructions/tas-artifact-policy.instructions.md`
- 기존 5개 공용 skill 디렉터리

### 보류 대상

- `.github/ref/**`

보류 이유:

- execution 중 동등성 검토를 마치기 전까지는 임시로 유지하되, 최종 단계에서 삭제한다.

## 세부 실행 단계

```markdown
- [ ] 1. `.github/ref/copilot-instructions.md`를 바탕으로 `.github/copilot-instructions.md`를 신설한다.
- [ ] 2. 전역 instruction에서 세부 KOS 작업 절차를 제거하고, 프로젝트 공통 규칙만 남긴다.
- [ ] 3. `.github/ref/instructions/copilot-instructions.md`를 의미가 드러나는 이름의 파일 기반 instruction으로 이관한다.
- [ ] 4. `kos-nonhtml-cheatsheet` 절차를 `.github/skills/kos-nonhtml-cheatsheet/SKILL.md`로 재구성한다.
- [ ] 5. `kos-quality-inspection` 절차를 `.github/skills/kos-quality-inspection/SKILL.md`로 재구성한다.
- [ ] 6. 신규 skill의 `name`, 디렉터리명, `description`을 정렬해 자동 발견 가능성을 높인다.
- [ ] 7. `.github/ref`와 신규 customization 간 내용 대응표를 검토해 누락 여부를 확인한다.
- [ ] 8. 동등성 확인 후 `.github/ref`를 삭제한다.
- [ ] 9. touched files 기준 Problems 재검사로 frontmatter/Markdown 오류가 없는지 확인한다.
```

## 파일별 편집 방침

### 1. `.github/copilot-instructions.md`

포함 예정:

- 한국어 응답 기본 원칙
- `docs/domain_knowledge` 우선 참조 규칙
- 표준 기술 스택 선언
- 아키텍처 문서화 방식
- Python 환경 실행 원칙
- Git push 제한

제외 예정:

- KOS HTML 변환의 상세 섹션 구조
- 비HTML 치트시트 수동 생성의 단계별 명령
- 품질 검수 tier별 실행 절차

### 2. `.github/instructions/kos-html-cheatsheet.instructions.md`

포함 예정:

- 기존 HTML 변환 규칙 원문 구조 대부분 유지
- `applyTo: "docs/domain_knowledge/KOS_DOC/**/*.html"`
- 샘플 참조와 무손실 정책 유지

조정 예정:

- 파일명과 제목을 역할 중심으로 명확화
- 전역 규칙과 겹치는 Git 문구는 필요 최소화

### 3. `.github/skills/kos-nonhtml-cheatsheet/SKILL.md`

포함 예정:

- 언제 이 skill을 사용해야 하는지 설명
- 입력 4개 파일과 출력 4개 파일 범위
- 단계별 절차와 검증 명령
- commit cadence는 "사용자 요청 시에만 수행" 원칙과 충돌하지 않도록 서술 조정

주의점:

- 현재 상위 에이전트 정책은 명시 요청 없는 commit 금지이므로, 기존 지침의 commit 명령은 직접 실행 지시가 아니라 권장 운영 절차로 서술을 낮춰야 한다.

### 4. `.github/skills/kos-quality-inspection/SKILL.md`

포함 예정:

- 검수 대상 범위
- Tier 1/2/3 절차
- `quality_report.json` 산출 규칙
- 판정 기준과 후속 조치 흐름

주의점:

- 이 skill은 광범위한 HTML 수정에 자동 적용되면 과도하므로 description을 "품질 검수", "inspection", "verdict", "quality_report.json" 같은 검색어 중심으로 작성한다.

## 검증 계획

### Problems 게이트

- 편집 전
  - 관련 `.github` 및 `docs/agent_docs/request_0001` 파일 기준 Problems 확인
- 편집 후
  - 신규/수정 파일 기준 Problems 재확인

### 구조 검증

- `.github/copilot-instructions.md`가 루트 `.github`에 존재하는지 확인
- 신규 skill 디렉터리명과 `name`이 일치하는지 확인
- instruction 파일의 frontmatter가 유효한지 확인
- Markdown heading, list, trailing newline 규칙 확인

### 의미 검증

- ref 4개 파일 각각이 새 구조에서 어느 파일로 흡수됐는지 대응표 확인
- 항상 적용 규칙과 온디맨드 절차가 분리됐는지 검토
- 기존 `.github/instructions` 및 `.github/skills`와 충돌하는 중복 문구가 없는지 점검

## 완료 기준

- `.github/copilot-instructions.md`가 생성되어 프로젝트 전역 규칙을 담고 있다.
- HTML 변환 규칙이 명시적 이름의 `.instructions.md`로 존재한다.
- 비HTML 치트시트화와 품질 검수가 각각 독립된 skill로 존재한다.
- 신규 customization 파일들에 frontmatter 오류가 없다.
- `ref` 원본과 신규 구조 간 의미상 누락이 없다.
- `.github/ref`가 삭제되어 더 이상 격리 경로가 남아 있지 않다.

## 롤백 트리거

- execution 중 전역 instruction이 과도하게 비대해져 기존 agent 품질을 떨어뜨릴 우려가 크다고 판단되면, 전역 규칙을 더 축약하는 방향으로 plan 수정
- skill보다 instruction이 더 적합한 반례가 발견되면, 해당 항목만 plan 단계로 되돌려 재분류
- Python 환경 규칙 충돌이 실제 실행 검증을 막으면, 환경 지침 분리를 먼저 수행하도록 순서 재조정

## 실행 전 결정 사항

현재 계획은 다음 결정을 기본값으로 사용한다.

- `ref/copilot-instructions.md` -> `.github/copilot-instructions.md`
- `ref/instructions/copilot-instructions.md` -> `.github/instructions/kos-html-cheatsheet.instructions.md`
- `ref/instructions/kos-nonhtml-cheatsheet.instructions.md` -> `.github/skills/kos-nonhtml-cheatsheet/SKILL.md`
- `ref/instructions/kos-quality-inspection.instructions.md` -> `.github/skills/kos-quality-inspection/SKILL.md`
- `.github/ref/**`는 execution 말미에 삭제