# 호스트별 실행 어댑터

공통 업무 흐름은 [합성 고객 여정](workflow-examples.md)을 따른다. 각 호스트는 독립적으로 사용할 수 있다. plugin/skill 파일은 지침을 제공하고, MCP 권한·제품 상태·도구 schema는 연결된 서버가 제공한다. 번들의 도구 schema 후보는 [구현 도구 스냅샷](implemented-tools.snapshot.json)에 있다. 실제 사용 가능 여부는 연결된 서버의 도구 목록과 schema로 확인한다. 업무별 후보 capability와 미지원 fallback은 [워크플로 capability 표](workflow-capabilities.json)에 있다. 매 작업에서 호스트가 실제 보여주는 도구와 입력 schema를 다시 확인한다.

## 내장 Copilot

- 제품이 제공하는 연결과 인증을 사용한다. 외부 marketplace 설치나 Claude/Codex OAuth 절차를 요구하지 않는다.
- 내장 Copilot은 `set_organization`으로 조직을 바꿀 수 없다. 다른 조직 작업이 필요하면 제품 화면에서 조직을 바꾼 새 대화로 이어간다.
- 음성 시험 도구는 없어 고객이 제품 UI에서 직접 시험한다. 번호 연결·발신·캠페인·통화 조회는 연결된 도구로 수행하며 실제 영향이 있는 도구는 [실행 계약](execution-contract.md)의 확인·실행 키 규칙을 따른다. 완료 여부는 고객 보고와 MCP readback을 구분한다.
- 예: “첨부한 합성 서비스 설명으로 첫 Manual을 만들고, 저장 후 전체 본문과 revision을 다시 읽어줘.” 이전 Thread에 접근할 수 없을 때만 실제 ID와 마지막 결정을 사용자에게 받아 검증한다.

### 만들기 질문과 우선 규칙
- 질문은 응답 형식 안내의 `vox-decisions` 블록으로 낸다. 칸 키와 선택지는 [정할 칸](decision-slots.json)을 쓰고, 이미 카드로 답한 칸은 다시 묻지 않는다. `feel` 칸(목소리·응대 느낌)은 첫 저장 뒤 들어 보고 고르는 카드로만 낸다.
- 응답 형식 안내가 `build-first-voice-agent`의 다음 단계보다 우선한다.
  - 배포: `deploy_agent`(현재를 새 버전으로 만들어 바로 프로덕션으로 지정)는 사용자가 요청할 때만 호출한다. 도구 목록에 없으면 배포하지 않고 변경 검토 카드로 안내한다.
  - 마무리 보고: 응답 형식 안내를 따르고, 기본값으로 정한 칸은 "제가 정한 것" 한 줄로 남긴다.
  - 예시값: 사용자가 예시라고 밝힌 값만 미정으로 보고 실제 값을 묻는다. 그 밖의 구체 값은 그대로 쓴다.
- 칸 토큰(기본 꺼짐): 응답 형식 안내가 켰을 때만 사용자만 아는 값을 `⟦slot:<칸 키>|<추측 기본값>⟧`으로 저장한다. 남은 토큰은 게시·번호 연결·발신 전에 서버가 막는다. 꺼져 있으면 모르는 값은 지어내지 않고 그 동작을 빼거나 미정으로 알린다.
- 초안 호스트: 저장·재조회·검증은 `draft_patch`·`draft_read`·`draft_validate`, 지침은 `read_guide`. 게시는 사람이 한다.

## Codex

- Codex plugin marketplace 흐름으로 plugin을 설치하고 MCP 연결은 Codex 호스트의 OAuth UI에서 완료한다. 토큰을 대화나 작업 파일에 복사하지 않는다.
- 설치 후 현재 연결, 조직과 노출 도구를 확인한다. plugin이 내장 Copilot의 Thread DB, E2B 작업 경로 또는 private 파일을 읽을 수 있다고 가정하지 않는다.
- 저장소 작업공간의 자료나 사용자가 첨부한 파일만 실제 호스트가 읽을 수 있는 범위에서 사용한다. URL 열람 여부도 그 Codex 세션의 도구로 확인한다.
- 자연어로 요청하거나 설치된 vox.ai skill을 호출한다. 저장은 받은 실제 `agent_id`/`manual_id`와 현재 revision을 사용하고, 결과를 재조회한다.
- 음성 시험은 고객이 제품 UI에서 직접 한다. 번호 연결·발신·캠페인·통화 조회는 도구로 하고, 발신·게시·번호 연결 전에는 대화에서 요약 확인을 받는다. 이어서 작업할 때는 Codex가 접근 가능한 대화 기록이나 사용자 handoff를 사용한다.
- 예: “`service-brief.md`를 근거로 첫 Manual을 만들고 저장값을 확인해줘.” 새 Codex 대화에서 이어갈 때는 사용자가 실제 ID, 마지막 결정, 시험 상태를 전달한다.

## Claude Code

- Claude Code plugin marketplace 흐름으로 plugin을 설치하고 MCP OAuth 연결을 호스트에서 완료한다. Codex 설정이나 내장 연결을 재사용한다고 가정하지 않는다.
- Claude Code에서는 `/vox-ai:build-first-voice-agent` 또는 `/vox-ai:try-and-improve-voice-agent`처럼 관련 skill을 명시적으로 부를 수 있고, 일반 자연어 요청도 가능하다.
- 제품 변경 뒤 실제 MCP 응답을 재조회한다. 고객이 직접 시험한 결과는 `customer_reported`; 실제 제품 call 조회 근거는 조회 도구와 결과가 확인된 경우에만 별도로 표시한다.
- 음성 시험은 고객이 제품 UI에서 직접 한다. 번호 연결·발신·캠페인·통화 조회는 도구로 하고, 발신·게시·번호 연결 전에는 대화에서 요약 확인을 받는다. 새 Claude Code 대화에서는 사용자가 제공한 handoff로 재개한다.
- 예: `/vox-ai:build-first-voice-agent`를 사용해 사용자가 제공한 서비스 자료로 첫 Manual을 만들고, 저장한 `agent_id`와 `manual_id`를 기록해줘. 새 호스트 대화에 상태가 자동 전달됐다고 가정하지 않는다.

## Grok Build

- Grok Build는 저장소의 `.claude-plugin` manifest와 `.mcp.json`, `skills/`를 그대로 읽는다. `grok plugin install https://github.com/vox-public/plugin.git`으로 설치하고 MCP OAuth 로그인은 TUI의 `/mcps`에서 완료한다.
- 그 밖의 원칙(조직·도구 확인, 저장 뒤 재조회, 고객 직접 음성 시험, 발신·게시·번호 연결 전 요약 확인, 새 대화에서는 handoff)은 Claude Code 절과 같다. Claude Code 전용 `/vox-ai:<skill>` 호출 형식을 가정하지 않고 설치된 skill을 선택하거나 자연어로 요청한다.

## 공식 문서 연결

plugin은 제품 MCP(`vox-ai`) 외에 공식 문서 MCP(`vox-docs`, `https://docs.tryvox.co/mcp`)를 함께 연결한다. 문서 검색은 [product-documentation](../skills/product-documentation/SKILL.md)을 따르고, 문서 MCP를 제품 데이터 접근이나 권한의 근거로 쓰지 않는다. `vox-docs`가 없는 호스트는 `https://docs.tryvox.co/llms.txt`를 읽는다.

## 연결·파일·재개 공통 원칙

- MCP 연결 성공, 인증, 제품 업무 완료는 서로 다른 상태다. 실제 호스트가 제공하는 조직·도구·schema를 확인한다.
- 호스트가 required tool을 제공하지 않으면 제품 write를 추측하거나 REST/CLI/DB로 우회하지 않는다. 가능한 자료 정리와 Manual 초안을 이어가고 빠진 capability를 말한다.
- 제품 file reference, 호스트 첨부, 로컬 경로는 서로 대체할 수 없다. 자료를 실제로 읽지 못했으면 분석했다고 표현하지 않는다.
- Thread/호스트 간 연속성은 접근 가능한 대화 기록이나 사용자 제공 handoff로 이어가며, 자동 공유 기억이 있다고 설명하지 않는다.
- 음성 시험은 고객이 제품 UI에서 하고 운영 호출은 도구로 한다. 고객의 음성 피드백은 reported로 기록하고, `get_call`로 조회한 통화만 독립 call evidence로 올린다. 짧은 요약과 필요한 최소 locator만 기록하며 외부 transcript 전체를 가져오지 않는다.
