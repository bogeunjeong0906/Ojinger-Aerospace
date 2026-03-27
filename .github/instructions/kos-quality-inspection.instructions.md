---
applyTo: "docs/domain_knowledge/KOS_cheatsheet/**"
---

# KOS Cheatsheet 품질 검수 실행 지침

## 이 지침의 목적
AI 에이전트가 `docs/plans/kos_cheatsheet_quality_inspection.md`의 3-Tier 검수 계획을 자율적으로 실행한다.  
사용자의 추가 입력 없이 처음부터 끝까지 완료하고 결과를 보고한다.

---

## STEP 0: 선행 조건 확인

```bash
# 치트시트 파일 수 확인 (138개여야 함)
find docs/domain_knowledge/KOS_cheatsheet -name "*.html" -not -name "cooked_sample.html" | wc -l

# 환경 확인
conda activate ./.venv && python -c "from bs4 import BeautifulSoup; print('OK')"
```

138개 미만이면 먼저 변환 스크립트를 실행한다:
```bash
conda activate ./.venv && python scripts/kos_cheatsheet_converter.py --mode full
```

---

## STEP 1: Tier 1 자동 통계 검증

`scripts/kos_cheatsheet_quality_checker.py`가 존재하면 실행한다.  
존재하지 않으면 아래 인라인 스크립트로 Tier 1 통계를 수집한다:

```bash
conda activate ./.venv && python - <<'EOF'
import json, re
from pathlib import Path
from bs4 import BeautifulSoup

SRC = Path("docs/domain_knowledge/KOS_DOC")
DST = Path("docs/domain_knowledge/KOS_cheatsheet")
out = {"tier1": {}, "tier2": {}, "tier3": {}, "bugs": []}

files = [f for f in DST.rglob("*.html") if f.name != "cooked_sample.html"]
has_snippet, has_suffix, empty_section, low_token = [], [], [], []

SECTIONS = ["Core Intent", "Safety", "Snippet Pack", "Tuning", "Suffix", "Agent"]

for f in files:
    soup = BeautifulSoup(f.read_text(), "html.parser")
    headings = [h.get_text(strip=True) for h in soup.find_all(["h2","h3"])]
    
    # 6섹션 존재 여부
    missing = [s for s in SECTIONS if not any(s in h for h in headings)]
    if missing:
        empty_section.append({"file": str(f.relative_to(DST)), "missing_sections": missing})
    
    # snippet/suffix 유무
    snip_h = next((h for h in soup.find_all(["h2","h3"]) if "Snippet" in h.get_text()), None)
    suf_h  = next((h for h in soup.find_all(["h2","h3"]) if "Suffix" in h.get_text()), None)

    snip_ok = bool(snip_h and (snip_h.find_next("ul") or snip_h.find_next("pre")))
    suf_ok  = bool(suf_h  and (suf_h.find_next("ul")))

    if snip_ok: has_snippet.append(str(f.relative_to(DST)))
    if suf_ok:  has_suffix.append(str(f.relative_to(DST)))

    # 토큰 추정
    clean = re.sub(r"<[^>]+>", " ", f.read_text())
    tokens = len(re.sub(r"\s+", " ", clean)) // 4
    if tokens < 50:
        low_token.append({"file": str(f.relative_to(DST)), "tokens": tokens})

total = len(files)
out["tier1"] = {
    "total_files": total,
    "snippet_count": len(has_snippet),
    "snippet_rate": round(len(has_snippet)/total*100, 1),
    "suffix_count": len(has_suffix),
    "suffix_rate": round(len(has_suffix)/total*100, 1),
    "empty_section_count": len(empty_section),
    "empty_section_files": empty_section[:20],
    "low_token_files": low_token,
}

Path("docs/plans/results").mkdir(parents=True, exist_ok=True)
Path("docs/plans/results/quality_report.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(json.dumps(out["tier1"], indent=2, ensure_ascii=False))
EOF
```

---

## STEP 2: Tier 2 Priority 1 육안 검수

아래 4개 파일에 대해 소스와 치트시트를 각각 읽어 검수한다.  
**각 파일 검수 절차:**

1. 소스 HTML 읽기: `docs/domain_knowledge/KOS_DOC/{path}` 
2. 치트시트 읽기: `docs/domain_knowledge/KOS_cheatsheet/{path}`
3. 아래 체크리스트 확인 후 결과를 `quality_report.json`의 `tier2.priority1`에 기록

### 파일 1: commands/flight/cooked.html
체크:
- [ ] suffix 22개 이상 존재
- [ ] `STEERINGMANAGER:PITCHPID:KP`, `STEERINGMANAGER:PITCHPID:KI`, `STEERINGMANAGER:PITCHPID:KD` 포함
- [ ] `SHIP:VELOCITY:SURFACE`, `SHIP:VELOCITY:ORBIT` 포함
- [ ] Snippet에 `LOCK STEERING TO` 계열 코드 존재

### 파일 2: commands/flight/raw.html
체크:
- [ ] Snippet에 `SET SHIP:CONTROL:PITCH TO` 또는 `SHIP:CONTROL:` 계열 코드 존재
- [ ] suffix에 `SHIP:CONTROL:PITCH`, `SHIP:CONTROL:YAW`, `SHIP:CONTROL:ROLL` 포함

### 파일 3: structures/vessels/vessel.html
체크:
- [ ] suffix 10개 이상 존재
- [ ] `SHIP:VELOCITY:SURFACE`, `SHIP:ALTITUDE`, `SHIP:MASS` 계열 포함

### 파일 4: structures/vessels/control.html
체크:
- [ ] `SHIP:CONTROL:PITCH/YAW/ROLL/MAINTHROTTLE` 계열 포함
- [ ] Snippet 1개 이상 존재

---

## STEP 3: Tier 2 Priority 2 육안 검수

Priority 2 파일 5개 동일한 방법으로 검수. 각 파일에서 핵심 키워드가 존재하는지 확인:

| 파일 | 확인 키워드 |
|------|------------|
| `language/variables.html` | `LOCAL`, `GLOBAL`, `DECLARE`, `SET` |
| `language/user_functions.html` | `FUNCTION`, `PARAMETER`, `RETURN` |
| `language/flow.html` | `UNTIL`, `IF`, `WHEN...THEN` |
| `math/direction.html` | `HEADING`, `LOOKDIRUP` |
| `math/vector.html` | `V(`, `VDOT`, `VCRS` |

---

## STEP 4: Tier 2 Priority 3 — 추출 실패 의심 파일 원본 대조

의심 파일 5개에 대해 소스의 `div.highlight` 수와 치트시트의 snippet 수를 비교한다:

```bash
conda activate ./.venv && python - <<'EOF'
from pathlib import Path
from bs4 import BeautifulSoup

SUSPECTS = [
    "addons/AGX.html",
    "structures/misc/terminal.html",
    "structures/misc/resource_transfer.html",
    "language/anonymous.html",
    "language/syntax.html",
]
SRC = Path("docs/domain_knowledge/KOS_DOC")
DST = Path("docs/domain_knowledge/KOS_cheatsheet")

for rel in SUSPECTS:
    src_soup = BeautifulSoup((SRC / rel).read_text(), "html.parser")
    dst_soup = BeautifulSoup((DST / rel).read_text(), "html.parser")
    src_codes = len(src_soup.select("div.highlight"))
    dst_pres  = len(dst_soup.select("pre"))
    status = "OK" if src_codes == 0 or dst_pres > 0 else "BUG"
    print(f"{status}  {rel}  src_code_blocks={src_codes}  dst_snippets={dst_pres}")
EOF
```

`BUG`로 표시된 파일은 `quality_report.json`의 `bugs` 배열에 추가한다.

---

## STEP 5: Tier 3 Suffix 정확도 샘플 검증

```bash
conda activate ./.venv && python - <<'EOF'
import re
from pathlib import Path
from bs4 import BeautifulSoup

SAMPLES = [
    "structures/misc/steeringmanager.html",
    "structures/misc/pidloop.html",
    "structures/vessels/orbit.html",
    "math/direction.html",
    "commands/flight/cooked.html",
]
SRC = Path("docs/domain_knowledge/KOS_DOC")
DST = Path("docs/domain_knowledge/KOS_cheatsheet")
PAT = re.compile(r'\b([A-Z][A-Z0-9_]+(?::[A-Z][A-Z0-9_]+)+)\b')

for rel in SAMPLES:
    src_text = (SRC / rel).read_text() if (SRC / rel).exists() else ""
    dst_soup = BeautifulSoup((DST / rel).read_text(), "html.parser")

    src_suffixes = set(PAT.findall(re.sub(r"<[^>]+>", " ", src_text)))
    dst_suffixes = set(li.get_text(strip=True) for li in dst_soup.select("li"))
    dst_suffixes = {s for s in dst_suffixes if ":" in s}

    missing = src_suffixes - dst_suffixes
    extra   = dst_suffixes - src_suffixes
    print(f"--- {rel}")
    print(f"  src:{len(src_suffixes)}  dst:{len(dst_suffixes)}  missing:{len(missing)}  extra:{len(extra)}")
    if missing: print(f"  missing sample: {list(missing)[:5]}")
EOF
```

---

## STEP 6: 최종 판정 및 보고

`quality_report.json`의 모든 결과를 취합하여 판정:

| 등급 | 조건 |
|------|------|
| **Pass** | snippet_rate ≥ 75 AND Priority 1 전부 OK AND bugs 0건 |
| **Conditional Pass** | snippet_rate 65~75 OR Priority 1 중 경미한 누락 1건 |
| **Fail** | snippet_rate < 65 OR Priority 1 다수 이상 OR bugs ≥ 3건 |

판정 결과를 `quality_report.json`에 `verdict` 필드로 기록하고 사용자에게 요약 보고한다.

**Conditional Pass / Fail 시 처리:**
1. `bugs` 배열의 각 항목에 대해 소스에서 누락된 내용을 확인
2. 버그가 스크립트 추출 로직 문제인지, 원본 HTML 구조 문제인지 판단
3. 로직 문제 → `scripts/kos_cheatsheet_converter.py` 수정 후 `--mode full --force` 재실행
4. 원본 구조 예외 → 해당 파일만 수동 수정

---

## 완료 기준

- `docs/plans/results/quality_report.json` 생성됨
- `verdict` 필드가 `Pass` 또는 `Conditional Pass`
- 사용자에게 판정 등급, 주요 수치(snippet_rate, suffix_rate, bug 건수), 조치 사항 보고 완료
