# 합성 고객 여정: 만들기, 다듬기, 직접 시험, 운영, 재개

이 예시는 합성 자료와 도구 호출 형식을 보여준다. 실제 요청 전에 연결된 호스트의 실제 도구와 schema를 확인한다. 번들의 도구 schema 후보는 실제 사용 가능 여부를 연결된 서버에서 확인한다. user-principal save_agent/save_manual에는 직전 get_work_context에서 받은 context receipt가 필요하다. 외부 공개 연결처럼 작업 기록 도구가 없는 호스트에서는 receipt 없이 저장을 시도하고 서버가 거부하면 초안과 빠진 capability를 안내한다.

## 합성 요청과 완료 기준

고객이 “샘플 홈케어 문의를 받는 음성 에이전트를 만들고 싶어요”라고 요청한다. 제공된 합성 자료에는 세 가지 업무가 있다.

- 어떤 서비스를 원하는지와 가능한 날짜 범위를 접수한다.
- 위치와 주소는 업무 범위를 파악한 뒤 한 번만 확인한다.
- 가격표나 예약 API는 연결되어 있지 않으므로 가격·방문 시간·예약 확정을 약속하지 않는다. 접수 내용 요약과 담당자 확인이 다음 단계다.

성공은 Manual에 접수 흐름과 제한이 저장되고 재조회되는 것이다. 이는 예약 기능 연결이나 고객 음성 시험 통과를 뜻하지 않는다.

## 1. Authoring: 첫 Manual 저장

조직이 의도한 곳인지 확인한 뒤, 반환된 ID만 후속 호출에 사용한다.

```mcp-call
{"tool":"get_organization","arguments":{}}
```

새 agent 모델을 고를 때는 먼저 `list_models(kind=llm)`을 호출한다. 이 예시는 사용자가 모델·계열을 지정하지 않은 경우의 흐름만 보인다. 정확한 모델·계열·공급사 지정과 구 API fallback 우선 규칙은 [모델 선택 규칙](../skills/build-first-voice-agent/SKILL.md#모델-고르기)을 따른다. `featured=true`이고 `deprecated=false`인 결과 중 `display_order`가 가장 작은 항목의 `model`을 사용한다. 아래 모델 값은 placeholder이며 실제 호출에서는 조회 결과의 `model` 값으로 바꾼다. 결과에 `featured` 필드가 없는 구 API에서는 `data.llm`을 생략하고, 서버 기본값을 사용한다고 알린다.

```mcp-call
{"tool":"list_models","arguments":{"kind":"llm"}}
```

user-principal 저장 직전에 context를 읽는다. 응답의 context_receipt.token을 아래 한 번의 save_agent에 복사한다. placeholder는 실제 호출 전에 응답 token으로 바꾼다. 영수증용 읽기는 `max_tokens`를 기본값(3000) 아래로 낮추지 않는다. `MEMORY_CONTEXT_BUDGET_TOO_SMALL`이 오면 `details.required_tokens` 이상(최대 3000)으로 한 번만 다시 호출하고, 같은 오류가 반복되면 저장하지 않고 초안으로 안내한다.

```mcp-call
{"tool":"get_work_context","arguments":{"purpose":"새 Single 생성 전 관련 결정 확인","max_tokens":3000}}
```

```mcp-call
{"tool":"save_agent","arguments":{"mode":"create","context_receipt":"<paste the recent context_receipt.token here>","payload":{"name":"샘플 홈케어 문의","data":{"llm":{"model":"<selected list_models item model>"}}}}}
```

`save_agent` 응답의 실제 `agent_id`를 받아 현재 상태와 revision을 읽는다. 아래 UUID는 모양을 보이는 합성값이며 실제 호출에서는 반환된 ID를 쓴다.

```mcp-call
{"tool":"get_agent","arguments":{"agent_id":"11111111-1111-4111-8111-111111111111"}}
```

아래 `expected_head_revision`은 형식을 보이는 예시값이다. 실제 호출에서는 방금 읽은 revision으로 바꾼다. Manual은 현재 agent에 귀속된다.

방금 읽은 agent revision을 확인한 뒤, 제품 저장마다 새 context receipt를 받는다. 이 placeholder는 실제 get_work_context 응답 token으로 바꾼다.

```mcp-call
{"tool":"get_work_context","arguments":{"agent_id":"11111111-1111-4111-8111-111111111111","purpose":"Manual 생성 전 agent 결정과 열린 작업 확인","max_tokens":3000}}
```

```mcp-call
{"tool":"save_manual","arguments":{"mode":"create","agent_id":"11111111-1111-4111-8111-111111111111","context_receipt":"<paste the recent context_receipt.token here>","payload":{"expected_head_revision":7,"name":"샘플 홈케어 문의 접수","trigger":"고객이 홈케어 서비스나 방문 가능 여부를 문의할 때, 서비스 종류나 지역을 먼저 말할 때, 또는 앞서 말한 접수 정보를 정정할 때. 이미 잡힌 방문의 변경·취소는 제외한다.","content":"## 규칙\n- 범위: 홈케어 서비스 문의 접수만 한다. 가격 확정, 방문 시각 약속, 예약 완료 안내는 하지 않는다.\n- 연결된 가격표와 예약 확인 기능이 없다. 확인이 필요한 질문은 추측하지 않고 \"담당자 확인이 필요합니다.\"라고 말한다.\n- 이미 들은 정보는 다시 묻지 않는다. 정정되면 그 값만 고친다.\n- 완료 조건: 서비스 종류, 날짜 범위, 위치를 확인하고 요약에 동의받은 뒤 \"말씀하신 내용을 확인했습니다.\"라고 안내한다. 예약 확정이나 외부 접수 성공을 말하지 않는다.\n## 진행 절차\n### 시작\n1. 고객이 이미 말한 서비스 종류, 날짜 범위, 위치를 기억하고 아직 듣지 못한 항목의 단계로 이동한다.\n### 서비스 종류\n1. 원하는 서비스 종류를 묻는다.\n### 날짜 범위\n1. 가능한 날짜 범위를 묻는다. 모른다고 하면 \"모름\"으로 기억하고 넘어간다.\n### 위치\n1. 서비스 범위를 좁힌 뒤 위치와 주소를 한 번만 확인한다.\n### 요약 확인\n1. 접수 내용을 요약하고 빠진 점이나 정정이 있는지 묻는다.\n2. 정정하면 그 항목만 고치고 요약을 다시 확인한다.\n3. 맞다고 하면 말씀하신 내용을 확인하고 끝낸다. 예약 확정이나 외부 접수 성공을 말하지 않는다."}}}
```

저장 결과의 `manual_id`를 보존하고 실제 리소스를 재조회한다.

```mcp-call
{"tool":"get_manual","arguments":{"agent_id":"11111111-1111-4111-8111-111111111111","manual_id":"22222222-2222-4222-8222-222222222222"}}
```

본문과 `head_revision`이 의도한 값인지 확인한다. Manual만 저장됐다면 새 agent를 만들지 않고 같은 `agent_id`로 이어간다. 저장 성공과 readback 성공은 별도 결과로 보고한다.

## 2. Refine: 정책을 좁게 바꾸고 확인

고객이 “주소를 먼저 묻지 말고, 어떤 서비스를 원하는지 파악한 다음 한 번만 물어봐 주세요”라고 한다. 먼저 같은 agent의 전체 Manual을 읽고 변경 지점과 보존할 제한을 확인한다.

```mcp-call
{"tool":"get_manual","arguments":{"agent_id":"11111111-1111-4111-8111-111111111111","manual_id":"22222222-2222-4222-8222-222222222222"}}
```

Manual 본문 저장은 전체 본문 교체다. 아래 `content`에는 변경 문장뿐 아니라 가격·예약 확정 제한, 요약과 정정 흐름을 포함한 **전체 새 본문**을 보낸다. `expected_head_revision`은 방금 조회한 Manual의 현재 revision으로 교체한다.

Manual의 최신 revision을 다시 읽고, 저장 직전에 새 context receipt를 받는다. 이 placeholder를 실제 token으로 교체한다.

```mcp-call
{"tool":"get_work_context","arguments":{"agent_id":"11111111-1111-4111-8111-111111111111","purpose":"Manual 수정 전 최신 결정과 agent head 확인","max_tokens":3000}}
```

```mcp-call
{"tool":"save_manual","arguments":{"mode":"update","agent_id":"11111111-1111-4111-8111-111111111111","manual_id":"22222222-2222-4222-8222-222222222222","context_receipt":"<paste the recent context_receipt.token here>","payload":{"expected_head_revision":8,"content":"## 규칙\n- 범위: 홈케어 서비스 문의 접수만 한다. 가격 확정, 방문 시각 약속, 예약 완료 안내는 하지 않는다.\n- 연결된 가격표와 예약 확인 기능이 없다. 확인이 필요한 질문은 추측하지 않고 \"담당자 확인이 필요합니다.\"라고 말한다.\n- 이미 들은 정보는 다시 묻지 않는다. 정정되면 그 값만 고친다.\n- 완료 조건: 서비스 종류, 날짜 범위, 위치를 확인하고 요약에 동의받은 뒤 \"말씀하신 내용을 확인했습니다.\"라고 안내한다. 예약 확정이나 외부 접수 성공을 말하지 않는다.\n## 진행 절차\n### 시작\n1. 고객이 이미 말한 서비스 종류, 날짜 범위, 위치를 기억하고 아직 듣지 못한 항목의 단계로 이동한다.\n### 서비스 종류\n1. 원하는 서비스 종류를 묻는다.\n### 날짜 범위\n1. 가능한 날짜 범위를 묻는다. 모른다고 하면 \"모름\"으로 기억하고 넘어간다.\n### 위치\n1. 고객이 원하는 업무 범위를 파악한 다음 위치와 주소를 한 번만 확인한다. 이미 주소를 들었다면 반복 질문하지 않는다.\n### 요약 확인\n1. 접수 내용을 요약하고 빠진 점이나 정정이 있는지 묻는다.\n2. 정정하면 그 항목만 고치고 요약을 다시 확인한다.\n3. 맞다고 하면 말씀하신 내용을 확인하고 끝낸다. 예약 확정이나 외부 접수 성공을 말하지 않는다."}}}
```

`get_manual(agent_id, manual_id)`로 다시 읽어 주소 규칙이 한 번만 반영되고 다른 제한이 남았는지 확인한다. `409`이면 최신 본문을 다시 읽고 의도를 재적용한다. 쓰기 응답이 불명이면 중복 update를 보내지 말고 알려진 ID를 재조회한다.

## 3. Customer direct test: 고객이 직접 말해 보고 피드백

Assistant는 고객이 확인할 사례와 기대 동작을 준비한다. 예를 들어 고객은 “이번 주 금요일에 에어컨 청소 가능해요? 가격도 알려주세요”라고 말해 본다. 기대 동작은 서비스 종류와 날짜 범위를 접수하고, 연결되지 않은 가격·예약 확정을 약속하지 않는 것이다. 두 번째 사례에서는 고객이 먼저 주소를 말하고 서비스 종류를 바꾼다. 기대 동작은 주소를 되묻지 않고 새 서비스 범위를 반영하는 것이다.

음성 시험을 시작하는 도구는 없어 고객이 제품 UI에서 직접 시험한다. 고객이 “두 번째 사례에서 주소를 다시 물었어요”라고 보고하면 이후 작업에 영향을 줄 피드백으로 보고 기록한다. 고객이 callId를 주거나 `list_calls`로 해당 통화를 찾아 `get_call`로 읽기 전에는 independent call evidence라고 부르지 않는다. 조회한 뒤에는 상태·당시 버전·추출 결과를 근거로 쓰고 원문은 필요할 때만 `include_transcript`로 읽는다. call reference는 locator로만 남기고 전체 transcript를 수집하지 않는다.

피드백이 Manual 분기 수정으로 이어지면 위 refine 흐름으로 좁게 바꾸고 저장값을 재조회한다. 고객의 보고는 feedback_reported 또는 customer_voice_report로 요약 기록하고 계속 reported 상태로 둔다. 전달에는 고객이 다시 말할 문장과 기대 결과를 적는다. 실제 재시험 전에는 “저장 확인·고객 재시험 대기”로 상태를 표현한다.

## 4. Operate: 게시, 번호 연결, 발신, 결과 확인

고객이 “오늘부터 실제 문의를 받아도 될까요?”라고 묻는다. 순서는 다음과 같다. 각 단계 뒤에 응답과 재조회로 확인한다.

1. 현재 설정을 `create_agent_version`으로 버전에 남기고 `list_agent_versions`로 확인한다.
2. 어느 버전을 production으로 지정할지 대화에서 요약해 확인받고 `publish_agent_version`을 호출한 뒤 `get_agent`로 production 설정을 읽는다.
3. 이미 가진 번호를 `list_numbers`/`get_number`로 찾아 연결 변경(현재 → 변경, 해제 여부)을 요약해 확인받고 `set_number_agents`를 호출한 뒤 `get_number`로 확인한다. 번호 획득은 웹에서만 한다.
4. 통제된 인바운드 전화나, 대상·발신 번호·agent 버전을 요약해 확인받은 `place_call`(새 `execution_key`)로 첫 통화를 만든다. 대량은 `create_sheet` → `launch_campaign`(새 `execution_key`)이며 `pause_campaign`/`resume_campaign`/`cancel_campaign`으로 제어한다.
5. `list_calls`/`get_call`로 접수·연결·종료·추출 결과를 읽는다. 응답이 불명(`EXECUTION_RESULT_UNKNOWN`·`EXECUTION_IN_PROGRESS`)이면 다시 실행하지 않고 `list_calls`·`get_campaign`으로 확인한다.

이후 고객이 “오늘 접수는 괜찮았지만 주소를 중복 질문했다”고 알려주면 고객 보고로 분류하고, 해당 통화가 조회되면 `get_call` 근거로 수정 가설·확인 사례를 제안한다. 조회되지 않은 운영 결과는 관측된 call 통계로 표현하지 않는다. 저장된 설정만 보고 운영 가능하다고 판정하거나 실제 전화가 나갔다고 말하지 않는다.

## 5. Resume: 부분 성공을 보존하고 다른 세션에서도 안전하게 이어가기

### Manual 생성 응답이 불명인 경우

agent 생성은 성공해 실제 `agent_id`를 받았지만 Manual 생성 응답이 사라졌다고 하자. 새 Manual을 즉시 만들지 않는다. 같은 `agent_id`에서 목록을 확인한다.

```mcp-call
{"tool":"list_manuals","arguments":{"agent_id":"11111111-1111-4111-8111-111111111111"}}
```

Manual 이름이 맞는 항목이 하나여도 기존 리소스와 이번 create 요청을 구분할 수는 없다. 후보의 실제 `manual_id`로 전체 본문과 revision을 읽어 의도한 내용인지 대조한다. 일치하면 그 리소스를 현재 대상으로 이어갈 수 있지만, exact receipt나 별도 증거가 없으면 불명 쓰기의 성공이라고 보고하지 않는다. 없거나 여러 후보가 있거나 내용이 다르면 상태 불명으로 남기고 create를 반복하지 않는다.

### 다른 Thread나 호스트에서 다시 시작하는 경우

번들 후보에는 shared-work 도구 네 개가 있다. 새 Thread나 다른 호스트에서는 실제 tool list와 schema를 먼저 확인하고 get_work_context/get_work_record로 case와 version을 읽는다. 관련 결정·피드백은 별도 기억 키워드를 요구하지 않고 짧게 save_work_record로 남긴다. routine case/event 저장 전 `get_work_context.data.background_settings`의 enabled/revision/epoch를 확인한다. 기본은 켜짐이며 OFF이면 automatic 저장을 멈춘다. 명시적으로 요청한 기존 기록 조회·정정·삭제는 계속 지원한다. 사용자가 현재 대화에서 저장하지 말라고 직접 요청하면 새 기록이나 수정을 하지 않는다. 도구가 없을 때만 현재 대화나 아래 사용자 제공 handoff로 이어가며 다른 Thread를 검색했다고 말하지 않는다.

```text
목표: 샘플 홈케어 문의 접수 Manual 완성
agent_id: <실제 ID>
manual_id: <실제 ID>
마지막으로 확인한 agent/manual revision: <실제 값>
직접 표현한 결정: 업무 범위 파악 후 주소를 한 번만 묻기
시험 피드백: 고객 보고 — 주소를 다시 물었음; call 증거는 미확인
다음 행동: 최신 Manual을 다시 읽고 규칙을 좁게 수정한 뒤 고객에게 재시험 사례 전달
```

이 fallback 요약은 사용자 제공 handoff이며 서버 기록이 아니다. shared-work 경로에서는 MCP가 반환한 case/record ID와 version을 확인한다. save_work_record 결과가 unknown이면 동일 operation_id로 get_work_operation을 조회하고 POST를 반복하지 않는다. 어느 경로든 재개할 때는 [resume-agent-work](../skills/resume-agent-work/SKILL.md)의 동일 ID·최신 상태 확인 원칙을 적용한다.


## 6. Relevant work record: 결정과 고객 피드백

중요한 사용자 결정이나 이후 작업에 영향을 줄 고객 피드백이 나오면 “기억해” 요청을 기다리지 않고 관련 record를 확인한다. 먼저 get_work_context를 읽고, agent case 목록은 아래처럼 찾는다.

```mcp-call
{"tool":"get_work_context","arguments":{"agent_id":"11111111-1111-4111-8111-111111111111","purpose":"현재 agent의 결정과 열린 개선 case 찾기","max_tokens":1000}}
```

기존 case 목록은 get_work_record로 확인한다.

```mcp-call
{"tool":"get_work_record","arguments":{"record_type":"list","agent_id":"11111111-1111-4111-8111-111111111111","limit":20}}
```

기존 case가 없으면 goal과 success criteria, 최소 source locator로 case를 만든다. operation_id는 매 쓰기마다 새 UUID를 한 번 사용한다.

```mcp-call
{"tool":"save_work_record","arguments":{"action":"create","payload":{"operation_id":"33333333-3333-4333-8333-333333333333","agent_id":"11111111-1111-4111-8111-111111111111","goal":"홈케어 문의 Manual이 주소를 한 번만 확인하는지 개선한다","success_criteria":"서비스 범위를 확인한 다음 주소를 한 번만 묻고 가격이나 예약을 확정하지 않는다","source":{"source_host":"codex","explicit_quote":"샘플 홈케어 문의를 받는 음성 에이전트를 만들고 싶어요.","observed_at":1790670000000},"expected_settings_revision":1,"expected_settings_epoch":1}}}
```

Routine automatic 저장의 `expected_settings_revision`과 `expected_settings_epoch`는 최신 get_work_context의 `background_settings`에서 복사한다. 예시 값은 placeholder이므로 실제 설정이 OFF이거나 revision/epoch가 달라졌다면 자동 요청을 보내지 않는다.

기존 case라면 get_work_record의 case version을 읽고 decision_set 또는 feedback_reported event를 append한다. 고객의 “주소를 다시 물었어요”는 고객 보고이며 call 조회 결과가 아니다. 아래 version/ID는 예시이므로 실제 응답값으로 바꾼다.

```mcp-call
{"tool":"get_work_record","arguments":{"record_type":"case","case_id":"44444444-4444-4444-8444-444444444444"}}
```

결정은 짧은 typed event로 남긴다.

```mcp-call
{"tool":"save_work_record","arguments":{"action":"event","case_id":"44444444-4444-4444-8444-444444444444","payload":{"expected_version":1,"operation_id":"55555555-5555-4555-8555-555555555555","source":{"source_host":"codex","explicit_quote":"주소를 먼저 묻지 말고, 어떤 서비스를 원하는지 파악한 다음 한 번만 물어봐 주세요.","observed_at":1790670000000},"payload":{"kind":"decision_set","statement":"업무 범위를 파악한 뒤 주소를 한 번만 묻는다","applicability":"샘플 홈케어 문의"},"expected_settings_revision":1,"expected_settings_epoch":1}}}
```

고객의 음성 피드백도 같은 case에 보고 event로 기록한다. 고객 보고를 독립 call evidence로 바꾸지 않는다.

```mcp-call
{"tool":"save_work_record","arguments":{"action":"event","case_id":"44444444-4444-4444-8444-444444444444","payload":{"expected_version":2,"operation_id":"66666666-6666-4666-8666-666666666666","source":{"source_host":"codex","explicit_quote":"두 번째 사례에서 주소를 다시 물었어요.","observed_at":1790670000000},"payload":{"kind":"feedback_reported","statement":"고객 보고: 두 번째 사례에서 주소를 다시 물음. 독립 call 조회는 아직 없음.","customer_tested":true},"expected_settings_revision":1,"expected_settings_epoch":1}}}
```

독립적인 text-contract holdout은 실제 voice test가 아니다. 아래 입력은 예시일 뿐이며 ID는 합성 값이다. holdout 등록은 자동 경로가 아니라 명시적 events 경로를 쓰므로 `expected_settings_*`를 보내지 않는다. 출처는 사용자가 현재 임베디드 Copilot 대화에서 직접 입력한 본인의 말이어야 하며 `source_host`는 `embedded`여야 한다. `source_thread_id`·`source_message_id`는 같은 턴에서 그 입력이 처리되기 전에 `get_work_context`가 돌려준 `pending_recent_inputs` 항목의 `source_thread_id`·`source_id`를 그대로 복사한 값이다(예: `{"source_id":"99999999-9999-4999-8999-999999999999","source_thread_id":"88888888-8888-4888-8888-888888888888","status":"pending",...}`). `explicit_quote`를 넣으면 그 입력의 부분 문자열이어야 한다. holdout 등록 가능 여부는 호스트 이름(Codex, Claude 등)으로 판단하지 않는다. 결론을 내리기 전에 반드시 `get_work_context(agent_id)`를 먼저 호출한다. `pending_recent_inputs`에 지금 사용자 메시지에 해당하는 항목이 `source_thread_id`와 함께 있으면 그 `source_thread_id`·`source_id`로 등록한다(`source_host`는 `embedded`). 해당 항목이 없으면 등록할 수 없다고 안내한다. `source_thread_id`가 비어 있는 항목도 추측하지 말고 등록하지 않는다. 운영에서는 사용자가 제공한 독립 task와 exact expected artifact를 사용한다. 시나리오는 이스케이프된 JSON 문자열을 손으로 만들지 않고 구조화 필드 `holdout_scenario`(`base_configuration`, `requested_change`, `required_preservation` 1~6개 문자열)로 보낸다. MCP가 `task_kind=agent_partial_edit`를 붙여 정규 `scenario` 문자열을 만들며, 예전 `scenario` 문자열도 받지만 둘을 함께 보내지 않는다. 전체 시나리오는 4096 UTF-8 바이트, `requested_change`와 보존 항목은 각각 1024 바이트 이하여야 한다. `required_preservation`·`required_additions` 값은 설명이 아니라 `base_configuration`·`requested_change`에서 글자 그대로 복사한 문구이며 `expected_result`는 채점되지 않는다. 같은 사실이 여러 곳에 있고 요청이 한쪽만 언급하면 선택 필드 `required_additions`(예: `["오후 8시"]`)와 `retired_literals`(예: `["오후 7시"]`)로 양쪽 반영을 확인한다. `observed_result`는 등록 필수 필드지만 `register_holdout: true`에서는 서버가 caller 값을 폐기하고 실행 전/unverified로 저장한다. expected artifact와 preservation 조건은 model prompt에 전달되지 않고 서버 grader에만 사용된다.

잘못된 예: holdout(`register_holdout: true`) payload에 routine 전용 `expected_settings_revision`·`expected_settings_epoch`(또는 `proposal_id`·비어 있지 않은 `evidence_ids`)를 함께 보내면 INVALID_ARGUMENTS이며 `details.problems`에 허용되지 않는 필드로 표시되므로, 그 필드를 제거하고 같은 operation_id로 다시 보낸다.

```mcp-call
{"tool":"save_work_record","arguments":{"action":"event","case_id":"44444444-4444-4444-8444-444444444444","payload":{"expected_version":3,"operation_id":"77777777-7777-4777-8777-777777777777","source":{"source_host":"embedded","source_thread_id":"88888888-8888-4888-8888-888888888888","source_message_id":"99999999-9999-4999-8999-999999999999","explicit_quote":"합성 text holdout 등록 예시이며 실제 고객 시험이나 음성 결과가 아닙니다.","observed_at":1790670000000},"payload":{"kind":"evaluation_reported","holdout_scenario":{"base_configuration":"환불 문의에는 영수증을 먼저 요청한다.","requested_change":"배송 지연 문의에는 예상 도착일을 함께 안내한다.","required_preservation":["영수증을 먼저 요청한다"]},"expected_result":"환불 문의에는 영수증을 먼저 요청한다. 배송 지연 문의에는 예상 도착일을 함께 안내한다.","observed_result":"Scenario registered; no provider execution.","evaluation_kind":"text_contract","register_holdout":true}}}}
```

외부 call transcript 전체를 읽거나 복사하지 않는다. 필요한 것은 짧은 피드백과, 사용자가 제공한 경우 조회에 필요한 call ID뿐이다. get_work_context의 background_settings가 OFF이면 routine create/event를 보내지 않는다. settings CAS가 거부되면 최신 context를 다시 읽기 전에는 반복하지 않는다. 사용자가 현재 대화에서 저장하지 말라고 직접 요청하면 자동 create/event 없이 현재 대화에서만 이어간다. 기존 기록을 사용자가 명시적으로 조회·정정·삭제해 달라고 요청한 경우에는 해당 요청을 지원한다.

save_work_record 응답이 unknown이면 같은 operation_id로 조회한다. 방금 보낸 UUID를 그대로 쓰고 POST를 재전송하지 않는다.

```mcp-call
{"tool":"get_work_operation","arguments":{"operation_id":"66666666-6666-4666-8666-666666666666"}}
```
