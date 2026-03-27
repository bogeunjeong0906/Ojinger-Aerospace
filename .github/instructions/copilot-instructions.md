---
applyTo: "docs/domain_knowledge/KOS_DOC/**/*.html"
---

# KOS_DOC -> KOS_cheatsheet 구현 규칙

## 목적
KOS 공식 문서를 AI 에이전트가 빠르게 검색/회수/코드생성에 활용할 수 있는 스니펫 중심 치트시트로 변환한다.

## Git 운영 규칙 (필수)
- 작업 중간중간 의미 단위로 commit 한다.
- 변환 작업에서는 최소 2회 commit 한다: (1) 변환 실행 결과 (2) 검증/수정 반영.
- 작업 중 `git push`는 금지한다.
- 사용자의 명시적 승인 없이 `git push`, `git push --force`를 실행하지 않는다.

## 입력/출력 경로 규칙
- 입력 루트: docs/domain_knowledge/KOS_DOC
- 출력 루트: docs/domain_knowledge/KOS_cheatsheet
- 샘플 루트: docs/domain_knowledge/KOS_cheatsheet

## 무손실 구조 규칙
- 원본 디렉토리 구조를 출력에 동일하게 복제한다.
- 치트시트 파일명은 원본과 동일하게 유지한다.
- 파일 suffix(.html 포함)는 절대 변경하지 않는다.
- 원문에서 등장한 suffix/키워드(예: STEERINGMANAGER:PITCHPID:KD)를 누락하지 않는다.

## 콘텐츠 변환 규칙 (스니펫 추출 우선)
- 문서 상단에 source file, source title, version 메타를 기록한다.
- 다음 순서로 구조화한다:
  1) Core Intent
  2) Safety Critical Notes
  3) Snippet Pack (즉시 실행 가능한 코드)
  4) Tuning/Parameters
  5) Suffix and Key Inventory (무손실 목록)
  6) Agent Usage Hints
- 설명은 짧게, 코드/명령/속성명은 원문 표기를 유지한다.
- 경고/제약(WAIT 금지, SAS 충돌 등)은 별도 섹션으로 승격한다.

## 토큰 절감 원칙
- 불필요한 서사/중복 문장을 제거한다.
- 긴 배경 설명은 1~3문장 요약으로 압축한다.
- 예시는 실행 가치가 높은 것만 남기고, 중복 예시는 제거한다.
- 단, suffix/핵심 키 이름은 누락 없이 inventory에 보존한다.

## 샘플 참조
- 샘플 파일: docs/domain_knowledge/KOS_cheatsheet/cooked_sample.html
- 샘플은 아래를 만족한다:
  - 샘플 파일명은 *_sample.html 형태로 출력 루트 바로 아래에 위치
  - 스니펫 우선 구성
  - 경고/제약 분리
  - suffix inventory 포함
