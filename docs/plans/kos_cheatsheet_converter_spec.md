# KOS_DOC Cheatsheet Converter - 명세서

**작성일**: 2026-03-28  
**버전**: 1.0  
**상태**: 승인됨

---

## 1. 목적

KOS 공식 HTML 문서(`KOS_DOC`)를 AI 에이전트가 사용하기 용이한 스니펫 중심 치트시트로 **자동 변환**하는 Python CLI 스크립트를 구현한다.  
AI 에이전트는 스크립트를 터미널에서 실행하고 리포트를 확인하는 역할만 담당한다.

## 1-1. Git 운영 규칙 (Autopilot)

- 작업 중간중간 의미 단위로 commit 한다.
- 기본 commit checkpoint:
  1) 변환 실행 결과 생성 직후
  2) 검증/후처리 수정 직후
  3) 최종 리포트/상태 반영 직후
- 작업 중 `git push`는 금지한다.
- 원격 반영은 사용자의 명시적 승인 이후에만 수행한다.

---

## 2. 파일 구성

```
scripts/
  kos_cheatsheet_converter.py   ← 메인 실행 스크립트 (단일 파일)
docs/
  domain_knowledge/
    KOS_DOC/                    ← 입력 루트 (읽기 전용)
    KOS_cheatsheet/             ← 출력 루트
      cooked_sample.html        ← 샘플 (구현 기준 참조)
```

---

## 3. CLI 인터페이스

```bash
python scripts/kos_cheatsheet_converter.py [OPTIONS]
```

### 옵션

| 옵션 | 단축 | 기본값 | 설명 |
|---|---|---|---|
| `--src` | `-s` | `docs/domain_knowledge/KOS_DOC` | 입력 루트 경로 |
| `--dst` | `-d` | `docs/domain_knowledge/KOS_cheatsheet` | 출력 루트 경로 |
| `--mode` | `-m` | `full` | `full` \| `incremental` \| `dry-run` |
| `--force` | | False | 기존 출력 파일 덮어쓰기 강제 |
| `--report` | | True | 변환 통계 리포트 출력 |
| `--log-level` | | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |

### 실행 예시

```bash
# 가상환경 활성화 (필수)
conda activate ./.venv

# 전체 변환 (기본)
python scripts/kos_cheatsheet_converter.py

# 특정 경로 지정
python scripts/kos_cheatsheet_converter.py --src docs/domain_knowledge/KOS_DOC --dst docs/domain_knowledge/KOS_cheatsheet

# dry-run: 파일 쓰기 없이 실행 결과만 확인
python scripts/kos_cheatsheet_converter.py --mode dry-run

# 증분 변환: 마지막 실행 이후 수정된 파일만 처리
python scripts/kos_cheatsheet_converter.py --mode incremental
```

---

## 4. 처리 파이프라인

```
[1] 파일 스캔     →   [2] HTML 파싱   →   [3] 치트시트 렌더링   →   [4] 파일 저장   →   [5] 검증   →   [6] 리포트
```

### 4-1. 파일 스캔
- 입력 루트를 재귀 탐색하여 `.html` 파일 목록을 수집
- `incremental` 모드는 `.cheatsheet_state.json` (출력 루트 아래)에 저장된 `mtime` 기준으로 신규/변경 파일만 필터링
- 비-HTML 파일은 그대로 경로 복사(바이너리 리소스 등은 변환 대상에서 제외)

### 4-2. HTML 파싱

BeautifulSoup4(`html.parser`)를 사용하며, 다음 순서로 블록을 추출한다.

| 추출 대상 | HTML 선택자 | 용도 |
|---|---|---|
| 문서 제목 | `<title>` | CHEATSHEET_META |
| h1/h2/h3 | `h1, h2, h3` | 섹션 인지 |
| 코드 블록 | `pre > code`, `.highlight pre` | Snippet Pack |
| 경고/주의 | `.admonition-title`, `.admonition.warning`, `.admonition.note` | Safety Critical Notes |
| suffix 후보 | `code.xref`, `code.docutils.literal`, `.sig-name .pre` | Suffix Inventory |
| 핵심 설명 | `dl.object > dd > p:first-child` | Core Intent 보충 |

**제거 대상 (네비게이션/보일러플레이트)**

- `nav`, `footer`, `.wy-nav-side`, `.wy-breadcrumbs`, `.rst-footer-buttons`, `<head>`, `<script>`, `<link>`, `<style>`

### 4-3. 치트시트 렌더링

출력 포맷은 `.html` 파일이며, 아래 고정 섹션 순서를 따른다.

```html
<!-- CHEATSHEET_META
source_file: <원본 상대경로>
source_doc_title: <title에서 추출>
source_doc_version: kOS 1.4.0.0 documentation
cheatsheet_type: snippet-first, agent-oriented
-->

<h1>{제목}</h1>

<h2>1) Core Intent</h2>
<!-- h1 직하 첫 단락 + dl.object 핵심 설명 1~3문장 -->

<h2>2) Safety Critical Notes</h2>
<!-- admonition.warning 블록 전체 보존 -->

<h2>3) Snippet Pack</h2>
<!-- pre/code 블록 전체 보존 (kerboscript/none 클래스 구분) -->

<h2>4) Tuning / Parameters</h2>
<!-- "Tuning", "Settings", "Parameters" 포함 h2/h3 섹션 내용 -->
<!-- 해당 내용 없으면 섹션 자체 생략 -->

<h2>5) Suffix and Key Inventory</h2>
<!-- code.xref / .sig-name .pre에서 추출한 suffix 목록 <ul> -->

<h2>6) Agent Usage Hints</h2>
<!-- admonition.note 블록 + 문서 내 "Note:" 단락 -->
```

### 4-4. 파일 저장

- 출력 경로 = `dst / (원본 파일의 src 기준 상대경로)`
- 출력 디렉토리가 없으면 자동 생성
- `--force` 없이 기존 파일이 있으면 건너뛰고 WARNING 로그 기록
- 저장 후 `mtime`을 `.cheatsheet_state.json`에 기록

### 4-5. 검증

각 파일 저장 후 즉시 아래를 검사한다.

| 검증 항목 | 합격 기준 | 실패 시 동작 |
|---|---|---|
| 경로/파일명 보존 | 출력 상대경로 == 입력 상대경로 | ERROR 로그 + 건너뜀 |
| 파일 suffix 보존 | `.html` 유지 | ERROR 로그 |
| 코드 블록 존재 | Snippet Pack ≥ 0개 (없어도 허용, 단 WARNING) | WARNING |
| suffix inventory 존재 | 5개 이상 추출 불가 시 WARNING | WARNING |

### 4-6. 리포트

변환 완료 후 stdout에 요약 출력:

```
==============================
KOS Cheatsheet Converter Report
==============================
Mode         : full
Source       : docs/domain_knowledge/KOS_DOC
Destination  : docs/domain_knowledge/KOS_cheatsheet
------------------------------
Total scanned     : 138 files
Converted (new)   : 138 files
Skipped (exist)   : 0 files
Errors            : 0 files
------------------------------
Total snippets    : 874
Total suffixes    : 1203
Estimated tokens  : ~24,100
------------------------------
Duration : 3.2 sec
State saved: docs/domain_knowledge/KOS_cheatsheet/.cheatsheet_state.json
==============================
```

---

## 5. 의존성

```yaml
# environment.yml에 추가 필요
dependencies:
  - beautifulsoup4>=4.12
  - lxml          # BeautifulSoup 파서 옵션
```

설치 확인:
```bash
conda activate ./.venv
python -c "from bs4 import BeautifulSoup; print('OK')"
```

---

## 6. 상태 파일 스키마 (`.cheatsheet_state.json`)

증분 변환에 사용하는 상태 파일. 출력 루트 바로 아래에 저장.

```json
{
  "version": 1,
  "last_run": "2026-03-28T01:40:00",
  "files": {
    "commands/flight/cooked.html": {
      "src_mtime": 1711548000.0,
      "dst_mtime": 1711548010.0,
      "snippets": 5,
      "suffixes": 23
    }
  }
}
```

---

## 7. AI 에이전트 실행 절차 (Runbook)

에이전트는 아래 순서만 따른다. 스크립트 내부 로직은 수정하지 않는다.

```
Step 1  : conda activate ./.venv
Step 2  : python scripts/kos_cheatsheet_converter.py --mode dry-run
           → 오류 없으면 Step 3으로 진행
Step 3  : python scripts/kos_cheatsheet_converter.py --mode full --report
           → "Errors : 0" 확인
Step 4  : 리포트의 "Estimated tokens"와 "Errors" 값을 사용자에게 보고
Step 5  : 오류 발생 시 로그 파일 내용을 복사해 보고 (재시도 금지, 사용자 판단 대기)
```

---

## 8. 구현 범위 (Phase별)

| Phase | 내용 | 완료 기준 |
|---|---|---|
| Phase 1 (MVP) | 파일 스캔 + 기본 파싱 + 고정 템플릿 출력 + 경로 무손실 검증 | 138개 파일 전부 변환 성공, Errors=0 |
| Phase 2 | suffix inventory 정교화, 경고 우선 추출, dry-run/incremental 모드 | dry-run 동작, 재실행 시 증분 처리 |
| Phase 3 | 리포트 토큰 추정, state 파일 관리, CI 검사 스크립트 | state.json 생성, token 추정 ±10% 이내 |

---

## 9. 비기능 요구사항

- **외부 API 사용 금지**: 외부 LLM/API 호출 없음. 순수 로컬 Python 처리.
- **재현성**: 동일한 입력에 대해 항상 동일한 출력 생성.
- **속도**: 138개 파일 전체 변환 30초 이내 완료 목표.
- **문자 인코딩**: 입/출력 모두 UTF-8.
- **에러 격리**: 단일 파일 파싱 실패가 전체 배치를 중단시키지 않음.
