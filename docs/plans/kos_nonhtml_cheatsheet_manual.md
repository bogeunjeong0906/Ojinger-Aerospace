# KOS_DOC 비HTML 파일 치트시트화 계획 (수동)

**작성일**: 2026-03-28  
**버전**: 1.0  
**상태**: 실행 대기  
**담당**: AI 에이전트 (autopilot, 수동 HTML 작성)  

---

## 1. 목적

`KOS_DOC` 내 HTML이 아닌 파일(`.md`, `.ks`)을 동일한 6섹션 치트시트 형식으로 수동 변환하여  
`KOS_cheatsheet` 디렉토리에 추가한다.  
자동화 스크립트를 사용하지 않고 에이전트가 각 파일을 직접 읽고 HTML을 작성한다.

---

## 1-1. Git 운영 규칙 (필수)

- 에이전트는 작업 중간중간 의미 단위로 commit 한다.
- 기본 commit checkpoint:
  1) P0+P1 완료 직후
  2) P2 완료 직후
  3) P3 및 전체 검증 완료 직후
- 작업 중 `git push`는 금지한다.
- 원격 반영은 사용자의 명시적 요청이 있을 때만 수행한다.

---

## 2. 변환 대상 및 우선순위

| 우선순위 | 소스 파일 | 출력 파일 | 예상 소요 |
|---------|-----------|-----------|----------|
| **P0** | `KOS_DOC/note/terminal_open.md` | `KOS_cheatsheet/note/terminal_open.html` | 15분 |
| **P1** | `KOS_DOC/mod/kerbal_engineer_redux.md` | `KOS_cheatsheet/mod/kerbal_engineer_redux.html` | 30분 |
| **P2** | `KOS_DOC/kOS-Ferram-master/README.md` + `kosferramtest.ks` | `KOS_cheatsheet/kOS-Ferram-master/README.html` | 45분 |
| **P3** | `KOS_DOC/kOS.MechJeb2.Addon-main/README.md` + 5개 `.ks` | `KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html` | 2~3시간 |

---

## 3. 출력 구조

```
docs/domain_knowledge/KOS_cheatsheet/
  note/
    terminal_open.html              ← P0
  mod/
    kerbal_engineer_redux.html      ← P1
  kOS-Ferram-master/
    README.html                     ← P2 (README + kosferramtest.ks 병합)
  kOS.MechJeb2.Addon-main/
    README.html                     ← P3 (README + 5개 .ks 핵심 패턴 병합)
```

---

## 4. 변환 규칙 (공통)

### 4.1 반드시 참조

- 기준 샘플: `docs/domain_knowledge/KOS_cheatsheet/cooked_sample.html`
- 변환 규칙: `.github/instructions/kos-nonhtml-cheatsheet.instructions.md`

### 4.2 6섹션 구성

| 섹션 | 내용 |
|------|------|
| META | source_file, source_title, category, mod_version |
| Core Intent | 모듈/애드온이 제공하는 기능 한두 문장 |
| Safety Critical Notes | WARNING/NOTE/버전 호환 경고 |
| Snippet Pack | 즉시 실행 가능한 kOS 코드 패턴 (테스트 하네스 제외, 실제 사용 패턴만) |
| Tuning / Parameters | 조정 가능한 파라미터, 기본값, 허용 범위 |
| Suffix and Key Inventory | `ADDONS:XXX:YYY` 형태 identifier 무손실 목록 |
| Agent Hints | 에이전트가 이 치트시트를 사용할 때 참고할 주의사항 |

### 4.3 .ks 파일 처리 원칙

- **포함**: API 호출 패턴, 구조체 접근 예시, 반환값 확인 코드
- **제외**: `PRINT "TEST PASS"` 계열 테스트 어서션, 루프 카운터, 메뉴 UI 코드
- 여러 `.ks` 파일에서 같은 패턴이 반복되면 한 번만 포함

---

## 5. 파일별 세부 지침

### P0: note/terminal_open.md

**소스**: `docs/domain_knowledge/KOS_DOC/note/terminal_open.md` (5줄)

- Core Intent: kOS 터미널을 스크립트에서 자동으로 여는 방법
- Snippet Pack: `CORE:PART:GETMODULE("kOSProcessor"):DOEVENT("Open Terminal").`
- Suffix: `CORE:PART`, `CORE:PART:GETMODULE`

### P1: mod/kerbal_engineer_redux.md

**소스**: `docs/domain_knowledge/KOS_DOC/mod/kerbal_engineer_redux.md` (60줄)

- Core Intent: KerbalEngineer 데이터를 kOS 스크립트에서 읽는 방법
- Snippet Pack: README 내 예제 코드 블록 전체
- Suffix: `SHIP:KERBALAUTOMATION`, `KE:*` 계열 identifier 모두
- Safety Notes: KerbalEngineer 모드 설치 필수 경고

### P2: kOS-Ferram-master/README.html

**소스**: 
- `docs/domain_knowledge/KOS_DOC/kOS-Ferram-master/README.md` (51줄)
- `docs/domain_knowledge/KOS_DOC/kOS-Ferram-master/kosferramtest.ks` (21줄)

- Core Intent: FAR(Ferram Aerospace Research) 공력 데이터를 kOS에서 읽는 방법
- Snippet Pack: `kosferramtest.ks` 내 `addons:far:ias`, `addons:far:mach` 등 접근 패턴
- Suffix: `ADDONS:FAR:IAS`, `ADDONS:FAR:MACH`, `ADDONS:FAR:CL`, `ADDONS:FAR:CD`, `ADDONS:FAR:DYNPRES` 등
- Safety Notes: FAR 미설치 시 `ADDONS:FAR:ISAVAILABLE` false 확인 필수

### P3: kOS.MechJeb2.Addon-main/README.html

**소스**:
- `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/README.md` (606줄)
- `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/AscentWrapperTest.ks` (799줄)
- `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/CoreWrapperTest.ks` (102줄)
- `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/InfoWrapperTest.ks` (168줄)
- `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/VesselWrapperTest.ks` (180줄)
- `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/TestRunner.ks` (115줄)

**주요 API 카테고리** (README에서 추출):
- Core: `ADDONS:MJ:AVAILABLE`, `ADDONS:MJ:GETCORE(vessel)`
- Ascent: `ADDONS:MJ:ASCENT:PITCHANGLE`, `ADDONS:MJ:ASCENT:TURNSHAPE` 등
- VesselState: `ADDONS:MJ:VESSELSTATE:SURFACESPEED`, `ADDONS:MJ:VESSELSTATE:ALTITUDE` 등
- InfoItems: `ADDONS:MJ:INFOITEMS:DELTAV` 등

**Snippet Pack 우선 포함 패턴** (.ks에서 추출):
```ks
// Ascent 자동조종 활성화
SET ADDONS:MJ:ASCENT:ENABLED TO TRUE.
SET ADDONS:MJ:ASCENT:PITCHANGLE TO 80.
// 선택적: 목표 고도 설정
SET ADDONS:MJ:ASCENT:DESIREDORBITALTITUDE TO 100000.
```

---

## 6. 완료 판정 기준

| 기준 | 내용 |
|------|------|
| 파일 생성 | 4개 HTML 파일 모두 지정 경로에 생성됨 |
| 6섹션 존재 | 각 파일에 6개 `<h2>` 섹션 모두 존재 |
| Snippet 비어있지 않음 | P0 제외 나머지 3개 파일에 코드블록 1개 이상 |
| META 정확성 | source_file, source_title 정확히 기재됨 |

---

## 7. 실행 순서

```
1. cooked_sample.html 참조하여 HTML 구조 파악
2. P0 terminal_open.html 생성 및 검증
3. P1 kerbal_engineer_redux.html 생성 및 검증
4. P0+P1 결과 1차 commit (push 금지)
5. P2 kOS-Ferram-master/README.html 생성 및 검증
6. P2 결과 2차 commit (push 금지)
7. P3 kOS.MechJeb2.Addon-main/README.html 생성 및 검증
8. 완료 판정 기준 체크 후 사용자에게 보고
9. 최종 결과 3차 commit (push 금지)
```
