# 🚀 프로젝트 개발 지침 (Project Guidelines)

## 1. 에이전트 제 1원칙
agent.md와 copilot-instructions.md의 내용은 모든 컨텍스트중 가장 우선적으로 참조한다. 
컨텍스트 용량이 부족하더라도 agent.md와 copilot-instructions.md의 내용은 요약없이 그대로 보존한다. 
모든 요청에는 agent.md와 copilot-instructions.md의 내용을 반드시 참조하여 답변한다.

## 2. 사용자 언어
답변에는 한국어를 사용한다. 단, 기술적 용어는 영어로 표기할 수 있다.

## 3. 지식 기반 개발 (Knowledge-Based Development)
다음 언어 및 패키지 사용 시, 반드시 `docs/domain_knowledge` 폴더 내의 문서를 참조하며 문서에 명시된 구문과 로직을 정확하게 인용하여 개발한다.
* **KOS (Kerbal Operating System):** `.ks` 스크립트 작성 시 참조
* **krpc:** KSP 원격 제어 인터페이스 활용 시 참조
* **dearpygui:** GUI 구성 및 이벤트 처리 루틴 참조

---

## 4. 표준 기술 스택 (Standard Tech Stack)
본 프로젝트는 아래의 표준 패키지 및 언어 사용을 원칙으로 한다.
* **KSP 실시간 제어:** `kOS` (ks 스크립트)
* **KSP 원격 제어/텔레메트리:** `krpc` 패키지
* **사용자 인터페이스(UI):** `dearpygui` 패키지
* **데이터 처리 및 수학 연산:** `numpy` 패키지
* **수치 해석 및 최적화:** `casadi` 패키지 (Numerical Analysis & Optimization)

---

## 5. 아키텍처 및 설계 (Architecture & Design)
프로젝트의 구조적 설계 및 로직 흐름은 시각화하여 관리하며, 다음 원칙을 준수한다.
* **UML 작성 표준:** 모든 다이어그램(Class, Sequence, State 등)은 **UML 형식**을 따른다.
* **작성 도구:** 코드 기반 다이어그램 도구인 **Mermaid (mmd)** 문법을 사용하여 작성한다.

## 6. 가상환경
파이썬 스크립트 실행시 가상환경을 반드시 활성화한다. 
**활성화 커맨드**: conda activate ./.venv

## 6-1. Git 작업 규칙 (Autopilot)
Autopilot 모드로 다단계 작업을 수행할 때는 아래 규칙을 반드시 지킨다.

* 작업 중간중간 의미 있는 단위로 commit 한다. (최소 2회 이상)
* commit 메시지는 작업 단위를 명확히 구분한다. (예: plan, instructions, execution)
* 작업 중에는 절대 push 하지 않는다.
* 사용자의 명시적 승인 없이 `git push`, `git push --force`를 실행하지 않는다.

## 7. KOS_DOC 치트시트 관련 지침

### 7-1. HTML 변환 규칙
KOS_DOC HTML 파일을 치트시트로 변환하는 작업 시 참조한다.

* 규칙 파일: `.github/instructions/copilot-instructions.md`
* 샘플 파일: `docs/domain_knowledge/KOS_cheatsheet/cooked_sample.html`
* 변환 스크립트: `scripts/kos_cheatsheet_converter.py`

### 7-2. 품질 검수
생성된 치트시트 품질 검수 작업 시 참조한다.

* 계획서: `docs/plans/kos_cheatsheet_quality_inspection.md`
* 실행 지침: `.github/instructions/kos-quality-inspection.instructions.md`
* 결과 출력: `docs/plans/results/quality_report.json`

### 7-3. 비HTML 파일 치트시트화
KOS_DOC 내 `.md`, `.ks` 파일을 수동으로 치트시트화하는 작업 시 참조한다.

* 계획서: `docs/plans/kos_nonhtml_cheatsheet_manual.md`
* 실행 지침: `.github/instructions/kos-nonhtml-cheatsheet.instructions.md`


