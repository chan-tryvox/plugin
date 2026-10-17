import json
import re
import unittest

from scripts.build import ROOT


MCP_CALL_BLOCK = re.compile(r"```mcp-call\s*\n(.*?)\n```", re.DOTALL)


def load_calls():
    text = (ROOT / "references/workflow-examples.md").read_text()
    return [json.loads(block) for block in MCP_CALL_BLOCK.findall(text)]


class WorkflowExampleTests(unittest.TestCase):
    def test_manual_body_examples_decode_newlines(self):
        manuals = [call for call in load_calls() if call["tool"] == "save_manual"]
        self.assertEqual(len(manuals), 2)
        for call in manuals:
            content = call["arguments"]["payload"]["content"]
            self.assertIn("\n", content)
            self.assertNotIn("\\n", content)


if __name__ == "__main__":
    unittest.main()
