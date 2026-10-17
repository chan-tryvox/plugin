---
name: prepare-voice-test
description: "고객이 vox.ai 에이전트를 직접 음성 시험하도록 준비하고 기대 결과와 고객 보고 또는 조회 가능한 통화 근거를 구분할 때 사용한다. 고객용 자동 시뮬레이션 플랫폼은 생성하지 않는다."
metadata:
  product: vox.ai
  layer: architect
  status: stable
---

# prepare-voice-test

제품 호출에는 [공통 실행 계약](../../references/execution-contract.md)을 적용한다. 내장/외부의 질문·음성·파일 차이는 [호스트 연결](../../references/host-adapters.md)을 따른다. 도구는 연결된 서버가 제공하는 실제 이름과 스키마를 확인한 뒤 사용한다.

## 준비
agent·대상 버전·해당 Single의 agent-scoped Manual을 확인한다. `get_agent`·`list_agent_versions`·`list_manuals`로 시험할 버전과 본문을 읽고, 읽지 못한 정보는 사용자가 준 것임을 표시한다. 자료가 아웃바운드 업무면 합성 사전 정보를 사용해 도입/거절을 시험할 수 있는지 현재 진입 경로를 확인한다. 실고객 데이터나 실제 발신을 기본값으로 쓰지 않는다.

[시험 사례](../../references/voice-test-cases.md)에서 목표에 맞는 정상/변경/오류 상황을 고른다. 시험 대화와 기대 저장값을 짝짓고 브라우저 음성으로 확인할 것과 실제 전화로 확인할 것을 구분한다.

텍스트 채팅 시험에서는 종료 도구 말고는 내장 도구(주소 검색·연결·문자·DTMF)가 실행되지 않는다. 내장 도구 동작은 음성 통화 시험으로 확인하도록 고객에게 안내한다.

## 고객 직접 시험과 결과
음성 시험을 시작하는 도구는 없다. 고객이 제품 UI에서 대상 agent와 버전을 확인해 직접 음성 시험을 하고, 우리는 시험할 대상·발화·기대 결과를 안내한 뒤 고객의 보고를 기다린다. 실제 전화로 확인하려면 보유 번호 연결([번호 연결](../connect-phone-service/SKILL.md))이나 사용자가 명시·확인한 단건 발신([발신 운영](../operate-outbound-and-followup/SKILL.md))을 쓴다. 임의 URL이나 토큰 포함 링크를 만들지 않는다.

고객이 알려준 결과는 customer_reported로 표시한다. 고객이 callId를 주거나 `list_calls`(`agent_id`·`start_at_after`)로 해당 통화를 찾으면 `get_call`로 독립 확인한다. 상태·당시 버전·추출 결과를 응답에서 읽은 경우에만 독립 call evidence로 기록하고, 고객의 말은 계속 customer_reported다. 원문(`include_transcript`)은 필요하고 사용자가 요청할 때만 읽는다. ID가 없거나 조회되지 않으면 추측하지 않는다.

## 완료 표시
‘시험 상황 작성’, ‘음성 시험 준비’, ‘실제 대화 수행’, ‘결과 확인’은 다른 단계다. 하나가 완료됐다고 뒤 단계를 완료로 표시하지 않는다. 수정이 필요하면 증거와 함께 해당 전문 스킬로 연결한다.

세부 실행 순환은 [합성 고객 여정](../../references/workflow-examples.md)을 따른다. 제품 설정 readback, 고객의 음성 수행, 고객 보고, `get_call`로 조회한 call 증거를 서로 다른 완료 단계로 전달한다.
