---
name: try-and-improve-voice-agent
description: "vox.ai 에이전트를 직접 말해 보고 피드백·실패 통화를 근거로 수정하고 재시험할 때 사용한다."
metadata:
  product: vox.ai
  layer: architect
  status: stable
---

# try-and-improve-voice-agent

제품 호출에는 [공통 실행 계약](../../references/execution-contract.md)을 적용한다. 내장/외부의 질문·음성·파일 차이는 [호스트 연결](../../references/host-adapters.md)을 따른다. 도구는 연결된 서버가 제공하는 실제 이름과 스키마를 확인한 뒤 사용한다. call 조회(`list_calls`/`get_call`) capability는 [워크플로 capability 표](../../references/workflow-capabilities.json)와 실시간 도구 목록에서 확인한다.

## 시험 또는 증거부터
아직 통화가 없으면 [시험 준비](../prepare-voice-test/SKILL.md)로 진입한다(음성 시험은 고객이 직접 한다). 실패 통화나 callId가 있으면 `get_call`(필요하면 `list_calls`로 찾기)로 [통화 근거](../inspect-call-evidence/SKILL.md)를 읽는다. 조회되지 않으면 고객이 직접 시험한 보고나 제공한 원문만 사용하고 그 출처를 표시한다. 기대 결과와 실제 결과의 차이를 한 가지 이상 구체적으로 적는다.

## 필요한 수정만 조합
- 말/질문/정정/마무리: [Manual 편집](../edit-manual-safely/SKILL.md).
- 발화 실패를 실제 prompt/Manual 규칙과 연결하고 최소 수정: [음성 프롬프트 실패 진단과 최소 수정](../../references/voice-prompt-failure-guidance.md).
- 도구 미호출·오류·불명: [도구 진단](../troubleshoot-agent-tool/SKILL.md).
- 추출·저장: [결과 설정](../configure-call-results/SKILL.md).
- 끼어들기·지연·음성: [음성 조정](../tune-voice-behavior/SKILL.md).
- 공유 변경: [영향 확인](../review-shared-impact/SKILL.md).

한 번의 틀린 응답을 전체 프롬프트 재작성으로 확대하지 않는다. 과거 버전 문제를 현재 설정에 이미 해결됐는지 확인하지 않고 다시 고치지 않는다. 인프라/외부 API 문제를 Manual로 덮지 않는다.

## 재시험과 완료
수정 저장·재조회 뒤 고객이 같은 상황과 관련 정정/실패 상황을 직접 시험하도록 기대 결과를 전달한다. `get_call`로 조회한 통화만 발화·도구·추출 결과를 그 증거와 대조한다. 수정이 운영에 반영되어야 하면 `create_agent_version` 뒤 사용자 확인을 받아 `publish_agent_version`을 쓴다. 고객이 보고한 결과는 `customer_reported`로 구분한다. 아직 사용자가 시험하지 않았다면 ‘수정 저장 완료·재시험 필요’다. 텍스트 검토나 합성 시나리오 작성은 실제 음성 통과가 아니다.

원인과 변경, 확인한 근거, 남은 시험을 전달한다. 더 큰 운영 추세가 필요하면 [기간 분석](../review-call-performance/SKILL.md)을 추가한다.

## 피드백을 다음 작업으로 바꾸기

[업무 판단 기준](../../references/workflow-guidance.md)의 피드백 표로 원고·연결·결과 저장·시험 조건 중 변경할 범위를 좁힌다. “대시보드 우선” 결정은 전달 위치와 결과 설정의 변경일 수 있으며 모든 외부 도구를 제거하라는 뜻은 아니다. [합성 고객 여정](../../references/workflow-examples.md)에 저장·고객 시험·재개 예가 있다. 현재 목표·사용자 결정·확인한 근거·변경한 대상·다음 시험이 이후 작업에 필요하면 save_work_record로 간결히 갱신한다. 고객 음성 결과는 feedback_reported 또는 evaluation_reported의 customer_voice_report로 기록해 계속 고객 보고로 표시한다. 전체 외부 transcript는 수집하지 않는다. routine record 저장은 get_work_context가 제공하는 자동 기록 enabled/revision/epoch로 게이트되며 OFF 또는 CAS 거부 시 자동 기록을 중단한다. 사용자가 현재 대화에서 저장하지 말라고 직접 요청하면 기록하지 않는다. OFF와 별개로 사용자가 명시적으로 요청한 기존 기록 조회·정정·삭제는 지원한다. text_contract 평가를 고객 음성 시험으로 표현하지 않는다. 이미 저장한 제품 리소스는 재사용한다. 마지막 단계로 사용자가 이번 요청에서 앞으로도 지킬 규칙·결정을 말했다면(예: "앞으로", "항상", "다음에도") 저장 후 `save_work_record`의 `decision_set`으로 짧게 기록한다(자동 기록이 OFF이거나 사용자가 기록하지 말라고 했으면 제외).
