# Changelog

## v0.2 (작업 중, mini-react 1주 적용 결과 반영)
근거: explain-back 대기 11건 · 완료 0건, weekly-audit 0회, AI가 설계를 끝낸 뒤 물어서 사람이 결정 이유를 따라가지 못함.

설계 순서
- 규칙 `ai-collab-design-briefing.md` 추가: 설계 전에 질문 지도를 내고 사람이 위에서부터 하나씩 결정한다. 결정 등급(묻기 · 알려주기 · 맡기기), 5줄 결정 카드, 짧은 채팅 브리핑, 규칙 변경은 승인 후 반영
- 템플릿 `question-map.md` 추가: 사람이 작업 중에 읽는 유일한 설계 문서
- 템플릿 `design-memo.md` 추가: 기록용. 질문 지도의 답을 옮겨 쓴다
- 템플릿 `CLAUDE.md`: 질문 지도 위치, 세션 시작 때 explain-back 대기 수 보고
- 새 추상화를 [패턴]과 [도우미]로 나눔. [패턴]만 질문 지도에 올려 사람이 정하고, [도우미]는 커밋에 한 줄

스킬
- `one-way-door`: 선택지 표를 5줄 결정 카드로 바꿈(용어 대신 결과, 이름은 고른 뒤). "추천대로"는 위임으로 표시하고 explain-log 대기에 넣음. ADR의 "결정 이유 (사용자 작성)" 빈칸을 없애고 카드에서 옮겨 씀
- `explain-back`: 두 줄 설명을 예측 질문 1개로 바꿈. 대상은 위임한 결정 · AI가 정한 작동 원리 · 경보 diff. 하루 무작위 1건 삭제. 기록 형식을 `대기·통과·보완·건너뜀`으로 통일
- `weekly-audit`를 `phase-audit`로 바꿈: 주 1회 대신 단계가 끝날 때 한 번. 기록에 단계 이름 추가

커밋 훅
- explain-back 대기 수를 한 줄로 보여 줌 (커밋은 막지 않음)
- 경보 기록에 날짜 · 브랜치 · 파일 위치를 남김
- 중복은 내용으로 구분해 옮긴 코드를 새 중복으로 세지 않음. 테스트 파일끼리의 중복은 제외
- LOC는 소스 증가만 예상과 비교하고 테스트 증가는 따로 표시. 예상 줄 수는 비교 후 삭제
- 협업 도구 폴더(`ai-collab-rules/`)는 검사에서 제외, Windows 한글 깨짐 수정
- `pre-push` 추가: main 직접 push 차단 (선택 설치)

기타
- MIT 라이선스 추가, 출처 표기 보강
- `.gitattributes`로 훅 파일 줄바꿈을 LF로 고정

## 후보 (아직 안 정함)
- explain-back 대기 한도 (v0.2는 강제 없음. 질문 지도의 효과를 먼저 본다)

## v0.1 — 2026-11-06
- 규칙 3개: coding-discipline, change-summary, quality-alarms
- 스킬 3개: one-way-door, explain-back, weekly-audit
- 템플릿: CLAUDE.md, ARCHITECTURE.md
- 커밋 훅: 새 CC>10 함수, 새 중복, 예상 2배 초과 LOC 경고 (차단 없음)
- 확정: learning 모드 한쪽 문 추가 항목(알고리즘·동시성/에러 처리·테스트 전략), 무작위 explain-back 하루 1건
