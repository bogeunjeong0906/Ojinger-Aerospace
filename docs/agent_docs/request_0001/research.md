# request_0001 분석

## 요청 요약

`ref` 폴더에 임시 보관된 지침 내용을 현재 프로젝트의 정식 Copilot customization 구조인 `.github/` 아래의 프로젝트 전용 instruction 및 skill로 내재화하기 위한 분석과 실행 계획을 수립한다.

## 작업 범위

- 대상 입력
  - `.github/ref/copilot-instructions.md`
  - `.github/ref/instructions/copilot-instructions.md`
  - `.github/ref/instructions/kos-nonhtml-cheatsheet.instructions.md`
  - `.github/ref/instructions/kos-quality-inspection.instructions.md`
- 대상 출력 후보
  - `.github/copilot-instructions.md`
  - `.github/instructions/**/*.instructions.md`
  - `.github/skills/*/SKILL.md`

## 컨텍스트 프리플라이트

- 예상 작업 세트
  - ref 지침 4개 파일
  - 기존 `.github/instructions` 2개 파일
  - 기존 `.github/skills` 5개 스킬
  - 향후 생성될 `.github/copilot-instructions.md` 및 신규 skill 디렉터리
- 복잡도 판단: 중간
- 근거
  - 코드 수정이 아닌 customization 재구성 작업이다.
  - 파일 수는 많지 않지만, 항상 적용되는 instruction과 온디맨드 skill의 경계를 잘못 잡으면 이후 모든 대화 품질에 영향이 간다.
  - 현재 `docs/agent_docs`가 비어 있어 요청 아티팩트만 추가하면 안정적으로 진행 가능하다.

## 현재 상태 요약

- `.github`에는 다음만 존재한다.
  - 항상 적용 instruction: 없음 (`.github/copilot-instructions.md` 부재)
  - 파일 기반 instruction: `markdown-docs.instructions.md`, `tas-artifact-policy.instructions.md`
  - skill: `clarification-fallback`, `context-preflight`, `git-commit-workflow`, `problems-lint-gate`, `python-execution-environment`
- `ref`에는 프로젝트 문맥이 강하게 반영된 instruction 초안이 별도로 존재한다.
- 현재 구조는 "프로젝트 공통 규칙"과 "KOS 특정 워크플로"가 정식 customization tree에 흡수되지 않은 상태다.

## ref 내용 분석

### 1. `.github/ref/copilot-instructions.md`

성격상 프로젝트 전역에 항상 적용되어야 하는 규칙이 다수 포함되어 있다.

- 사용자 언어: 한국어 우선
- 지식 기반 개발: `docs/domain_knowledge` 참조 의무
- 표준 기술 스택 선언: `kOS`, `krpc`, `dearpygui`, `numpy`, `casadi`
- 아키텍처 문서화 원칙: UML, Mermaid
- Python 실행 환경: `conda activate ./.venv`
- Git 운영 원칙: Autopilot 모드에서 의미 단위 commit, push 금지
- KOS_DOC 관련 서브작업 안내: 변환, 검수, 비HTML 치트시트화 지침 연결

판단:

- 이 파일의 본체는 `.github/copilot-instructions.md`로 승격하는 것이 자연스럽다.
- 단, 세부 워크플로 절차까지 항상 적용 instruction에 과도하게 싣는 것은 컨텍스트 낭비가 될 수 있다.

### 2. `.github/ref/instructions/copilot-instructions.md`

실제 내용은 `docs/domain_knowledge/KOS_DOC/**/*.html`에 적용되는 파일 기반 instruction이다.

- KOS_DOC HTML -> KOS_cheatsheet 변환 규칙
- 변환 구조, 메타, 섹션 순서, 무손실 정책, 샘플 참조

판단:

- 파일명은 다소 혼동을 준다.
- 역할상 `.github/instructions/kos-html-cheatsheet.instructions.md` 같은 명시적 이름으로 옮기는 것이 적절하다.
- `applyTo`는 현재 패턴이 적절하다.

### 3. `.github/ref/instructions/kos-nonhtml-cheatsheet.instructions.md`

특정 4개 비HTML 문서를 치트시트로 수동 변환하는 절차형 워크플로다.

- 입력 파일과 출력 파일이 고정돼 있다.
- 단계별 검증 명령과 commit 단위까지 정의돼 있다.

판단:

- 이 문서는 "파일 편집 규칙"이라기보다 "작업 절차"에 가깝다.
- 자동 적용 instruction으로 둘 수는 있지만, 더 적합한 형태는 skill이다.
- 이유는 이 워크플로가 특정 작업 요청에서만 필요하고, 검증 명령과 단계적 수행법을 함께 묶어야 하기 때문이다.

### 4. `.github/ref/instructions/kos-quality-inspection.instructions.md`

KOS cheatsheet 품질 검수용 3-tier 절차형 워크플로다.

- 선행 조건 확인
- Tier 1/2/3 검증
- 결과 파일 갱신과 판정 기준

판단:

- 이것 역시 특정 워크플로이며 skill로 승격하는 편이 적합하다.
- 현재처럼 `applyTo: docs/domain_knowledge/KOS_cheatsheet/**`만으로 자동 로딩시키면, 단순 HTML 수정 작업에도 불필요하게 무거운 검수 절차가 붙을 수 있다.

## 공식 문서 기반 구조 판단

VS Code 최신 문서 기준 핵심 원칙:

- `.github/copilot-instructions.md`
  - 프로젝트 전역 always-on 규칙에 사용
- `.github/instructions/*.instructions.md`
  - `applyTo` 기반 파일/폴더별 규칙에 사용
  - 또는 `description` 매칭으로 온디맨드 참조 가능
- `.github/skills/<name>/SKILL.md`
  - 특정 작업에만 필요한 절차형 capability에 사용
  - 스크립트, 예시, 검증 절차를 함께 보관 가능
- skill frontmatter는 `name`과 디렉터리명이 반드시 일치해야 한다.
- instruction은 여러 파일이 함께 적용될 수 있고 우선순위가 보장되지 않으므로, 중복/충돌 규칙은 최소화해야 한다.

## 구조적 문제점

1. ref가 정식 탐색 경로 밖에 있다.

- `.github/ref`는 VS Code customization 표준 위치가 아니다.
- 현재 파일들은 사람이 참조하지 않으면 자동 발견되지 않을 가능성이 높다.

2. 절차형 문서가 instruction으로 과적재돼 있다.

- `kos-nonhtml-cheatsheet`와 `kos-quality-inspection`은 skill이 더 적합하다.
- instruction으로 두면 관련 파일을 건드리는 넓은 범위의 작업에 계속 주입될 수 있다.

3. 파일명 의미가 모호하다.

- `ref/instructions/copilot-instructions.md`는 실제로는 copilot 전역 instruction이 아니라 KOS HTML 변환 규칙이다.
- 정식 위치로 옮길 때 의미 기반 이름으로 재배치해야 한다.

4. Python 환경 지침이 프로젝트 규칙과 현재 세션 상태 사이에 차이가 있다.

- ref는 `conda activate ./.venv`를 요구한다.
- 현재 터미널은 `conda activate base` 상태다.
- 실행 단계에서 Python 관련 skill과 전역 instruction 사이의 일관성을 다시 맞출 필요가 있다.

## 내재화 권장안

### A. 항상 적용 instruction으로 승격

대상: `.github/ref/copilot-instructions.md`

목표 파일:

- `.github/copilot-instructions.md`

권장 정리 방식:

- 남길 것
  - 한국어 응답 원칙
  - `docs/domain_knowledge` 참조 의무
  - 표준 기술 스택
  - UML/Mermaid 문서화 원칙
  - Python 실행 환경 원칙
  - Git push 금지, 명시 승인 없는 push 금지
- 축약 또는 링크화할 것
  - KOS 치트시트 세부 작업 절차 자체
  - commit 횟수 같은 특정 워크플로 세칙

이유:

- 전역 instruction은 짧고 안정적일수록 좋다.
- 세부 절차는 skill 또는 파일 기반 instruction으로 분리해야 불필요한 컨텍스트 점유를 줄일 수 있다.

### B. 파일 기반 instruction으로 유지 또는 개명

대상: `.github/ref/instructions/copilot-instructions.md`

권장 목표 파일:

- `.github/instructions/kos-html-cheatsheet.instructions.md`

판단 근거:

- `applyTo: docs/domain_knowledge/KOS_DOC/**/*.html`가 명확하다.
- 문서 구조/변환 산출물 형식을 규정하는 규칙이므로 instruction이 맞다.

### C. skill로 전환

대상 1: `.github/ref/instructions/kos-nonhtml-cheatsheet.instructions.md`

권장 목표 디렉터리:

- `.github/skills/kos-nonhtml-cheatsheet/SKILL.md`

대상 2: `.github/ref/instructions/kos-quality-inspection.instructions.md`

권장 목표 디렉터리:

- `.github/skills/kos-quality-inspection/SKILL.md`

권장 frontmatter:

- `name`: 디렉터리명과 동일
- `description`: 언제 이 skill을 써야 하는지 명확히 서술
- `user-invocable: true` 유지 가능

판단 근거:

- 둘 다 다단계 실행 절차다.
- 결과물, 검증, commit cadence, 예외 처리까지 포함한다.
- 필요할 때만 로딩하는 것이 합리적이다.

## 실행 시 고려사항

- 기존 `ref`를 바로 삭제하지 말고, 1차 내재화 후 동등성 검토를 거친 뒤 제거 여부를 결정하는 것이 안전하다.
- instruction/skill의 중복 문구가 생기면 이후 agent가 상충된 규칙을 동시에 읽을 수 있다.
- `.github/copilot-instructions.md`에는 특정 파일 경로에 한정된 세부 절차를 넣지 않는 편이 낫다.
- skill 설명에는 검색 키워드를 충분히 넣어야 자동 로딩 가능성이 올라간다.

## 현재 기준 결론

가장 안정적인 내재화 방향은 다음 3층 구조다.

1. 전역 규칙은 `.github/copilot-instructions.md`
2. HTML 변환 규칙은 `.github/instructions/kos-html-cheatsheet.instructions.md`
3. 절차형 KOS 워크플로는 각각 별도 skill

## 오픈 이슈 및 기본 가정

- 오픈 이슈
  - Python 실행 환경 문구를 `.venv` 기준으로 통일할지, 현재 conda `base`와 병행 허용할지는 실행 단계에서 정리 필요
- 기본 가정
  - 사용자는 `ref`를 의도적으로 자동 참조되지 않게 둔 상태였고, 내재화 완료 후 `ref`를 삭제할 계획이다.
  - 이번 단계에서는 구현이 아니라 분석과 계획 수립만 수행한다.

## 추가 연구 2026-03-31

### 사용자 의도 보정

- `.github/ref`는 단순 임시 저장소가 아니라, 의도적으로 자동 참조를 막기 위한 격리 구역이었다.
- 따라서 내재화 완료 조건에는 다음이 포함된다.
  - 프로젝트 전용 customization이 표준 탐색 경로에서 발견 가능해야 한다.
  - 기존 `ref`는 최종적으로 제거되어야 한다.

### GitHub 웹 최신 문서 기준 전역 instruction 참조 경로

GitHub Docs의 2026-03-31 기준 웹 문서에서 확인한 사항:

- GitHub.com의 repository-wide custom instructions 경로는 `.github/copilot-instructions.md`다.
- GitHub.com의 path-specific custom instructions 경로는 `.github/instructions/**/*.instructions.md`다.
- GitHub.com의 agent instructions는 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` 파일을 사용한다.
- GitHub.com에서 Copilot Chat은 repository-wide instruction만 안정적으로 사용한다.
- GitHub.com에서 Copilot coding agent는 repository-wide, path-specific, agent instructions를 모두 지원한다.
- GitHub.com에서 Copilot code review는 repository-wide와 path-specific instructions를 지원한다.

추가로 확인된 세부 사항:

- GitHub 웹 문서상 path-specific instructions는 `.github/instructions` 하위에서 재귀적으로 구성할 수 있다.
- precedence는 다음 순서다.
  - Personal instructions
  - Repository path-specific instructions
  - Repository-wide `.github/copilot-instructions.md`
  - Agent instructions
  - Organization instructions
- GitHub.com의 code review는 custom instruction 파일의 처음 4,000자만 읽는다.

의미:

- GitHub 웹까지 고려하면 프로젝트 전역 규칙의 정식 경로는 확정적으로 `.github/copilot-instructions.md`다.
- 프로젝트 전용 세부 규칙을 `.github/instructions` 아래로 분리하는 방식은 VS Code뿐 아니라 GitHub.com coding agent/code review와도 정합성이 있다.
- 반면 skill은 VS Code 계열 customization에는 적합하지만, GitHub 웹의 repository custom instructions 체계와는 별개다.

### 현재 `.github`에서 프로젝트 전용 문서를 구분하는 방법 아이디어

현재 `ref`를 제외한 `.github` 파일들은 대부분 범용 에이전트 운영 규칙이다. 이 위에 프로젝트 전용 문서를 얹을 때는 "자동 적용 범위"와 "사람이 봤을 때의 식별성"을 같이 설계하는 편이 좋다.

#### 아이디어 A: 전역은 단일 파일, 프로젝트 전용은 명시적 prefix 사용

- `.github/copilot-instructions.md`에는 오직 이 프로젝트의 핵심 전역 규칙만 둔다.
- 프로젝트 전용 파일 기반 instruction은 파일명에 `ojinger-` 또는 `project-` prefix를 붙인다.
  - 예: `ojinger-kos-html-cheatsheet.instructions.md`
- 프로젝트 전용 skill도 디렉터리명에 같은 prefix를 붙인다.
  - 예: `ojinger-kos-quality-inspection`

장점:

- GitHub 웹, VS Code, CLI 어느 표면에서도 추가 설정 없이 바로 구분된다.
- skill은 상위 폴더를 더 중첩하지 않아도 되어 안전하다.

단점:

- 파일명이 길어진다.

#### 아이디어 B: instruction은 하위 디렉터리, skill은 prefix

- instruction은 공식 문서상 `.github/instructions` 하위 재귀 탐색이 가능하므로 다음처럼 분리한다.
  - `.github/instructions/core/...`
  - `.github/instructions/project/...`
- skill은 탐색 안정성을 위해 `.github/skills` 바로 아래 디렉터리명을 prefix 방식으로 유지한다.
  - 예: `core-context-preflight`, `project-kos-quality-inspection`

장점:

- instruction은 폴더 구조만 봐도 범용/프로젝트 전용이 분리된다.
- skill은 보수적으로 표준 위치를 유지한다.

단점:

- 기존 범용 skill 이름까지 손대려면 범위가 커질 수 있다.

#### 아이디어 C: 사람용 분류 문서를 추가하고 실제 탐색 경로는 표준 유지

- customization 파일은 표준 위치에 두되, `.github/CUSTOMIZATIONS.md` 같은 사람용 인덱스를 둔다.
- 인덱스에서 다음을 표로 관리한다.
  - 범용 운영 규칙
  - 프로젝트 전용 규칙
  - GitHub 웹에서 적용되는 파일
  - VS Code 전용 skill

장점:

- 에이전트 탐색 경로를 건드리지 않으면서 팀원이 구조를 이해하기 쉽다.

단점:

- 사람용 문서라 자동 구분 신호는 아니다.

### 현재 요청에 가장 적합한 구분 전략

현재 저장소 상황에서는 다음 조합이 가장 현실적이다.

1. `.github/copilot-instructions.md`는 프로젝트 전용 always-on 규칙으로 사용
2. `.github/instructions/project/` 하위에 프로젝트 전용 `.instructions.md`를 배치
3. `.github/instructions` 루트 또는 `core/`에는 범용 instruction만 유지
4. `.github/skills` 아래 프로젝트 전용 skill은 `ojinger-` 같은 prefix로 명확히 식별
5. 필요하면 사람용 인덱스 문서 1개를 추가

이 조합을 권장하는 이유:

- instruction 쪽은 GitHub 웹 문서가 재귀 하위 디렉터리를 공식적으로 허용한다.
- skill 쪽은 추가 설정 없이도 안전하게 운영하려면 하위 디렉터리 중첩보다 명시적 디렉터리명 prefix가 낫다.
- 범용 규칙과 프로젝트 규칙이 같은 `.github` 아래 공존하더라도, 이름과 폴더만으로 운영 의도가 분리된다.

### 연구 결과가 기존 계획에 미치는 영향

- 기존의 "ref를 한동안 보류" 전략은 사용자의 최신 요구와 맞지 않는다.
- execution 계획은 다음 방향으로 수정되어야 한다.
  - 신규 customization 생성
  - 동등성 점검
  - `ref` 삭제
  - 삭제 후 Problems 및 구조 재검증