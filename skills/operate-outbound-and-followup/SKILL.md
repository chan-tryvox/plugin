---
name: operate-outbound-and-followup
description: "vox.ai의 단건 발신과 시트 기반 캠페인 실행·중지·재개·취소를 사용자의 명시 업무 범위에서 수행하고 실제 결과를 확인할 때 사용한다."
metadata:
  product: vox.ai
  layer: architect
  status: stable
---

# operate-outbound-and-followup

제품 호출에는 [공통 실행 계약](../../references/execution-contract.md)을 적용한다. 내장/외부의 질문·음성·파일 차이는 [호스트 연결](../../references/host-adapters.md)을 따른다. 도구는 연결된 서버가 제공하는 실제 이름과 스키마를 확인한 뒤 사용한다. 현재 capability는 [워크플로 capability 표](../../references/workflow-capabilities.json)에서 확인한다.

## 실행 전 상태
실행 의도, agent/버전, 발신 번호(`list_numbers`로 보유 확인), 대상, 사전 변수, 현재 권한·한도를 확인한다. ‘에이전트 만들어줘’나 ‘발신 계획을 짜줘’는 실제 발신 요청이 아니다. 실제 발신·캠페인 실행·재개 전에는 [실행 계약](../../references/execution-contract.md)대로 대화에서 짧게 요약해 사용자의 진행 확인을 받는다. 요약에는 대상(번호 끝 4자리·고객 수), 발신 번호, agent와 버전, 사전 변수 유무, 한 번의 실제 발신이라는 점을 넣는다. 이미 승인받은 같은 요약의 재전송·실패 재시도는 다시 묻지 않는다.

## 동작별 계약
| 업무 | 실행/조회 | 완료 판단 |
| --- | --- | --- |
| 단건 발신 | `place_call`(`routing`, `execution_key`) → `list_calls`/`get_call` | 접수·연결·종료·업무 결과 구분 |
| 대상 시트 | `create_sheet`(행: `to_number`, 문자열 `dynamic_variables`) → `get_sheet`; 기존은 `list_sheets` | 시트 생성은 발신이 아니다 |
| 캠페인 | `launch_campaign`(`execution_key`) → `get_campaign`; 중지·재개·취소 `pause_campaign`/`resume_campaign`/`cancel_campaign` | 대상별 시도·결과; 중지·취소가 이미 연결된 통화를 끊지 않음 |

`execution_key`(8~128자, UUID 권장)는 `place_call`·`launch_campaign`·`resume_campaign`에 필수이고 `pause_campaign`·`cancel_campaign`에는 선택이다. 실행하려는 의도마다 새 키를 만든다. 같은 키는 같은 실행(같은 인자)의 재전송에만 쓰고, 같은 키의 재호출은 새로 실행하지 않고 앞선 결과를 돌려준다. 기록된 실패도 그대로 돌려주므로 실패(일시 오류 포함)를 다시 시도하려면 새 키를 만든다. `EXECUTION_KEY_REUSED`는 같은 키를 다른 인자에 쓴 것이므로 새 키로 요청 내용을 사용자에게 다시 확인한 뒤 호출한다.

**`EXECUTION_RESULT_UNKNOWN`·`EXECUTION_IN_PROGRESS`이면 다시 실행하지 않는다.** 새 키도 만들지 않는다. 단건은 `list_calls`(`call_to`·`start_at_after`)와 `get_call`, 캠페인은 `get_campaign`/`list_campaigns`로 접수 여부를 읽어 사용자에게 보고하고 추가 실행은 사용자의 새 결정을 받는다. [복귀](../resume-agent-work/SKILL.md)로 이어간다.

설정 저장과 실행 도구를 혼동하지 않는다. 정확한 ID와 반환된 결과 참조를 보존한다. 지원되지 않는 예약 발신·상시 감시를 추가하지 않는다. 통화 전환·SMS를 단독으로 실행하는 MCP 도구는 이 범위에 없다(agent 안의 내장 도구와 Flow 노드는 구축 단계에서 설정한다). 진행 중인 통화에 외부 사실을 알리는 일은 [통화 중 맥락 넣기](../../references/call-context.md)의 REST API 안내를 따른다. 호스트가 실제로 제공하지 않으면 호출하거나 성공했다고 말하지 않는다. 새 대화에서 이어갈 때는 현재 대화나 사용자 handoff를 사용한다. 합성 예시는 [합성 고객 여정](../../references/workflow-examples.md)을 따른다.

## 결과와 후속
모수와 성공/실패/미응답/불명/처리 중을 구분한다. 접수는 연결·업무 성공이 아니다. 캠페인은 `get_campaign`으로 진행을 읽고, 통화별 결과는 `list_calls`(`campaign_id` 필터)와 `get_call`로 확인한다. 고객 식별은 `find_customer`(읽기 전용)를 쓰고 `resolve_customer`는 없으면 고객을 만든다는 점을 알린 뒤 쓴다. 실패 대상만 재실행할 때도 실제 실행 여부를 먼저 확인하고 사용자 의도 범위 안에서 새 시트·새 키로 진행한다. 상세 통화는 필요한 접근 범위로만 읽는다. 내용 분석은 [통화 성과](../review-call-performance/SKILL.md)로 이어간다.

‘A/B 비교’ 요청은 같은 대상에게 두 버전을 각각 시험할지, 대상자를 분할할지에 따라 실행이 다르다. 실제 의도가 불명확하면 [업무 판단 기준](../../references/workflow-guidance.md)에 따라 질문한다. 시험 설계 합의를 실고객에 대한 추가 발신 위임으로 확대하지 않는다.
