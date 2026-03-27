---
applyTo: "docs/domain_knowledge/KOS_DOC/**/*.{md,ks}"
---

# KOS_DOC 비HTML 파일 치트시트 변환 지침

## 이 지침의 목적
AI 에이전트가 `docs/plans/kos_nonhtml_cheatsheet_manual.md`에 정의된 4개 비HTML 파일을  
자율적으로 읽고 수동으로 HTML 치트시트를 작성한다.  
사용자의 추가 입력 없이 처음부터 끝까지 완료하고 결과를 보고한다.

## Git 운영 규칙 (필수)

- 작업 중간중간 의미 단위로 commit 한다 (최소 3회).
- 권장 commit 단위: `p0-p1`, `p2`, `p3-final`.
- 작업 중 `git push`는 절대 금지한다.
- 사용자의 명시적 승인 없이는 어떤 원격 push도 수행하지 않는다.

---

## STEP 0: 선행 조건 확인

```bash
# 기준 샘플 파일 존재 확인 (HTML 구조 참조용)
ls docs/domain_knowledge/KOS_cheatsheet/cooked_sample.html

# 출력 디렉토리 생성 (없으면)
mkdir -p docs/domain_knowledge/KOS_cheatsheet/note
mkdir -p docs/domain_knowledge/KOS_cheatsheet/mod
mkdir -p docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master
mkdir -p docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main
```

---

## HTML 템플릿 구조

모든 치트시트 파일은 아래 구조를 따른다. `cooked_sample.html` 참조.

```html
<!--
CHEATSHEET_META
source_file: {소스 파일 상대 경로}
source_doc_title: {문서 제목}
source_doc_version: {버전 또는 N/A}
cheatsheet_type: snippet-first, agent-oriented
-->

<h1>{문서 제목} - Cheat Sheet</h1>

<h2>1) Core Intent</h2>
<p>
{이 모듈/파일이 무엇을 제공하는가. 1~3문장.}
</p>

<h2>2) Safety Critical Notes</h2>
<ul>
  <li>{경고 항목 1}</li>
  <li>{경고 항목 2}</li>
</ul>

<h2>3) Snippet Pack (Directly Usable)</h2>
<pre><code>// 즉시 실행 가능한 kOS 코드 패턴
{코드}</code></pre>

<h2>4) Tuning / Parameters</h2>
<pre><code>// 조정 가능한 파라미터 (있는 경우)
{코드 또는 테이블}</code></pre>

<h2>5) Suffix and Key Inventory (No-loss policy)</h2>
<ul>
  <li>{IDENTIFIER:SUFFIX}</li>
</ul>

<h2>6) Agent Usage Hints</h2>
<ul>
  <li>{에이전트 사용 시 참고 사항}</li>
</ul>
```

---

## STEP 1: P0 — note/terminal_open.html

**소스 읽기**: `docs/domain_knowledge/KOS_DOC/note/terminal_open.md`

**작성 지침:**
- Core Intent: kOS 프로세서 터미널을 스크립트에서 자동으로 여는 방법
- Safety Notes: 파트 모듈명이 kOSProcessor인지 확인 필요 (커스텀 프로세서 파트는 다를 수 있음)
- Snippet: README의 코드 블록 그대로 사용
- Suffix: `CORE:PART`, `CORE:PART:GETMODULE`
- Agent Hints: 터미널 UI가 필요한 `TERMINAL:*` 명령과 함께 사용

**출력 경로**: `docs/domain_knowledge/KOS_cheatsheet/note/terminal_open.html`

**완료 검증**:
```bash
grep -c "GETMODULE" docs/domain_knowledge/KOS_cheatsheet/note/terminal_open.html
# 결과: 1 이상
```

---

## STEP 2: P1 — mod/kerbal_engineer_redux.html

**소스 읽기**: `docs/domain_knowledge/KOS_DOC/mod/kerbal_engineer_redux.md`

**작성 지침:**
- Core Intent: KerbalEngineer mod의 계산 데이터(델타V, TWR 등)를 kOS 스크립트에서 읽는 인터페이스
- Safety Notes:
  - KerbalEngineer mod 설치 필수
  - `ADDONS:KE:AVAILABLE` 또는 유사 가용성 체크 먼저 수행
- Snippet: README.md의 코드 예시를 `<pre><code>` 블록으로 변환
- Suffix: README에 등장하는 `ADDONS:KE:*` 또는 `SHIP:*` 계열 kOS identifier 전부 수집
- Agent Hints: KerbalEngineer 없이는 런타임 오류 발생, 가용성 체크 코드 항상 포함 권장

**출력 경로**: `docs/domain_knowledge/KOS_cheatsheet/mod/kerbal_engineer_redux.html`

**완료 검증**:
```bash
grep -c "<li>" docs/domain_knowledge/KOS_cheatsheet/mod/kerbal_engineer_redux.html
# 결과: 3 이상 (suffix + safety notes)
```

P0/P1 완료 후 즉시 중간 commit 수행:

```bash
git add docs/domain_knowledge/KOS_cheatsheet/note/terminal_open.html docs/domain_knowledge/KOS_cheatsheet/mod/kerbal_engineer_redux.html
git commit -m "nonhtml: add P0-P1 cheatsheets"
```

---

## STEP 3: P2 — kOS-Ferram-master/README.html

**소스 읽기 (두 파일 모두 읽기)**:
1. `docs/domain_knowledge/KOS_DOC/kOS-Ferram-master/README.md`
2. `docs/domain_knowledge/KOS_DOC/kOS-Ferram-master/kosferramtest.ks`

**작성 지침:**
- Core Intent: FAR(Ferram Aerospace Research) 공력 데이터를 kOS 스크립트에서 실시간으로 읽고 조작하는 인터페이스
- Safety Notes:
  - FAR mod 미설치 시 `ADDONS:FAR` 접근 불가 → `ADDONS:FAR:ISAVAILABLE` 체크 필수
  - 비행 중 flap/spoiler 상태 변경은 즉각 공력에 영향
- Snippet: `kosferramtest.ks` 전체를 핵심 패턴으로 추출 (until 루프 구조는 유지, PRINT 라인은 주석으로 변환)
- Suffix 목록 (반드시 전부 포함):
  - `ADDONS:FAR:ISAVAILABLE`
  - `ADDONS:FAR:IAS`
  - `ADDONS:FAR:TAS`
  - `ADDONS:FAR:MACH`
  - `ADDONS:FAR:CL`
  - `ADDONS:FAR:CD`
  - `ADDONS:FAR:CM`
  - `ADDONS:FAR:REFAREA`
  - `ADDONS:FAR:DYNPRES`
  - `ADDONS:FAR:STALLFRACTION`
  (README에 추가 항목 있으면 전부 포함)
- Agent Hints: FAR 없는 환경에서는 이 치트시트의 모든 ADDONS:FAR:* 항목 사용 불가

**출력 경로**: `docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master/README.html`

**완료 검증**:
```bash
grep -c "ADDONS:FAR" docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master/README.html
# 결과: 5 이상
```

P2 완료 후 중간 commit 수행:

```bash
git add docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master/README.html
git commit -m "nonhtml: add P2 ferram cheatsheet"
```

---

## STEP 4: P3 — kOS.MechJeb2.Addon-main/README.html

**소스 읽기 (순서대로 읽기)**:
1. `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/README.md` (전체 읽기)
2. `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/CoreWrapperTest.ks`
3. `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/AscentWrapperTest.ks` (핵심 패턴만)
4. `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/VesselWrapperTest.ks` (핵심 패턴만)
5. `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/InfoWrapperTest.ks` (핵심 패턴만)
6. `docs/domain_knowledge/KOS_DOC/kOS.MechJeb2.Addon-main/TestRunner.ks` (참조만, snippet 불필요)

**작성 지침:**
- Core Intent: MechJeb2 자동조종 기능(Ascent, Landing, Maneuver 등)을 kOS 스크립트에서 제어하는 통합 인터페이스
- Safety Notes:
  - MechJeb2 mod 설치 필수
  - `ADDONS:MJ:AVAILABLE` 체크 필수
  - Ascent 자동조종 활성화 전 목표 궤도 파라미터 설정 완료 필요
  - MechJeb와 kOS 동시 조종 시 충돌 주의
- Snippet Pack: 아래 카테고리별로 구분하여 작성
  ```
  // --- 가용성 확인 ---
  // --- Core 접근 ---
  // --- Ascent 자동조종 ---
  // --- VesselState 읽기 ---
  // --- InfoItems 읽기 ---
  ```
  각 `.ks` 파일에서 테스트 어서션(`PRINT "PASS"`, `SET testsPassed TO`)과 메뉴 UI 코드를 제외한 실제 API 호출 패턴만 추출
- Suffix: README.md에서 `ADDONS:MJ:*` 계열 identifier 전부 수집 (누락 없이)
- Tuning 섹션: Ascent 파라미터 (`PITCHANGLE`, `TURNSHAPE`, `DESIREDORBITALTITUDE` 등) 및 조정 가능 범위

**출력 경로**: `docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html`

**완료 검증**:
```bash
grep -c "ADDONS:MJ" docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html
# 결과: 10 이상
```

---

## STEP 5: 전체 완료 검증

```bash
# 4개 파일 모두 생성 확인
for f in \
  "docs/domain_knowledge/KOS_cheatsheet/note/terminal_open.html" \
  "docs/domain_knowledge/KOS_cheatsheet/mod/kerbal_engineer_redux.html" \
  "docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master/README.html" \
  "docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html"; do
  if [ -f "$f" ]; then
    LINES=$(wc -l < "$f")
    echo "OK  $f  ($LINES lines)"
  else
    echo "MISSING  $f"
  fi
done
```

```bash
# 각 파일의 6섹션 존재 확인
conda activate ./.venv && python - <<'EOF'
from pathlib import Path
from bs4 import BeautifulSoup

files = [
    "docs/domain_knowledge/KOS_cheatsheet/note/terminal_open.html",
    "docs/domain_knowledge/KOS_cheatsheet/mod/kerbal_engineer_redux.html",
    "docs/domain_knowledge/KOS_cheatsheet/kOS-Ferram-master/README.html",
    "docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html",
]
SECTIONS = ["Core Intent", "Safety", "Snippet", "Tuning", "Suffix", "Agent"]

for f in files:
    soup = BeautifulSoup(Path(f).read_text(), "html.parser")
    headings = [h.get_text(strip=True) for h in soup.find_all(["h2","h3"])]
    missing = [s for s in SECTIONS if not any(s in h for h in headings)]
    status = "OK" if not missing else f"MISSING {missing}"
    print(f"{status}  {f}")
EOF
```

최종 완료 후 마지막 commit 수행:

```bash
git add docs/domain_knowledge/KOS_cheatsheet/kOS.MechJeb2.Addon-main/README.html
git commit -m "nonhtml: add P3 mechjeb cheatsheet and final checks"
```

주의: 위 3개 commit 수행 후에도 `git push`는 금지한다.

---

## 완료 기준

- 4개 HTML 파일 모두 생성됨
- 각 파일에 6개 `<h2>` 섹션 모두 존재
- P1~P3 파일에 `<pre><code>` 블록 1개 이상
- P2 파일에 `ADDONS:FAR:` 포함 suffix 5개 이상
- P3 파일에 `ADDONS:MJ:` 포함 identifier 10개 이상
- 사용자에게 생성된 파일 목록 및 각 파일의 snippet/suffix 수 보고
