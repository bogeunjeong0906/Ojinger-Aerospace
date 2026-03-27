# KOS Cheatsheet 구현 품질 검수 계획

**작성일**: 2026-03-28  
**버전**: 1.0  
**상태**: 실행 대기  
**담당**: AI 에이전트 (autopilot)  

---

## 1. 목적

`scripts/kos_cheatsheet_converter.py`로 자동 생성된 138개 치트시트 파일의 품질을 체계적으로 검증한다.  
검수 결과를 `docs/plans/results/quality_report.json`에 기록하고 Pass/Conditional/Fail 판정을 내린다.

---

## 2. 선행 조건

| 항목 | 확인 방법 |
|------|-----------|
| 치트시트 변환 완료 | `docs/domain_knowledge/KOS_cheatsheet/*.html` 존재 확인 |
| 상태 파일 존재 | `docs/domain_knowledge/KOS_cheatsheet/.cheatsheet_state.json` 존재 확인 |
| Python 환경 | `conda activate ./.venv` 후 `python -c "from bs4 import BeautifulSoup"` 성공 확인 |

---

## 3. 검수 체계 (3-Tier)

### Tier 1: 자동 통계 검증

**실행 커맨드:**

```bash
conda activate ./.venv
python scripts/kos_cheatsheet_quality_checker.py \
  --source docs/domain_knowledge/KOS_DOC \
  --cheatsheet docs/domain_knowledge/KOS_cheatsheet \
  --output docs/plans/results/quality_report.json
```

**검사 항목:**

| 항목 | 판정 기준 | 정상 케이스 예외 |
|------|-----------|----------------|
| 6섹션 모두 존재 | `<h2>` 태그로 Core Intent / Safety / Snippet Pack / Tuning / Suffix Inventory / Agent Hints 헤더 6개 확인 | 없음 |
| Snippet 보유율 | **실코드 보유 파일** 기준 ≥75% (참조 전용 Overview 페이지 제외) | `structures/celestial_bodies.html` 등 index 역할 페이지 |
| Suffix 보유율 | 전체 파일 기준 ≥85% | index/overview 페이지 |
| 빈 섹션 | 각 섹션 `<ul>` 또는 `<pre>` 안에 실제 내용 1개 이상 존재 | 원본에도 내용이 없는 경우 |
| 토큰 추정 | 파일당 최소 50 tokens (생성 실패 탐지) | 없음 |

**Overview 파일 판별 기준:**
소스 HTML에 `div.highlight pre` 또는 `dt.sig` 태그가 0개이고 파일명이 하위 디렉토리 인덱스인 경우 (예: `structures/vessels.html`, `structures/collections.html`).

### Tier 2: 우선순위별 수동 육안 검수

에이전트는 아래 목록을 **순서대로** 처리한다. 각 파일은 소스 HTML과 치트시트 HTML을 나란히 읽어 비교한다.

**Priority 1 — 비행 제어 핵심 (반드시 검수)**

| 소스 파일 | 치트시트 파일 | 검수 포인트 |
|-----------|-------------|------------|
| `commands/flight/cooked.html` | 동일 경로 | `cooked_sample.html`(수동 기준, 23 suffix)과 비교 — suffix 22개 이상, STEERINGMANAGER:PITCHPID:KP/KI/KD 포함 확인 |
| `commands/flight/raw.html` | 동일 경로 | Snippet Pack에 `SET SHIP:CONTROL:PITCH TO` 계열 코드 포함 확인 |
| `structures/vessels/vessel.html` | 동일 경로 | suffix 10개 이상, `SHIP:VELOCITY:SURFACE` 포함 확인 |
| `structures/vessels/control.html` | 동일 경로 | `SHIP:CONTROL:PITCH/YAW/ROLL` 계열 suffix 포함 확인 |

**Priority 2 — 언어/수학 (검수 권장)**

| 소스 파일 | 검수 포인트 |
|-----------|------------|
| `language/variables.html` | `LOCAL`, `GLOBAL`, `DECLARE` 키워드 snippet 포함 |
| `language/user_functions.html` | `FUNCTION`, `PARAMETER`, `RETURN` 사용 예제 포함 |
| `language/flow.html` | `UNTIL`, `IF`, `WHEN...THEN` 구문 snippet 포함 |
| `math/direction.html` | `HEADING()`, `LOOKDIRUP()` 등 함수 signature 포함 |
| `math/vector.html` | `V()`, `VDOT()`, `VCRS()` snippet 포함 |

**Priority 3 — 추출 실패 의심 파일 (반드시 원본 대조)**

소스에 실제 코드가 있음에도 Snippet/Suffix가 0개인 파일들을 원본과 대조한다.

| 파일 | 원본에 코드 있는지 확인 방법 |
|------|-----------------------------|
| `addons/AGX.html` | 소스에서 `div.highlight` 태그 수 출력 |
| `structures/misc/terminal.html` | 소스에서 `div.highlight` 태그 수 출력 |
| `structures/misc/resource_transfer.html` | 소스에서 `div.highlight` 태그 수 출력 |
| `language/anonymous.html` | 소스에서 `div.highlight` 태그 수 출력 |
| `language/syntax.html` | 소스에서 `div.highlight` 태그 수 출력 |

원본에 코드가 있는데 치트시트에 없으면 → **버그 리포트 기록** (quality_report.json의 `bugs` 배열)

### Tier 3: Suffix 정확도 샘플 검증

다음 5개 파일을 무작위 샘플로 지정하여 치트시트 suffix 목록이 원본 HTML 내 실제 등장 identifier와 일치하는지 확인한다.

```
structures/misc/steeringmanager.html
structures/misc/pidloop.html
structures/vessels/orbit.html
math/direction.html
commands/flight/cooked.html
```

검증 방법: 소스에서 `grep -oP '[A-Z][A-Z0-9_]+(?::[A-Z][A-Z0-9_]+)+' {source_file}` 결과와 치트시트 suffix 목록을 집합 비교 — 치트시트에 있는 항목이 소스에도 있는지 (정밀도 확인)

---

## 4. 판정 기준

| 등급 | 조건 | 조치 |
|------|------|------|
| **Pass** | Snippet 보유율 ≥75% AND Priority 1 전부 OK AND 버그 0건 | 검수 완료 선언 |
| **Conditional Pass** | Snippet 보유율 65~75% OR Priority 1 중 1건 경미한 누락 | 발견된 버그만 픽스 후 해당 파일 재변환 |
| **Fail** | Snippet 보유율 <65% OR Priority 1 다수 이상 OR 버그 3건 이상 | 스크립트 추출 로직 전반 재검토 후 full 재변환 |

---

## 5. 출력물

| 파일 | 내용 |
|------|------|
| `docs/plans/results/quality_report.json` | Tier 1 통계, Tier 2 체크 결과, Tier 3 샘플 결과, 최종 판정, 버그 목록 |

### quality_report.json 스키마

```json
{
  "generated_at": "ISO8601",
  "verdict": "Pass | Conditional Pass | Fail",
  "tier1": {
    "total_files": 0,
    "snippet_rate": 0.0,
    "suffix_rate": 0.0,
    "empty_section_files": [],
    "low_token_files": []
  },
  "tier2": {
    "priority1": [
      { "file": "", "status": "OK | WARN | FAIL", "notes": "" }
    ],
    "priority2": [
      { "file": "", "status": "OK | WARN | FAIL", "notes": "" }
    ],
    "priority3": [
      { "file": "", "source_code_blocks": 0, "cheatsheet_snippets": 0, "status": "OK | BUG" }
    ]
  },
  "tier3": {
    "samples": [
      { "file": "", "source_suffixes": [], "cheatsheet_suffixes": [], "missing": [], "extra": [] }
    ]
  },
  "bugs": [
    { "file": "", "description": "", "severity": "critical | major | minor" }
  ]
}
```

---

## 6. 실행 순서 요약

```
1. 선행 조건 확인
2. python scripts/kos_cheatsheet_quality_checker.py 실행 → quality_report.json 생성
3. Tier 2 Priority 1 파일 4개 순차 육안 검수 → report에 기록
4. Tier 2 Priority 2 파일 5개 검수 → report에 기록  
5. Tier 2 Priority 3 의심 파일 원본 대조 → 버그 발견 시 기록
6. Tier 3 샘플 5개 suffix 정확도 검증 → report에 기록
7. 최종 판정 기록 및 사용자에게 결과 보고
8. Conditional Pass / Fail 시 → 버그픽스 후 재변환 
```
