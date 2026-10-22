# 통화 중 맥락 넣기

진행 중인(`ongoing`) 통화에 외부 시스템이 알게 된 사실을 텍스트로 전달하는 REST API다. 연결된 서버가 이를 실행하는 도구를 제공하지 않으면 도구를 호출하거나 전달됐다고 말하지 않고, 아래 요청 형식을 안내만 한다. 이 API는 사람을 연결하는 전환과 다르다. 고객 응대에 필요한 사실을 에이전트에게 알리는 용도다.

## 요청

`POST https://client-api.tryvox.co/v3/calls/{call_id}/context`

- 인증은 API 키 Bearer 헤더다. 키를 대화에 붙여 넣거나 파일에 저장하지 않는다.
- `Idempotency-Key` 헤더는 필수다(비어 있지 않고 255자 이하). 같은 키와 같은 본문의 재전송은 24시간 동안 처음 응답을 돌려주고 맥락을 다시 넣지 않는다. 새 맥락마다 새 키를 쓴다.
- 본문은 `text`(필수), `response`(`none` 또는 `when_idle`, 기본 `none`), `expires_in_seconds`다.
- 성공하면 `202`와 `{call_id, control_id, status: "accepted"}`가 온다. 이는 통화에 전달됐다는 뜻까지만이다.

| `response` | 에이전트 행동 | `expires_in_seconds` |
| --- | --- | --- |
| `none` | 먼저 말하지 않고 기억해 다음 응답부터 반영한다 | 쓸 수 없다(보내면 거절) |
| `when_idle` | 통화가 조용해지면 그 내용에 대해 한 번 먼저 말한다 | 1~180초, 생략하면 90초. 말하기를 시작할 때까지 기다리는 시간이다 |

## 통화에서 일어나는 일

- 맥락은 연동한 시스템이 보낸 외부 데이터로 다뤄지며 고객의 발화나 지시로 취급되지 않는다. 통화가 끝날 때까지 이후 응답에 쓰인다.
- 첫 인사가 끝난 뒤에 반영된다. 고객이나 에이전트가 말하는 중이면 끊지 않는다.
- 상담사 전환 중이거나 통화가 끝나는 중이면 반영되지 않는다.
- 통화당 한도를 넘으면 `429 CONTEXT_LIMIT_EXCEEDED`가 온다(초당 2회, 분당 10회, 먼저 말하기 대기 8건, 본문 합계 64 KiB). `text`는 공백만이면 안 되고 요청 전체가 16 KiB 이하여야 한다.
- 진행 중이 아닌 통화는 `CALL_NOT_ACTIVE`로 거절된다.

## 결과 확인

처리 결과가 정해지면 통화 데이터 웹훅 URL로 `call_context` 이벤트가 요청마다 한 번 온다. 별도 구독은 필요 없고 맥락 본문은 담기지 않는다. 요청 응답의 `control_id`나 요청에 쓴 `Idempotency-Key`(`idempotency_key`)로 짝을 맞춘다. 웹훅이 `202`보다 먼저 올 수 있다.

- `input`: 맥락이 에이전트에 닿은 결과(`applied`, `rejected`, `canceled`). 반영되지 않은 사유는 `failure_reason`에 온다.
- `reply`: 말하기 결과(`not_requested`, `completed`, `merged`, `interrupted`, `expired`, `canceled`, `unknown`).
- `consumed`는 응답을 만드는 데 쓰였다는 뜻일 뿐 에이전트가 그 내용을 말했다는 뜻이 아니다. 말했는지는 `reply`로 판단한다.

## 재시도

- `202`를 받으면 성공으로 보고하되, 반영과 발화는 웹훅이 올 때까지 확인되지 않았다고 말한다. 웹훅이 끝내 오지 않으면 결과를 알 수 없는 요청으로 둔다.
- `503 CONTEXT_COMMAND_UNAVAILABLE`은 `details.retryable`을 확인한다. `true`이면 같은 키로 다시 보낸다. `false`이면 전달 여부를 알 수 없으므로 새 키로 보내지 않는다. 같은 맥락이 두 번 들어갈 수 있다.
- `409 IDEMPOTENCY_KEY_CONFLICT`는 같은 키를 다른 본문에 쓴 것이다. 새 키가 필요한 요청인지 사용자에게 확인한다.
