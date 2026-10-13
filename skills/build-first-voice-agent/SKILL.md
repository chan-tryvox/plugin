---
name: build-first-voice-agent
description: "URL·파일·설명으로 vox.ai의 첫 Single 음성 에이전트를 만들고 Manual·결과 저장·직접 시험까지 연결할 때 사용한다."
metadata:
  product: vox.ai
  layer: architect
  status: stable
---

# build-first-voice-agent

제품 호출에는 [공통 실행 계약](../../references/execution-contract.md)을 적용한다. 내장/외부의 질문·음성·파일 차이는 [호스트 연결](../../references/host-adapters.md)을 따른다. 도구는 연결된 서버가 제공하는 실제 이름과 스키마를 확인한 뒤 사용한다. 현재 구현 capability는 [구현 도구 스냅샷](../../references/implemented-tools.snapshot.json)과 [워크플로 capability 표](../../references/workflow-capabilities.json)에 있다.

## 먼저 읽을 상태와 판단
기존 agent를 고치는 요청인지 새 구축인지 구분한다. 기존 대상이 있으면 [현재 상태](../explore-agent-context/SKILL.md)를 읽는다. 자료를 검토해 prompt·Manual·지식 중 둘 위치는 [근거 정리](../knowledge-grounding/SKILL.md)에서 결정하고, 업무 유형은 [음성 업무 설계](../voice-agent-design/SKILL.md)로 판단한다. 핵심 업무·방향·실제 완료 결과를 짧게 제안하고 중요한 미확정 판단만 묻는다. 새 구축이면 [유형 선택](../voice-agent-design/SKILL.md)을 적용하고, 유형과 이유를 한 줄로 알린다. 첫 `save_agent` 호출 직전 응답에 `유형: <Single + Manual n개 | Flow>. 이유: <한 문장>`을 반드시 쓴다(무인 실행이어도 쓴다). 사용자가 Flow를 지정했더라도 대화로 받는 접수·상담이 중심이면, 첫 저장 전에 'Single + Manual이 더 맞는 이유'를 한 번만 말하고 요청대로 진행한다. 기본은 Single + Manual이며 Flow로 정해지면 이 스킬 대신 [Flow 절차](../agents-platform/SKILL.md)를 따른다.

## 구축

프롬프트나 Manual의 실제 음성 발화 문구를 작성할 때 [음성 프롬프트 기본 지침](../../references/voice-prompt-guidance.md)을 적용한다.
### 모델 고르기
새 agent 모델을 정하거나 사용자가 요청한 기존 agent 모델을 바꿀 때마다 `list_models(kind=llm)`을 호출한다. 사용자가 모델 ID·모델명·계열·공급사를 직접 지정하지 않았다면 “좋은 모델로”, “최신 모델로”, “성능 좋게”, “빠른 모델”, “비용이 낮은 모델”, “품질이 좋은 모델” 같은 속도·비용·품질·최신 선호는 지정으로 보지 않는다. 호스트 자신의 모델 계열이라는 이유로 고르지 않으며, 기존 agent 모델은 변경 요청이 없으면 보존한다.

- 결과에 `featured` 필드 자체가 없는 구 API에서는 새 agent의 `data.llm`을 생략해 서버 기본값을 쓴다. 사용자가 모델·계열·공급사를 지정했으면 그 선택을 이 구 API로 명시 저장할 수 없다고 알린다. 기존 agent 모델 변경도 실행하지 않고 현재 값을 보존한다. 모델이 들어 있는 템플릿은 선택하지 말고 `save_agent(mode=create)`에서 `data.llm`을 생략한다. `featured` 정보가 있는데 활성 featured 항목이 하나도 없다면 지정 없는 요청은 추천 모델을 찾지 못했다고 알리고 임의 선택하지 않는다.
- 추천 기준은 `featured=true`, `deprecated=false`인 모델이며, `display_order`가 가장 작은 항목이 이번 출시의 vox 추천 1순위다. 지정이 없으면 전역 추천 1순위의 `model` 값을 `data.llm.model`에 그대로 넣는다. 이는 표시 이름과 다른 routing group 키일 수 있다.
- featured 추천 범위 밖의 모델은 사용자가 모델 ID·모델명·계열·공급사를 직접 지정한 경우에만 선택한다. 정확한 모델 ID는 조회 결과의 `model`과, 모델명은 `display_name`과 정확히 일치시킨다. `deprecated=true` 항목은 정확한 모델 ID를 직접 지정한 경우에만 허용한다. 사용자가 계열이나 공급사를 지정하면 해당 범위에서 deprecated가 아닌 featured 항목 중 `display_order`가 가장 작은 것을 고른다. 범위 안에 featured 항목이 없으면 deprecated가 아닌 항목 중 순서가 가장 앞선 것을 선택한다. 저장 시 선택한 모델이 `featured=true`이고 `deprecated=false`인 추천 항목이 아니면 반드시 `이 모델은 vox 추천 모델이 아닙니다(추천: <featured 1순위 display_name>)` 한 줄을 알린다. 활성 featured 추천이 없으면 추천 이름을 만들지 말고 같은 문구의 추천 값을 `현재 featured 추천 모델 없음`으로 표시한다. 해당 ID·계열·공급사의 사용 가능한 항목이 조회 결과에 없으면 저장하지 않는다. 모델 ID를 추측하거나 다른 필드에서 만들어 내지 않는다.
- 선택을 한 줄로 알린다. 예: `모델: <display_name> (vox 추천 1순위)`, `모델: <display_name> (요청한 계열의 vox 추천 모델)`, `모델: <display_name> (사용자 지정)`, 또는 `모델: <display_name> (요청한 계열, vox 추천 모델 아님)`. 추천이 아닌 모델은 위의 필수 알림도 저장 전에 별도로 한 줄 표시한다. 사용자가 deprecated ID를 정확히 요청했다면 그 사실도 표시한다. 구 API fallback은 `모델: vox 추천 기본값 (구 API 서버 기본값)`이라고 알린다.
- `save_agent(mode=create)`에서는 선택한 `model`을 `data.llm.model`에 넣는다. 템플릿 생성은 `instantiate_agent_template` 성공 뒤 `get_agent`로 `head_revision`과 현재 `data.llm`을 읽고, `data.llm`의 기존 지원 필드는 보존하면서 `model`만 선택값으로 바꿔 `save_agent(mode=update)`에 보낸다. 방금 읽은 revision을 `expected_head_revision`으로 쓰고 다른 설정 묶음은 보내지 않는다. `llm` 묶음은 통째로 교체되므로 temperature 등 기존 값을 빠뜨리지 않는다.

### 구축 순서
1. Manual 목록(이름·트리거·제외절)과 프롬프트·Manual·지식 분담을 정한다. 아래 '프롬프트와 Manual 골격'과 '운영 수준 점검'은 반드시 지키고, 더 자세한 규칙과 예시는 [Manual 작성](../manual-authoring/SKILL.md)에 있다. 외부 동작이 필수라면 [도구 연결](../connect-agent-tools/SKILL.md)의 의존성을 먼저 확인한다.
2. 시작점을 고른다. 새 agent는 위 [모델 고르기](#모델-고르기) 규칙을 템플릿과 직접 생성 모두에 적용한다. 맞는 업무 템플릿이 있으면 `list_agent_templates` → `get_agent_template`로 내용을 확인하고 `instantiate_agent_template`(payload.name)으로 Single을 만든다. 템플릿은 자동 게시되지 않으며 부분 실패 결과를 그대로 읽는다. 템플릿의 기본 프롬프트와 Manual은 업종·방향·완료 문구가 새 업무와 충돌할 수 있으므로 그대로 두지 않고 고쳐 쓴다. 없으면 `save_agent(mode=create)`로 Single을 만들고 선택 모델은 `data.llm.model`, 다시 쓴 프롬프트는 `data.prompt.prompt`에 넣는다. 반환된 `agent_id`를 보존한다.
3. `get_agent` 또는 `list_manuals`로 현재 `head_revision`을 읽은 뒤 Manual마다 `save_manual`로 본문을 저장한다(생성이면 `mode=create`와 같은 `agent_id`, `payload.expected_head_revision`, `name`, `trigger`, `content`; 템플릿이 만든 Manual은 수정). 이 호출이 Manual을 에이전트에 연결하며, Manual을 저장할 때마다 revision이 바뀌므로 다음 Manual 전에 다시 읽는다. 다른 Manual이 `@manual:<manual_id>`로 가리킬 대상은 UUID가 필요하므로 먼저 저장한다. 폐기된 `manualIds`를 agent payload에 만들지 않는다. Manual이 쓰는 내장 도구는 본문에서 `@tool:이름`, API 도구는 `list_tools`가 돌려준 `@tool:<tool_id>`로 참조해야 실행된다.

4. `list_manuals`로 Manual 수와 진단 건수를, `get_manual(agent_id, manual_id)`와 `get_agent(agent_id)`로 본문·참조·현재 revision을 재조회한다. 넓은 참고 자료가 필요하거나 사용자가 요청한 경우에만 [지식](../knowledge-grounding/SKILL.md)(텍스트·URL)을 연결하고, 외부 연동은 [도구](../connect-agent-tools/SKILL.md), 내부 추출·저장은 [결과 설정](../configure-call-results/SKILL.md)으로 연결한다. 실제 입력·ID 흐름은 [완성된 합성 여정](../../references/workflow-examples.md)에 있다. 그다음 아래 '운영 수준 점검' 1~10을 다시 읽은 본문에 대고 확인하고, 어긋난 Manual은 고친다.
5. 저장한 상태를 `create_agent_version`으로 버전에 남긴다(반환된 버전 번호 보존, `list_agent_versions`로 확인). 운영에 쓰려면 사용자에게 어느 버전을 production으로 지정할지 요약해 확인받고 `publish_agent_version`을 호출한 뒤 `get_agent`(production)로 재조회한다. 게시는 번호·발신 경로에 바로 영향을 주며 모든 의존성의 불변 게시가 아니다.
6. 이미 가진 번호에 연결하려면 [번호 연결](../connect-phone-service/SKILL.md), 발신하려면 [발신 운영](../operate-outbound-and-followup/SKILL.md), 결과 확인은 [통화 근거](../inspect-call-evidence/SKILL.md)로 이어간다. 음성 시험은 [직접 음성 시험](../prepare-voice-test/SKILL.md)에서 고객이 직접 한다. 번호 획득은 웹에서만 하며 첫 체험의 필수 단계가 아니다.

### 업무 신호 → 내장 도구
| 업무 신호 | 내장 도구 |
|---|---|
| 사람 연결 | `transfer_call` |
| 다른 에이전트가 이어받기 | `transfer_agent` |
| 문자로 보내기 | `send_sms` |
| 고객 주소 받기(방문·배송·출동) | `search_address` |
| 끝인사 후 종료 | `end_call` |
| 아웃바운드에서 상대 ARS 번호 누르기 | `send_dtmf` |

- 내장 도구는 그 Manual의 `built_in_tools`에 넣고 같은 이름으로 `@tool:이름`을 참조한다. 에이전트 수준 도구는 Manual에서 참조할 수 없다. `skill`은 통화에서 무시되므로 Manual에 넣지 않는다.
- 고객 주소를 업무에 쓰면 `@tool:search_address`로 후보를 읽어 주고 고객이 확인한 뒤 확정한다. 가게 위치 안내처럼 고객 주소를 받지 않는 업무에는 붙이지 않는다. 결과값별 행동은 [주소 수집 패턴](../manual-authoring/SKILL.md#주소-수집-패턴)과 [내장 도구별 신호와 결과](../manual-authoring/SKILL.md#내장-도구별-신호와-결과)를 따른다.
- 고객사 주소 조회 API가 따로 있으면 어느 쪽을 쓸지 고객에게 확인하고, 정하지 않았으면 `search_address`를 기본으로 권한다.
- 텍스트 채팅 시험에서는 종료 도구 말고는 내장 도구(주소 검색·연결·문자·DTMF)가 실행되지 않는다. 내장 도구 동작은 음성 통화 시험으로 확인하도록 고객에게 안내한다.

## 프롬프트와 Manual 골격
프롬프트(보통 1,500~4,000자)는 모든 업무에 공통인 것만 담는다.
```
# 역할
# 말투와 발화: 한 턴에 질문 하나, 이미 들은 값은 다시 묻지 않음, 숫자 읽는 법, 큰따옴표 문장은 그대로 말함, 대괄호는 실제 값으로 바꿔 말함, 날짜를 되물을 때 시스템 날짜로 계산할 수 없으면 요일을 붙이지 않는다; 접수만 하고 확정은 나중에 하는 업무면 '아직 확정은 아니다'를 마무리에 한 번 말한다
# 공통 규칙: 모든 업무의 금지와 범위 밖 응대
# Manual 선택: 인사와 첫 용건 확인은 여기서 한다. 구체 업무가 확인되면 업무별 정보를 받거나 판단하기 전에 해당 Manual을 연다. ① 위급·안전 ② 진행 중인 Manual 계속 ③ 트리거가 하나만 맞으면 그 Manual ④ 없으면 용건을 한 번 묻기
# 마무리: 마지막 도움을 제안하고 답을 기다린 뒤 더 없으면 종료한다. 명시적 종료 사유에는 질문을 생략하고, 종료 도구 인사를 중복하지 않는다.
```
Manual 하나는 고객 의도 하나다(보통 3~10개).
```
## 규칙
- 범위: 하는 일 / 하지 않는 일(→ @manual:<id>)
- 완료 조건: 무엇이 확인돼야 완료라고 말하는가
## 진행 절차
### 시작
1. 고객이 이미 말한 값은 확인만 하고 다음 단계로 간다.
### <단계 이름>
1. 질문 하나.
   - <조건>: <행동>
   - 답이 없거나 불분명하면 한 번 다시 묻는다. 그래도 안 되면 <행동>.
   - 말하기를 거절하면 <행동>.
### <도구 결과 처리>
1. 언제: <조건>. 입력: <값의 출처>. @tool:<이름 또는 tool_id>를 부른다.
   - 성공: <행동> / 없음: <행동> / 실패·지연: 다시 부르지 않고 <대안>.
### 완료
1. 하위 Manual이면 원래 절차로 돌아간다. 전체 업무가 정상 완료되면 완료 조건을 확인해 결과를 알리고, 추가 도움 질문 → 답 대기 → 더 없으면 종료 도구 순서로 마친다. 새 요청이면 이어서 처리한다.
```

## 운영 수준 점검
Manual을 쓸 때 지키고, 저장한 뒤 `get_agent`·`get_manual`로 다시 읽어 하나씩 확인한다.
1. 질문 단계마다 "답이 없거나 불분명하면 한 번 다시 묻고, 그래도 안 되면 …" 가지를 둔다. 정보 제공 거절, 정정, 범위 밖 요청에도 할 행동을 적는다.
2. 도구 호출마다 언제·입력·결과별 행동(성공/없음/실패·지연)을 쓰고, "실패하면 다시 부르지 않고 …(메모·콜백·안내)"를 적는다. "완료·접수·전송했다"는 성공 결과를 받은 뒤에만 말한다. 전환·문자·등록처럼 부작용이 있는 도구는 고객이 동의한 뒤 부른다.
3. 순서가 중요한 곳은 게이트("…을 확인하기 전에는 …하지 않는다")로, 반복은 상한("최대 2회. 넘으면 …")으로 쓴다.
4. 상담원 연결·연락처 확인처럼 두 Manual 이상이 쓰는 단계는 공용 Manual 하나에 두고 `@manual:<id>`로 넘긴다. 공통 마무리 문장은 프롬프트 `# 마무리` 한 곳에만 두고 [공통 순서](../../references/voice-prompt-guidance.md#마무리)를 따른다. 종료 결과에 확인되지 않은 콜백 상태를 덧붙이지 않는다.
5. 프롬프트에 둔 규칙(금지·말투·정해진 거절 문구)을 Manual에 다시 쓰지 않는다. 같은 대상(Manual·종료 도구)은 늘 같은 이름으로 부른다.
6. 내용이 가까운 형제 Manual의 트리거에는 "…은 제외한다(○○ 담당)"를 붙인다. 실제 고객이 할 법한 대표 발화를 인접 트리거마다 대입해 담당을 정하고 겹침·공백을 조정한다. 평가용 발화는 저장된 Manual 내용에 넣지 않으며, 정해진 개수를 채우려 하지 않는다.
7. `{{변수}}`를 쓰면 `presetDynamicVariables`에 선언하고, 고객에게 말할 값은 [음성 발화 지침](../../references/voice-prompt-guidance.md#발화와-데이터-값)에 맞춰 처리한다.
8. 위급·안전 신호(통증·사고·누출 등)는 접수 Manual 끝에 묻어 두지 않고, 연결 도구를 가진 별도 진입 Manual로 둔다.
9. 새 Single 또는 공통 prompt 전체 작성이면 `# 말투와 발화`에 음성 기본 규칙을 한 번 넣는다. 세부 내용은 [음성 프롬프트 기본 지침](../../references/voice-prompt-guidance.md)을 따르고, 각 Manual에 반복하지 않는다.
10. 새 Manual 묶음은 의도한 진입 트리거부터 연결 Manual·각 분기·도구 참조와 종료/복귀까지 따라가며 전체 경로를 확인한다. 조건과 빠져나갈 경로가 분명한 순환은 오류로 단정하지 않고, 연결 깊이만으로 Flow를 선택하지 않는다. 서버 진단과 재조회도 확인하되 전체 경로 검토를 대신한다고 보지 않는다.

어긋난 곳은 같은 `manual_id`(또는 `agent_id`)로 고친 뒤, 사용자에게 "점검: ○○ 보완" 한 줄로 알린다.

## 부분 성공과 전달
Single만 저장됐다면 그 `agent_id`에서 Manual 생성 단계를 계속한다. Manual 저장 성공 뒤에는 같은 `agent_id`·`manual_id`로 확인한다. 게시 응답이 불명이면 `list_agent_versions`/`get_agent`로 production 상태를 읽고 다시 호출하지 않는다. `409` revision conflict는 최신 상태를 다시 읽고 의도를 다시 적용할 때만 처리하며, unknown 응답은 새 Single·Manual 생성이나 같은 쓰기로 자동 재시도하지 않는다. Agent 저장 성공을 시험 성공으로 보고하지 않는다. 실제 예약이 목표인데 연동이 없으면 그 결손을 알리고 사용자 목표를 유지한다.

사용자가 변경 의견을 주거나 새 대화에서 이어서 고치려 하면 [edit-manual-safely](../edit-manual-safely/SKILL.md)의 '피드백·재개 반영 순서'를 따른다.

## 마무리 보고
저장과 점검을 마치면 사용자에게 아래 순서로 짧게 알린다. 항목마다 한두 줄이면 된다.
1. **만든 것**: 유형과 이유 한 줄, Manual 이름 목록, 연결한 지식·도구·통화 결과 항목.
2. **점검 결과**: `get_manual`로 본문을 다시 읽어 '운영 수준 점검'과 대조한 결과. 고친 것이 있으면 무엇을 고쳤는지.
3. **가정과 확인할 것**: 사용자가 주지 않아 가정한 값(번호·시간·정책), 그대로 말하게 한 문구 중 고객 확인이 필요한 것, 개인정보를 받는다면 수집·녹취 안내가 필요한지.
4. **한계**: 지금 연결하지 못한 것(예: 실제 예약 시스템 연동 없음)과 그 때문에 통화에서 생기는 일.
5. **다음 할 일**: 체크리스트로 쓴다.
   - [ ] 직접 시험할 대화 3개(정상 / 예외·거절 / 위급·연결)
   - [ ] 번호 연결과 게시 전 확인할 것
   - [ ] 출시 뒤 첫 주에 볼 것: 결과별 종료 비율, 연결 실패, 도중 종료, 같은 질문 반복

## 업무 판단

첫 업무 선택·외부 의존성·질문 범위는 [업무 판단 기준](../../references/workflow-guidance.md)을 읽는다. 고객의 중요도, 자료에서 보이는 반복성과 업무 경계, 지금 확인 가능한 결과를 비교해 첫 완료 지점을 제안한다. 기술 설정 설문으로 시작하지 않는다. 독립적인 준비는 진행하고, 결정을 기다려야 하는 실행은 구분한다.

내부 접수가 목표라면 Manual의 질문과 추출·저장 필드를 함께 설계한다. 실제 예약이 목표라면 필요한 조회/등록 도구가 없는 상태를 숨기지 않는다. 음성 시험 도구는 없으므로 고객이 직접 확인할 사례와 남은 단계를 구분해 전달한다. 번호 연결·발신·통화 조회는 연결된 도구가 목록에 있을 때 위 단계로 진행하고, 없으면 해당 단계가 막혔다고 알린다.
