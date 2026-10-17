---
name: agents-platform
description: "연결된 vox.ai Agents MCP에서 조직·현재 도구 capability와 작업 context를 확인하고 agent·Manual 작업을 수행할 때 적용한다. 상담원의 실시간 통화 업무에는 적용하지 않는다."
metadata:
  product: vox.ai
  layer: mcp
  status: stable
---

# agents-platform

제품 호출에는 [공통 실행 계약](../../references/execution-contract.md)을 적용한다. 내장/외부의 질문·음성·파일 차이는 [호스트 연결](../../references/host-adapters.md)을 따른다. 도구는 연결된 서버가 제공하는 실제 이름과 스키마를 확인한 뒤 사용한다.

## 제품 모듈 선택
이 스킬은 Agents 제품의 연결과 도구 사용을 안내한다. 사용자의 요청이 음성 agent 구축·시험·통신 운영이면 이 모듈을 선택한다. desk의 상담원 수신·이어받기·상담원 발신 요청을 비슷한 이름의 Agents 도구에 넘기지 않는다. 현재 연결에서 지원 여부를 확인하고 미지원 범위를 알려준다. 현재 번들의 구현 기준은 [워크플로 capability 표](../../references/workflow-capabilities.json)다.

## 연결과 발견
호스트에서 제공하는 인증 절차를 사용한다. 키나 토큰을 프롬프트/파일에 요구하지 않는다. 연결은 한 번에 한 조직에서 동작한다. 조직이 여러 개인 계정이면 `list_organizations`로 접근 가능한 조직과 현재 조직을 읽고, 사용자가 바꾸기를 원할 때만 `set_organization`을 호출한다. 이 전환은 이 MCP 연결 전체의 대상 조직을 바꾸므로 호출 전에 대상 조직 이름을 사용자에게 보여 확인받고, 전환 뒤 `get_organization`으로 현재 조직을 다시 읽는다. 이전 조직에서 읽은 agent_id·number_id 등 ID와 `expected_*_revision`은 새 조직에서 재사용하지 않고 다시 조회한다. 내장 Copilot은 조직을 바꿀 수 없으므로 제품 화면에서 조직을 바꾼 새 대화로 이어가도록 안내한다.

호스트가 실제 제공한 MCP 도구 이름과 스키마를 먼저 확인한다. 이름 검색 후 정확한 ID를 확보한다. `list_models`, `list_schemas`, `get_schema`는 제품 설정 탐색용이며 호스트의 MCP 도구 발견 기능과 혼동하지 않는다. 여러 서버가 있으면 연결 식별자와 제품 모듈을 함께 확인한다. Manual은 Single에 귀속되므로 `list_agents`로 대상을 정하고 `list_manuals` 또는 `get_manual`로 같은 `agent_id` 범위의 현재 Manual을 읽는다.

## 도구 선택
첫 배포 범위의 도구는 대화만으로 첫 출시 여정(구축 → 버전 저장·게시 → 보유 번호 연결 → 발신 → 결과 확인)을 끝낼 수 있게 한다. 실제 사용 가능 여부는 연결된 서버의 목록과 schema로 확인한다.
- 조직·탐색: `get_organization`, `list_organizations`/`set_organization`(조직 전환, 위 ‘연결과 발견’ 참고), `list_models`, `list_schemas`, `get_schema`. 조직 관리는 `update_organization`(요청한 설정만)과 `list_organization_members`(개인정보라 필요한 범위만)다.
- 구축: 기본은 Single + Manual이다. `list_agent_templates` → `get_agent_template` → `instantiate_agent_template`로 시작하거나 `save_agent`(mode=create)로 Single을 만들고, 업무 절차는 `save_manual`(mode=create)로 고객 의도별 Manual을 붙인다. 새 agent의 모델 선택은 [모델 선택 규칙](../build-first-voice-agent/SKILL.md#모델-고르기)을 따르며, 템플릿 생성 뒤에도 선택 모델을 `save_agent(mode=update)`로 적용한다. 새 agent는 첫 `save_agent` 전에 유형과 이유를 한 줄로 알린다([유형 선택](../voice-agent-design/SKILL.md)). `list_manuals`/`get_manual`/`save_manual`, 도구 `list_tools`/`get_tool`/`save_tool`, 지식 `list_knowledges`/`create_knowledge`/`import_knowledge_documents`(텍스트·URL만)/`list_knowledge_documents`/`delete_knowledge_document`. Manual 저장에는 `agent_id`와 현재 `head_revision`에 해당하는 `expected_head_revision`을 포함하고 Agent 수정에도 현재 `head_revision`을 사용한다. Manual이 쓰는 내장 도구는 본문에서 `@tool:이름`, API 도구는 `@tool:<tool_id>`, 다른 Manual은 저장된 대상의 `@manual:<manual_id>`로 참조해야 동작한다([manual-authoring](../manual-authoring/SKILL.md)).
- Flow agent: [유형 선택](../voice-agent-design/SKILL.md)에서 Flow로 정해진 경우에만 만든다(기본은 Single + Manual). `type=flow`이고 그래프는 `payload.flow`의 `{nodes, edges}`다. 새 agent 모델 선택은 [모델 선택 규칙](../build-first-voice-agent/SKILL.md#모델-고르기)을 따른다. 노드 `data` 키는 snake_case(`static_sentence`, `prompt_type`, `is_allow_interruption` 등)이고 허용 노드는 `begin`, `conversation`, `tool`, `condition`, `extraction`, `api`, `sendSms`, `transferCall`, `transferAgent`, `endCall`, `note`다. 분기는 edge의 `condition`(`ai`·`logic`·`fallback`)이며, `begin`의 나가는 edge는 `fallback`만 허용하므로 영업시간 같은 분기는 `begin` → `condition` 노드 → 분기로 만든다. DTMF 키 입력은 메시지로 들어오므로 키마다 AI 조건 edge를 달지 않고, 분류 `extraction` 노드가 메뉴 코드를 뽑고 `condition` 노드의 logic 조건이 분기한다([Flow ARS 패턴](../../references/flow-ars-pattern.md)). `conversation` 노드에는 `fallback`을 달 수 없고(저장 거부), 무입력(침묵)은 전환 조건이 되지 않는다. 자기 자신으로 돌아오는 self-loop는 허용된다. 생성·수정 모두 `validate_flow`를 `level="all"`로 먼저 호출해 errors를 고친 뒤 `save_agent`로 저장하고, 수정은 `get_agent`로 현재 그래프를 읽어 전체 그래프를 편집해 보내며 방금 읽은 flow revision을 `expected_flow_revision`으로, `head_revision`을 `expected_head_revision`으로 함께 보낸다(수정 검증에는 `agent_id`를 함께 보낸다). 저장 뒤 `get_agent`로 재조회한다. `api` 노드의 헤더 값·인증 정보는 조회 때 `********`로 마스킹되어 오고 마스킹 값은 저장에서 거부되므로 되돌려 보내지 않는다. `api` 노드가 있는 flow를 수정할 때는 사용자에게 실제 비밀값을 다시 받아 넣는다. 입력 형식은 실제 schema와 `get_schema`로 확인하고 검증 오류를 추측으로 우회하지 않는다. 원문 질문은 답을 받아야 할 때 dynamic conversation 노드의 `first_message`에 글자 그대로 두고, `prompt`에는 판정·재안내 규칙만 쓴다(`prompt` 안의 원문은 그대로 읽힌다는 보장이 없다). 고지·완료 문구는 `static_sentence`에 둔다. 설계 기준은 [음성 업무 설계](../voice-agent-design/SKILL.md)의 ‘Flow와 ARS 흐름’을 따른다.
- 음성 모델: `create_voice_model`로 사용자가 동의한 화자의 음성을 등록한다. 자세한 조건은 [음성 조정](../tune-voice-behavior/SKILL.md)의 ‘음성 모델 만들기’를 따른다.
- 버전·게시: `list_agent_versions`, `create_agent_version`(현재 설정을 버전으로 저장) → `publish_agent_version`(production 지정). → [첫 출시 연결](../build-first-voice-agent/SKILL.md)
- 번호: `list_numbers`, `get_number`, `set_number_agents`, `update_number`. 이미 가진 번호만 다루며 번호 획득·해지는 웹에서만 한다. → [번호 연결](../connect-phone-service/SKILL.md)
- 발신·캠페인: `place_call`, 시트 `list_sheets`/`get_sheet`/`create_sheet`, `launch_campaign`, `list_campaigns`/`get_campaign`, `pause_campaign`/`resume_campaign`/`cancel_campaign`. → [발신 운영](../operate-outbound-and-followup/SKILL.md)
- 결과 확인: `list_calls`, `get_call`(원문은 명시 요청 시만), 고객 `list_customers`/`get_customer`/`find_customer`/`save_customer`/`resolve_customer`와 속성 정의 3개. → [통화 근거](../inspect-call-evidence/SKILL.md)
- 이 범위 밖(음성 시험 시작, 독립 SMS 발송, 채팅·위젯, 번호 구매, 파일 업로드)은 도구가 없다. 통화 중 문자와 전환은 별도 MCP 도구가 아니라 agent 안의 내장 도구(`send_sms`, `transfer_call`)나 Flow 노드(`sendSms`, `transferCall`)로 설정한다. 음성 시험은 고객이 제품 UI에서 직접 하고 결과를 보고한다. 호스트가 추가 tool을 실제로 노출하면 그 입력 schema를 확인한 뒤 사용한다. 예제와 schema 검증은 [합성 고객 여정](../../references/workflow-examples.md)을 따른다.

## Flow 저장 전 점검
- API 노드 저장 전에 응답을 실제로 한 번 받아 `response_variables` 경로를 그 형태에 맞춘다. [구현 도구 스냅샷](../../references/implemented-tools.snapshot.json)에는 API 시험 호출 도구가 없으므로, 현재 연결에도 없거나 응답을 받을 수 없으면 명세의 응답 예시를 그대로 따르고 실측하지 않았으며 추측한 부분이 있으면 사용자에게 알린다.
- 접수·기록 업무는 확인 응답 뒤 저장 API 노드로 실제로 이어지는 간선을 확인한다. 대화 노드의 `loop_condition`은 참일 때 다음 단계로 나갈 수 있는 조건이므로 “아직 선택하지 않았다” 같은 반복 지시 대신 “고객이 접수 방식을 선택했다” 또는 “다섯 항목을 수집하고 요약에 동의했다”처럼 완료 조건으로 쓴다.
- loop_condition에는 성공 출구와 포기 출구(재안내 상한 도달)를 함께 쓴다. 예: '등록값이 일치했거나, 재안내 1회 뒤에도 일치하지 않았다'.
- `outcome` 값과 문항별 결과 필드는 명세 값 그대로 쓴다.
- 실패 뒤 대안이 필요한 연결은 warm 연결에 실패 간선을 붙인다.
- 지원하지 않는 재조회나 동작은 완성됐다고 말하지 않는다. 자세한 기준은 [Flow 업무 계약](../../references/flow-business-contract.md)을 따른다.


실제 전화·대량 발신·운영 반영·번호 연결 변경·삭제·인증 변경은 [실행 계약](../../references/execution-contract.md)의 ‘실제 영향이 있는 도구’(사용자 확인, `execution_key`, 결과 불명, 비밀값 마스킹)를 따른다. agent 저장이나 게시가 실고객 발신을 허가하지 않는다.

## 응답과 복귀
저장/접수/최종 완료/부분 실패/불명을 분리한다. 저장 성공 뒤 조회가 실패했다면 받은 `agent_id`와 `manual_id`부터 이어간다. `409` conflict는 현재 상태를 다시 읽고 사용자의 변경 의도를 다시 적용할 때만 처리하며 무조건 재시도하지 않는다. 쓰기 응답이 불명이면 새 생성이나 같은 쓰기를 반복하지 말고 [resume-agent-work](../resume-agent-work/SKILL.md)로 지원되는 조회를 이어간다. OAuth 만료를 조직 전체 키나 직접 REST로 우회하지 않는다.

스킬 부재를 제품 접근 차단 사유로 만들지 않는다. 도구 설명·스키마만으로도 지원 업무를 수행할 수 있어야 한다. 세부 업무 판단은 관련 Architect 스킬, 개념·작성 품질은 general을 필요할 때 읽는다.
