# 프로젝트 지침

MODE: learning

@ARCHITECTURE.md

## 세션 시작
- `docs/explain-log.md`의 대기 수를 한 줄로 알린다. 0건이면 생략
- 대기가 한도(기본 1건)를 넘었으면 새 구현 전에 그 건부터 예측 질문으로 낸다
- 커밋 훅 확인은 전역 규칙 `ai-collab-repo-setup.md`가 한다

## 설계
- 순서 · 결정 등급 · 결정 카드: `ai-collab-design-briefing.md`
- 개발 범위를 시작할 때 흐름 지도부터 낸다
- 사람이 읽는 문서: 흐름 지도 `docs/flow-map.md`, 질문 지도 `docs/question-maps/QN-범위.md`
- 설계를 받아서 시작하면 빈칸 지도부터 만든다 (`ai-collab-design-briefing.md` "설계를 다른 곳에서 할 때")
- 기록용: 설계 메모 `docs/design-memos/DN-제목.md`, 결정 기록 `docs/adr/`
- 학습 가이드는 만들지 않는다

## 문서
- README · 발표 · 회고는 쓰기 전에 독자 · 한 줄 결론 · 순서를 닫는다 (`ai-collab-design-briefing.md` "문서를 쓸 때")
