# ai-collab-rules

AI로 빠르게 구현하면서도, 결과 코드를 직접 설명하고 책임질 수 있게 만드는 규칙과 스킬 모음입니다.

## 목차
1. 무엇을 하나
2. 구성
3. 설치
4. 새 프로젝트에 적용
5. 팀 프로젝트에 적용
6. 업데이트
7. 출처

## 1. 무엇을 하나

AI가 결정하고 AI가 기록하면, 사람은 이미 내려진 결정의 사후 해설만 읽게 됩니다. 그래서 결정을 두 종류로 나눕니다.

- **한쪽 문**: 되돌리기 비싼 결정(자료구조, 스키마, API, 모듈 경계, 외부 의존성, 새 패턴)은 사람이 내립니다.
- **양쪽 문**: 나머지는 AI가 결정하고 기록만 남깁니다.

검사는 세 겹입니다. 규칙으로 예방하고, 도구로 이상 징후를 잡고, 사람이 고른 곳만 직접 설명해 봅니다.
설계 배경과 결정 이유는 `docs/design-log.md`에 있습니다.

## 2. 구성

```
ai-collab-rules/
├── rules/        항상 적용되는 규칙 3개
├── skills/       필요할 때 불러 쓰는 절차 3개
├── templates/    프로젝트에 복사하는 CLAUDE.md, ARCHITECTURE.md
├── hooks/        커밋 직전 품질 경보 (pre-commit, quality_check.py)
└── docs/         설계 기록
```

| 종류 | 파일 | 역할 |
|---|---|---|
| 규칙 | `ai-collab-coding-discipline.md` | 최소 코드, 재사용 우선, 같은 일은 한 방식으로 |
| 규칙 | `ai-collab-change-summary.md` | 구현 전 예상 1줄, 커밋 요약 5줄 |
| 규칙 | `ai-collab-quality-alarms.md` | 복잡도·중복 경보 기준과 대응 |
| 스킬 | `one-way-door` | 중요한 결정 앞에서 선택지 제시, 결정 대기, ADR 초안 |
| 스킬 | `explain-back` | 사용자가 코드를 2줄로 설명하고 피드백 받기 |
| 스킬 | `weekly-audit` | 주 1회 품질 추세 점검 |
| 훅 | `hooks/pre-commit` | 커밋마다 새 복잡 함수·새 중복·예상 초과 LOC 경고 (커밋은 막지 않음) |

## 3. 설치

규칙은 `~/.claude/rules/`에, 스킬은 `~/.claude/skills/`에 복사합니다. 한 번 설치하면 모든 프로젝트에 적용됩니다.

Windows (PowerShell):
```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\rules", "$HOME\.claude\skills" | Out-Null
Copy-Item rules\*.md "$HOME\.claude\rules\" -Force
Copy-Item skills\* "$HOME\.claude\skills\" -Recurse -Force
```

macOS / Linux:
```bash
mkdir -p ~/.claude/rules ~/.claude/skills
cp rules/*.md ~/.claude/rules/
cp -r skills/* ~/.claude/skills/
```

설치 확인: Claude Code에서 `/memory` 또는 `/context`로 규칙 파일이 불러와졌는지, 스킬 목록에 세 스킬이 보이는지 확인합니다.

## 4. 새 프로젝트에 적용

1. `templates/CLAUDE.md`와 `templates/ARCHITECTURE.md`를 프로젝트 루트에 복사합니다.
2. CLAUDE.md의 `MODE:`를 정합니다.
   - `learning`: 배우는 단계. 핵심 알고리즘, 에러 처리, 테스트 전략도 사람이 결정합니다.
   - `ship`: 출시 단계. 한쪽 문 기본 목록만 사람이 결정합니다.
3. ARCHITECTURE.md의 모듈 맵과 단일 방식 규칙을 채웁니다. 처음에는 비워 두고, 첫 한쪽 문 결정 때부터 채워도 됩니다.
4. 커밋 훅을 설치합니다. 프로젝트 저장소마다 한 번 합니다.
   ```bash
   cp <ai-collab-rules>/hooks/pre-commit <ai-collab-rules>/hooks/quality_check.py .git/hooks/
   chmod +x .git/hooks/pre-commit   # macOS/Linux
   pip install lizard               # 복잡도 검사
   ```
   중복 검사는 Node.js가 있으면 `npx jscpd`로 자동 실행됩니다. 도구가 없으면 해당 검사만 건너뛰고 안내 한 줄을 띄웁니다.
   경보 기록은 `.git/ai-alarms.log`에 쌓입니다.

## 5. 팀 프로젝트에 적용

팀원의 AI도 같은 규칙을 읽어야 하면, `rules/`의 파일을 저장소의 `.claude/rules/`에 복사해 커밋합니다.
Claude Code가 아닌 도구(AGENTS.md를 읽는 도구 등)를 함께 쓰면, 해당 도구의 설정 파일에서 같은 규칙 파일을 가리키게 합니다.

## 6. 업데이트

이 저장소가 원본입니다. 규칙이나 스킬을 고친 뒤에는 3번 설치 명령을 다시 실행해 `~/.claude/`의 사본을 갱신합니다.

변경 내역은 `CHANGELOG.md`에 남기고, 버전은 git 태그로 찍습니다.

## 7. 출처

- 코딩 규율은 Karpathy 코딩 가이드라인(multica-ai/andrej-karpathy-skills, MIT)을 각색했습니다.
- 한쪽 문 / 양쪽 문은 제프 베이조스의 2015년 주주 서한(Type 1 / Type 2 결정)에서 가져왔습니다.
- 장황성·침식도 지표는 SlopCodeBench 소개 글을 참고했습니다.
