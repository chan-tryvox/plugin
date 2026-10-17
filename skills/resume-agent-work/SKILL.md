---
name: resume-agent-work
description: "vox.ai 구축·운영 작업이 연결 단절·권한 만료·부분 성공·불명 응답으로 끊겼을 때 완료된 단계를 보존하고 이어간다."
metadata:
  product: vox.ai
  layer: architect
  status: stable
---

# resume-agent-work

제품 호출에는 [공통 실행 계약](../../references/execution-contract.md)을 적용한다. 내장/외부의 질문·음성·파일 차이는 [호스트 연결](../../references/host-adapters.md)을 따른다. 도구는 연결된 서버가 제공하는 실제 이름과 스키마를 확인한 뒤 사용한다. 현재 저장·재개 capability는 [워크플로 capability 표](../../references/workflow-capabilities.json)와 [합성 고객 여정](../../references/workflow-examples.md)에 있다.

## 복귀 자료
현재 연결 조직·주체를 확인하고 현재 호스트의 접근 가능한 대화나 사용자가 제공한 handoff로 이어간다.

## 상태별 다음 행동
| 상태 | 행동 |
| --- | --- |
| Manual 저장 성공, 후속 단계 실패 | 받은 `agent_id`와 `manual_id`로 Manual을 조회하고 그 Single에서 이어간다 |
| 저장 성공, 재조회 실패 | 같은 `agent_id`·`manual_id`를 재조회; 새 리소스 생성 금지 |
| Manual create 응답 불명 | 같은 `agent_id`에서 `list_manuals`로 후보를 찾고 `get_manual`로 ID·전체 본문·revision을 비교한다; 일치 후보는 현재 대상으로 사용할 수 있지만 exact receipt 없이는 원 create 성공으로 단정하지 않는다 |
| 발신·캠페인 응답 불명(`EXECUTION_RESULT_UNKNOWN`·`EXECUTION_IN_PROGRESS`) | 재실행·새 `execution_key` 금지; `list_calls`(`call_to`·`start_at_after`)/`get_call`, 캠페인은 `get_campaign`/`list_campaigns`로 접수 여부 확인 후 보고 |
| 게시·번호 연결·지식 삭제 등 제품 작업 응답 불명 | `get_agent`/`list_agent_versions`, `get_number`, `list_knowledge_documents`로 실제 상태를 읽고 재실행하지 않음; 조회 도구가 없으면 사용자에게 상태 확인을 요청 |
| 인증 만료/철회 | 호스트의 재연결 경로로 권한 복구 후 실제 상태 재조회 |
| 다른 조직으로 바뀜(`set_organization` 전환 포함) | 이전 조직 자격 증명/리소스·ID·revision을 재사용하지 않고 `get_organization`으로 현재 조직을 확인한 뒤 필요한 리소스를 다시 조회; 의도하지 않은 전환이면 사용자에게 알리고 대상 조직을 확인받는다 |

제품의 unknown 결과를 임의로 재실행하지 않는다. 새 operation ID, POST 재시도, 직접 API 우회를 하지 않는다.

## 결과
지금까지 확인된 완료, 미확인 동작, 현재 막힌 이유, 가능한 다음 조회/사용자 행동을 구분한다. 콜이 이미 접수됐으면 연결을 끊거나 대화를 취소해도 전화가 자동 취소된다고 말하지 않는다. 파일·모델 요약은 제품 상태의 정본이 아니다.

복귀 시 [업무 판단 기준](../../references/workflow-guidance.md)의 작은 업무 요약과 사용자가 제공한 handoff에서 목표·사용자 결정·완료 참조·다음 행동을 읽는다. 새 Thread나 호스트에서 그 요약에 접근할 수 없다면 사용자에게 최신 ID와 결정 요약을 요청한다. 모델 요약만으로 실행 권한이나 제품 상태를 확정하지 않는다. delivery.reference는 원문 읽기를, delivery.unavailable은 알려진 결과 조회를 이어간다. 새 환경이 생겨도 이미 시도한 제품 쓰기를 다시 실행하지 않는다. handoff 예는 [합성 고객 여정](../../references/workflow-examples.md)에 있다.
