# 🚀 프로젝트 개발 지침 (Project Guidelines)

## 0. 사용자 언어
답변에는 한국어를 사용한다. 단, 기술적 용어는 영어로 표기할 수 있다.

## 1. 지식 기반 개발 (Knowledge-Based Development)
다음 언어 및 패키지 사용 시, 반드시 `domain_knowledge/` 폴더 내의 문서를 참조하며 문서에 명시된 구문과 로직을 정확하게 인용하여 개발한다.
* **KOS (Kerbal Operating System):** `.ks` 스크립트 작성 시 참조
* **krpc:** KSP 원격 제어 인터페이스 활용 시 참조
* **dearpygui:** GUI 구성 및 이벤트 처리 루틴 참조

---

## 2. 표준 기술 스택 (Standard Tech Stack)
본 프로젝트는 아래의 표준 패키지 및 언어 사용을 원칙으로 한다.
* **KSP 실시간 제어:** `kOS` (ks 스크립트)
* **KSP 원격 제어/텔레메트리:** `krpc` 패키지
* **사용자 인터페이스(UI):** `dearpygui` 패키지
* **데이터 처리 및 수학 연산:** `numpy` 패키지
* **수치 해석 및 최적화:** `casadi` 패키지 (Numerical Analysis & Optimization)

---

## 3. 아키텍처 및 설계 (Architecture & Design)
프로젝트의 구조적 설계 및 로직 흐름은 시각화하여 관리하며, 다음 원칙을 준수한다.
* **문서화 위치:** 아키텍처 설계 내용은 루트의 `architecture_map.md`에 기록한다.
* **UML 작성 표준:** 모든 다이어그램(Class, Sequence, State 등)은 **UML 형식**을 따른다.
* **작성 도구:** 코드 기반 다이어그램 도구인 **Mermaid (mmd)** 문법을 사용하여 작성한다.

## 4. 가상환경
파이썬 스크립트 실행시 가상환경을 반드시 활성화한다. 
**활성화 커맨드**: conda activate ./.venv
