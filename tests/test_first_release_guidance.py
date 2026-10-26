import json
import re
import unittest

from scripts.build import ROOT

FIRST_RELEASE_TOOLS = """
get_organization list_models list_schemas get_schema update_organization list_organization_members
list_agents get_agent save_agent list_agent_versions create_agent_version publish_agent_version
list_agent_templates get_agent_template instantiate_agent_template
list_manuals get_manual save_manual list_tools get_tool save_tool
list_knowledges create_knowledge list_knowledge_documents import_knowledge_documents delete_knowledge_document
list_numbers get_number update_number set_number_agents
list_calls get_call place_call
list_campaigns get_campaign launch_campaign pause_campaign resume_campaign cancel_campaign
list_sheets get_sheet create_sheet
list_customers get_customer find_customer save_customer resolve_customer
list_customer_attribute_definitions get_customer_attribute_definition save_customer_attribute_definition
""".split()

SIDE_EFFECT_TOOLS = [
    "place_call", "launch_campaign", "resume_campaign", "publish_agent_version",
    "set_number_agents", "update_number", "delete_knowledge_document", "save_tool",
]

# Phrases that send the user to the product UI/dashboard for capabilities the 50 tools now cover.
DASHBOARD_FALLBACKS = [
    r"대시보드에서(?! 보자)",
    r"제품 UI에서 (운영|상태를 확인|실운영)",
    r"실운영(은|을)[^.\n]{0,20}제품 UI",
    r"기존 vox\.ai 제품 UI",
    r"baseline에",
    r"포함되지 않는다",
    r"도구가 없다고 .{0,10}제품 UI",
    r"Use the product UI for live operation",
    r"do not claim MCP call, campaign",
]


def read(relative):
    return (ROOT / relative).read_text()


def guidance_files():
    paths = sorted(ROOT.glob("skills/*/SKILL.md"))
    paths += [ROOT / "references" / name for name in (
        "execution-contract.md", "host-adapters.md", "workflow-guidance.md",
        "workflow-examples.md", "workflow-capabilities.json")]
    paths += [ROOT / "README.md", ROOT / "DEVELOPMENT.md"]
    return paths


class FirstReleaseGuidanceTests(unittest.TestCase):
    def test_execution_contract_states_confirmation_key_unknown_and_secret_rules(self):
        text = read("references/execution-contract.md")
        for tool in SIDE_EFFECT_TOOLS:
            self.assertIn(f"`{tool}`", text, tool)
        for needle in (
            "## 실제 영향이 있는 도구",
            "대화에서 짧게 요약한다",
            "‘계획을 짜줘’·‘준비해줘’는 실행 승인이 아니다",
            "`execution_key`(8~128자",
            "같은 키는 같은 실행(같은 인자)의 재전송에만 쓰며",
            "실패(일시 오류 포함)를 다시 시도하려면 새 키를 만든다",
            "`EXECUTION_KEY_REUSED`",
            "`EXECUTION_RESULT_UNKNOWN`",
            "`EXECUTION_IN_PROGRESS`",
            "다시 실행하지 않고 새 키도 만들지 않는다",
            "`list_calls`",
            "`get_campaign`",
            "마스킹",
            "`save_tool`에 되돌려 넣지 않고",
            "`include_transcript`",
            "지식은 텍스트·URL만 받는다",
            "번호 획득·해지는 웹에서만",
            "음성 시험 도구는 없으며 고객이 제품 UI에서 직접 시험한다",
        ):
            self.assertIn(needle, text, needle)

    def test_skills_carry_their_first_release_guidance(self):
        required = {
            "agents-platform": ["`instantiate_agent_template`", "`create_agent_version`", "`publish_agent_version`",
                                 "`set_number_agents`", "`place_call`", "`launch_campaign`", "`get_call`",
                                 "‘실제 영향이 있는 도구’", "`import_knowledge_documents`(텍스트·URL만)",
                                 "번호 획득·해지는 웹에서만"],
            "build-first-voice-agent": ["`instantiate_agent_template`", "`create_agent_version`",
                                         "`publish_agent_version`", "사용자에게 어느 버전을 production으로 지정할지 요약해 확인받고"],
            "connect-phone-service": ["`list_numbers`", "`get_number`", "`set_number_agents`", "**`set_number_agents`의 null은 연결 해제다.**",
                                       "번호 획득·해지와 대표번호·발신표기번호 신청·심사는 웹에서만", "`publish_agent_version`"],
            "operate-outbound-and-followup": ["`place_call`", "`execution_key`", "`launch_campaign`", "`pause_campaign`",
                                               "`resume_campaign`", "`cancel_campaign`", "`create_sheet`", "`EXECUTION_RESULT_UNKNOWN`",
                                               "`EXECUTION_IN_PROGRESS`", "`EXECUTION_KEY_REUSED`", "새 키를 만든다",
                                               "대화에서 짧게 요약해 사용자의 진행 확인을 받는다"],
            "prepare-voice-test": ["음성 시험을 시작하는 도구는 없다", "`get_call`", "`list_calls`", "customer_reported"],
            "inspect-call-evidence": ["`list_calls`", "`get_call`", "`include_transcript`", "사용자가 요청할 때만"],
            "review-call-performance": ["`list_calls`", "`get_call`", "`get_campaign`"],
            "knowledge-grounding": ["`create_knowledge`", "`import_knowledge_documents`", "텍스트(`document_type=text`)와 URL(`webpage`)만",
                                     "파일은 전달할 수 없으므로", "`list_knowledge_documents`", "`delete_knowledge_document`"],
            "connect-agent-tools": ["`save_tool`", "마스킹", "`save_tool`에 되돌려 넣지 않는다", "인증을 바꾸는 저장은"],
            "resume-agent-work": ["`EXECUTION_RESULT_UNKNOWN`", "재실행·새 `execution_key` 금지", "`list_calls`"],
        }
        for name, needles in required.items():
            text = read(f"skills/{name}/SKILL.md")
            for needle in needles:
                self.assertIn(needle, text, f"{name}: {needle}")

    def test_no_skill_or_reference_sends_covered_capabilities_to_the_dashboard(self):
        for path in guidance_files():
            text = path.read_text()
            for pattern in DASHBOARD_FALLBACKS:
                self.assertIsNone(re.search(pattern, text), f"{path.relative_to(ROOT)}: {pattern}")

    def test_every_first_release_tool_is_named_in_guidance_and_none_is_design_only(self):
        corpus = "\n".join(path.read_text() for path in guidance_files())
        for tool in FIRST_RELEASE_TOOLS:
            self.assertRegex(corpus, rf"(?<![A-Za-z_]){tool}(?![A-Za-z_])", tool)
        catalog = json.loads(read("catalog.json"))
        for skill in catalog["skills"]:
            self.assertFalse(set(skill["tools"]["designed_only"]) & set(FIRST_RELEASE_TOOLS), skill["name"])
        self.assertFalse(set(catalog["designed_tool_references"]) & set(FIRST_RELEASE_TOOLS))

    def test_workflow_capabilities_cover_the_first_release_journey(self):
        contract = json.loads(read("references/workflow-capabilities.json"))
        workflows = {workflow["id"]: workflow for workflow in contract["workflows"]}
        self.assertTrue({"authoring", "publish", "connect_phone", "operate", "inspect_results"} <= set(workflows))
        covered = set()
        for workflow in workflows.values():
            tools = workflow["implemented"]["required_tools"] + workflow["implemented"]["optional_tools"]
            covered.update(tools)
        self.assertTrue(set(FIRST_RELEASE_TOOLS) <= covered, sorted(set(FIRST_RELEASE_TOOLS) - covered))
        operate = workflows["operate"]
        self.assertIn("place_call", operate["implemented"]["optional_tools"])
        self.assertIn("launch_campaign", operate["implemented"]["optional_tools"])
        self.assertTrue(any("execution_key" in action for action in operate["host_actions"]))
        self.assertTrue(any("EXECUTION_RESULT_UNKNOWN" in action for action in operate["host_actions"]))
        self.assertEqual(
            workflows["publish"]["implemented"]["required_tools"],
            ["create_agent_version", "get_agent", "list_agent_versions", "publish_agent_version"])
        self.assertEqual(
            workflows["connect_phone"]["implemented"]["required_tools"],
            ["get_number", "list_numbers", "set_number_agents"])
        # The voice test stays a customer action.
        self.assertTrue(any("customer performs the voice test" in a
                            for a in workflows["customer_direct_test"]["host_actions"]))

    def test_snapshot_covers_public_tools_and_native_org_tools_only(self):
        snapshot = json.loads(read("references/implemented-tools.snapshot.json"))
        implemented = set(snapshot["implemented_tools"])
        self.assertEqual(snapshot["native_tools"], ["list_organizations", "set_organization"])
        self.assertEqual(snapshot["public_excluded"], [])
        self.assertTrue({"validate_flow", "create_voice_model", *snapshot["native_tools"]} <= implemented)
        self.assertEqual(len(implemented), 55)
        for skill in json.loads(read("catalog.json"))["skills"]:
            self.assertTrue(set(skill["tools"]["implemented"]) <= implemented, skill["name"])

    def test_flow_guidance_follows_the_real_schema(self):
        for name in ("agents-platform", "voice-agent-design"):
            text = read(f"skills/{name}/SKILL.md")
            for needle in ("snake_case", "`static_sentence`", "`prompt_type`", "`is_allow_interruption`",
                           "`begin`의 나가는 edge는 `fallback`", "`condition` 노드", "self-loop",
                           '`level="all"`'):
                self.assertIn(needle, text, f"{name}: {needle}")
        platform = read("skills/agents-platform/SKILL.md")
        for needle in ("`sendSms`", "`transferCall`", "`transferAgent`", "`endCall`", "`note`",
                       "DTMF 키 입력은 메시지로 들어오므로 키마다 AI 조건 edge를 달지 않고", "`********`", "실제 비밀값을 다시 받아"):
            self.assertIn(needle, platform, needle)

    def test_agent_type_rule_defaults_to_single_manual_and_flow_is_conditional(self):
        design = read("skills/voice-agent-design/SKILL.md")
        for needle in ("## 에이전트 유형 선택", "기본은 **Single + Manual**", "### 만들기 전에 말하기",
                       "F1 키패드 메뉴", "F2 원문 낭독", "F3 값에 따른 기계적 분기",
                       "F4 건너뛰기 금지 단계", "F5 아웃바운드 고정 스크립트",
                       "Flow 신호가 아닌 것", "애매하면 Single + Manual로 만든다"):
            self.assertIn(needle, design, needle)
        self.assertIn("Flow로 정해졌을 때만 적용한다", design)
        self.assertNotIn("Flow agent가 맞는지 먼저 비교한다", design)
        flow = design.split("## Flow와 ARS 흐름")[1]
        rest = design.split("## Flow와 ARS 흐름")[0]
        self.assertLess(len(flow), len(rest) / 2)
        for name, pointer in (("agents-platform", "Flow로 정해진 경우에만"),
                              ("build-first-voice-agent", "유형과 이유를 한 줄로 알린다"),
                              ("manual-authoring", "Flow로 바꾸지 않는다")):
            text = read(f"skills/{name}/SKILL.md")
            self.assertIn(pointer.split("(")[0], text, name)
            self.assertIn("voice-agent-design/SKILL.md", text, name)
        self.assertNotIn("메뉴·분기·전환이 정해진 흐름은 Flow agent로 만든다", read("skills/agents-platform/SKILL.md"))
        readme = read("README.md")
        self.assertLess(readme.index("Single + Manual로 만듭니다"), readme.index("키패드 메뉴 ARS를 Flow"))
        actions = " ".join(json.loads(read("references/workflow-capabilities.json"))["workflows"][0]["host_actions"])
        self.assertIn("default to single_prompt", actions)

    def test_manual_authoring_covers_split_triggers_attach_and_tool_references(self):
        text = read("skills/manual-authoring/SKILL.md")
        for needle in ("## 어디에 쓸까", "## 몇 개로 나눌까", "## 트리거 쓰기", "## 저장 순서와 확인",
                       "`@manual:`", "`@tool:이름`", "`save_manual(mode=create", "기본 프롬프트", "8,096자",
                       "`data.manuals` 맵이나 폐기된 `manualIds`를 손으로 만들지 않는다"):
            self.assertIn(needle, text, needle)
        self.assertNotIn("초기에는 완결된 Manual 하나를 만들고", text)

    def test_manual_authoring_teaches_the_template_trigger_runtime_and_reference_syntax(self):
        text = read("skills/manual-authoring/SKILL.md")
        for needle in ("## Manual이 통화에서 쓰이는 방식", "## 본문 템플릿", "## 규칙", "## 진행 절차",
                       "### 시작", "### <단계 이름>", "### <도구 결과 처리>", "### 완료",
                       "## 단계와 분기를 산문으로 쓰는 법", "## 반드시·절대와 원문 문장",
                       "## 도구 쓰기 (@tool)", "## 피할 것",
                       "**정확히 하나의** 트리거", "제외한다(○○ 담당)", "Manual 선택 우선순위",
                       "1,500~4,000자", "보통 3~10개", "`@tool:<tool_id>`",
                       "[Manual 예시](../../references/manual-examples.md)"):
            self.assertIn(needle, text, needle)
        # The target of an @manual: reference must be saved first because only its UUID is valid.
        self.assertRegex(text, r"\*\*먼저\*\* `save_manual\(mode=create\)`로 저장해 `manual_id`를 받는다")
        # Superseded advice stays out of every piece of guidance.
        for path in guidance_files() + [ROOT / "references/manual-examples.md"]:
            body = path.read_text()
            for stale in ("트리거를 비운 공용 Manual", "트리거 없는 공용", "대략 1,500자 이내", "첫 구축은 보통 2~5개"):
                self.assertNotIn(stale, body, f"{path.relative_to(ROOT)}: {stale}")
        examples = read("references/manual-examples.md")
        for needle in ("### 예시 1. 사고 보상 접수", "### 예시 2. 상담원 연결 (공용)", "## 규칙", "## 진행 절차",
                       "- trigger:", "제외한다"):
            self.assertIn(needle, examples, needle)
        # Pointers elsewhere stay short and agree with the manual-authoring guidance.
        for name in ("voice-agent-design", "build-first-voice-agent", "agents-platform"):
            self.assertIn("manual-authoring/SKILL.md", read(f"skills/{name}/SKILL.md"), name)
        for name in ("build-first-voice-agent", "agents-platform"):
            self.assertIn("@manual:<manual_id>", read(f"skills/{name}/SKILL.md"), name)
        design = read("skills/voice-agent-design/SKILL.md")
        self.assertIn("`@tool:<tool_id>`", design)
        self.assertIn("1,500~4,000자", design)
        actions = " ".join(json.loads(read("references/workflow-capabilities.json"))["workflows"][0]["host_actions"])
        self.assertIn("@manual:<manual_id>", actions)
        catalog = {skill["name"]: skill for skill in json.loads(read("catalog.json"))["skills"]}
        frontmatter = read("skills/manual-authoring/SKILL.md").split("---", 2)[1]
        self.assertIn(catalog["manual-authoring"]["description"], frontmatter)

    def test_manual_guidance_is_host_neutral_and_public_safe(self):
        paths = [ROOT / "skills/manual-authoring/SKILL.md", ROOT / "references/manual-examples.md",
                 ROOT / "skills/voice-agent-design/SKILL.md", ROOT / "skills/build-first-voice-agent/SKILL.md"]
        for path in paths:
            text = path.read_text()
            name = path.relative_to(ROOT)
            for host in ("Claude", "Codex", "Grok", "Copilot", "코파일럿", "ChatGPT", "Cursor"):
                self.assertNotIn(host, text, f"{name}: {host}")
            self.assertNotRegex(text, r"(?i)\b__docs__\b|docs repo|docs 저장소|vox-mono|/Users/", str(name))
            self.assertNotRegex(text, r"\b01[016789]-?\d{3,4}-?\d{4}\b|https?://", f"{name}: concrete contact or URL")

    def test_ars_flow_pattern_reference_states_pitfalls_and_the_silence_limit(self):
        text = read("references/flow-ars-pattern.md")
        for needle in ("분류 노드 하나", "키마다 AI edge를 다는 설계", "`fallback` edge를 달 수 없다",
                       "무입력(침묵)은 전환을 일으키지 않는다", "정확히 **\"요청 성공 시\"**",
                       "`current_time`", "휴무 edge", "`sms_from_number`", "cold 전환",
                       "만들어도 실행되지 않는다"):
            self.assertIn(needle, text, needle)
        skeleton = json.loads(read("references/flow-ars-skeleton.json"))
        types = {node["type"] for node in skeleton["nodes"]}
        self.assertTrue({"begin", "condition", "extraction", "transferCall", "sendSms", "endCall"} <= types)
        self.assertEqual([e for e in skeleton["edges"]
                          if e["source"] in {n["id"] for n in skeleton["nodes"] if n["type"] == "conversation"}
                          and e["condition"]["type"] == "fallback"], [])
        self.assertIn("flow-ars-pattern.md", read("skills/voice-agent-design/SKILL.md"))
        self.assertIn("flow-ars-pattern.md", read("skills/agents-platform/SKILL.md"))

    def test_guidance_does_not_depend_on_one_host_or_ask_for_docs_changes(self):
        for relative in ("skills/voice-agent-design/SKILL.md", "skills/manual-authoring/SKILL.md",
                         "references/flow-ars-pattern.md"):
            text = read(relative)
            for host in ("Claude Code", "Codex", "Grok"):
                self.assertNotIn(host, text, f"{relative}: {host}")

    def test_new_work_requires_confirmation_summary_for_every_side_effect_skill(self):
        for name in ("operate-outbound-and-followup", "connect-phone-service", "build-first-voice-agent",
                     "knowledge-grounding", "connect-agent-tools"):
            text = read(f"skills/{name}/SKILL.md")
            self.assertRegex(text, r"요약해 확인받|요약해 사용자의 진행 확인|대화에서 짧게 요약해", name)


if __name__ == "__main__":
    unittest.main()
