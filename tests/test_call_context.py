"""Keep the call context reference aligned with the public API contract."""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'references/call-context.md'


class CallContextReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = REFERENCE.read_text(encoding='utf-8')

    def test_documents_request_contract(self):
        for phrase in (
            'POST https://client-api.tryvox.co/v3/calls/{call_id}/context',
            '`Idempotency-Key` 헤더는 필수다',
            '`none`',
            '`when_idle`',
            '1~180초, 생략하면 90초',
            '{call_id, control_id, status: "accepted"}',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_documents_webhook_result_and_retry_rules(self):
        for phrase in (
            '`call_context` 이벤트',
            '`control_id`',
            '`reply`',
            '`503 CONTEXT_COMMAND_UNAVAILABLE`',
            '새 키로 보내지 않는다',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_does_not_claim_an_unexposed_tool_ran(self):
        self.assertIn('도구를 호출하거나 전달됐다고 말하지 않고', self.text)

    def test_skills_link_the_reference(self):
        for path in (
            'skills/operate-outbound-and-followup/SKILL.md',
            'skills/inspect-call-evidence/SKILL.md',
        ):
            with self.subTest(path=path):
                body = (ROOT / path).read_text(encoding='utf-8')
                self.assertIn('../../references/call-context.md', body)


if __name__ == '__main__':
    unittest.main()
