"""Keep skill and voice-guidance loading budgets tied to the frozen 0.2.13 baseline."""
import math
import re
import unittest
from pathlib import Path

import tiktoken


ROOT = Path(__file__).resolve().parents[1]

# Exact o200k_base counts from baseline e14f540. Per-file headroom allows focused
# semantic additions; the tighter aggregate cap prevents moving the whole corpus
# above baseline to hide concentrated growth.
BASELINE_SKILL_TOKENS = {
    'skills/agents-platform/SKILL.md': 3142,
    'skills/build-first-voice-agent/SKILL.md': 4322,
    'skills/cli-authoring/SKILL.md': 553,
    'skills/configure-call-results/SKILL.md': 512,
    'skills/configure-supporting-channel/SKILL.md': 432,
    'skills/connect-agent-tools/SKILL.md': 698,
    'skills/connect-phone-service/SKILL.md': 786,
    'skills/dashboard-navigation/SKILL.md': 528,
    'skills/edit-manual-safely/SKILL.md': 1335,
    'skills/explore-agent-context/SKILL.md': 541,
    'skills/inspect-call-evidence/SKILL.md': 578,
    'skills/knowledge-grounding/SKILL.md': 730,
    'skills/manual-authoring/SKILL.md': 5519,
    'skills/operate-outbound-and-followup/SKILL.md': 1280,
    'skills/post-call-result-design/SKILL.md': 486,
    'skills/prepare-voice-test/SKILL.md': 905,
    'skills/product-documentation/SKILL.md': 653,
    'skills/resume-agent-work/SKILL.md': 1783,
    'skills/review-call-performance/SKILL.md': 634,
    'skills/review-shared-impact/SKILL.md': 497,
    'skills/tool-integration-design/SKILL.md': 502,
    'skills/troubleshoot-agent-tool/SKILL.md': 584,
    'skills/try-and-improve-voice-agent/SKILL.md': 1058,
    'skills/tune-voice-behavior/SKILL.md': 786,
    'skills/voice-agent-design/SKILL.md': 3074,
    'skills/voice-interaction-design/SKILL.md': 519,
}

# Count each unique file once. The common voice guide did not exist at baseline.
HOTPATH_BASELINE_TOKENS = {
    'skills/build-first-voice-agent/SKILL.md': 4322,
    'skills/manual-authoring/SKILL.md': 5519,
    'skills/voice-agent-design/SKILL.md': 3074,
    'references/voice-prompt-guidance.md': 0,
    'references/manual-examples.md': 2198,
}
SKILL_BASELINE_TOTAL = sum(BASELINE_SKILL_TOKENS.values())
HOTPATH_BASELINE_TOTAL = sum(HOTPATH_BASELINE_TOKENS.values())

# The three entry-point skills stay individually within the same +5% bound as
# the full hotpath. Other files have local allowances, with the aggregate cap
# serving as the stricter guard against distributed growth.
ENTRY_SKILL_CAPS = {
    'skills/build-first-voice-agent/SKILL.md': 4538,
    'skills/manual-authoring/SKILL.md': 5794,
    'skills/voice-agent-design/SKILL.md': 3227,
}

HOTPATH_FILES = (
    'skills/build-first-voice-agent/SKILL.md',
    'skills/manual-authoring/SKILL.md',
    'skills/voice-agent-design/SKILL.md',
    'references/voice-prompt-guidance.md',
    'references/manual-examples.md',
)


class GuidanceTokenBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encoder = tiktoken.get_encoding('o200k_base')

    def token_count(self, relative_path):
        return len(self.encoder.encode((ROOT / relative_path).read_text(encoding='utf-8')))

    @staticmethod
    def current_skill_paths():
        return sorted(
            str(path.relative_to(ROOT))
            for path in (ROOT / 'skills').rglob('SKILL.md')
        )

    def assert_at_most_five_percent_over(self, actual, baseline, label):
        upper = math.floor(baseline * 1.05)
        self.assertLessEqual(actual, upper, f'{label}: {actual} is above {upper}')

    def test_skill_inventory_matches_the_frozen_baseline(self):
        actual = set(self.current_skill_paths())
        self.assertTrue(set(BASELINE_SKILL_TOKENS).issubset(actual))

    def test_core_voice_guide_has_four_direct_skill_routes(self):
        linked_skills = {
            path for path in self.current_skill_paths()
            if 'voice-prompt-guidance.md' in (ROOT / path).read_text(encoding='utf-8')
        }
        self.assertEqual(linked_skills, {
            'skills/build-first-voice-agent/SKILL.md',
            'skills/manual-authoring/SKILL.md',
            'skills/edit-manual-safely/SKILL.md',
            'skills/voice-interaction-design/SKILL.md',
        })

    def test_failure_guide_is_linked_only_from_diagnosis_skills(self):
        linked_skills = {
            path for path in self.current_skill_paths()
            if 'voice-prompt-failure-guidance.md' in (ROOT / path).read_text(encoding='utf-8')
        }
        self.assertEqual(linked_skills, {
            'skills/inspect-call-evidence/SKILL.md',
            'skills/try-and-improve-voice-agent/SKILL.md',
        })

    def test_each_skill_has_a_baseline_derived_cap(self):
        for path in self.current_skill_paths():
            with self.subTest(path=path):
                actual = self.token_count(path)
                baseline = BASELINE_SKILL_TOKENS.get(path)
                # The global +5% corpus budget is stricter than this local cap.
                # A 10% allowance or 200 tokens, whichever is larger, gives a
                # changed skill room for required detail while stopping outliers.
                # New skills have no historical per-file budget; they receive a
                # 2,000-token ceiling and still count toward the aggregate cap.
                cap = (baseline + max(200, math.ceil(baseline * 0.10))
                       if baseline is not None else 2000)
                self.assertLessEqual(actual, cap, f'{path}: {actual} tokens exceeds {cap}')

    def test_entry_skills_stay_within_five_percent_of_baseline(self):
        for path, cap in ENTRY_SKILL_CAPS.items():
            with self.subTest(path=path):
                self.assertLessEqual(self.token_count(path), cap)

    def test_skill_total_stays_within_five_percent_of_baseline(self):
        paths = self.current_skill_paths()
        actual = sum(self.token_count(path) for path in paths)
        self.assert_at_most_five_percent_over(actual, SKILL_BASELINE_TOTAL, 'all SKILL.md files')

    def test_voice_authoring_hotpath_stays_within_five_percent(self):
        actual = sum(self.token_count(path) for path in HOTPATH_FILES)
        self.assert_at_most_five_percent_over(actual, HOTPATH_BASELINE_TOTAL, 'voice authoring hotpath')

    def test_hotpath_has_no_repeated_long_prose_paragraphs(self):
        paragraphs = {}
        for path in HOTPATH_FILES:
            if path.endswith('/manual-examples.md'):
                continue  # The file consists of worked examples, excluded by design.
            text = (ROOT / path).read_text(encoding='utf-8')
            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
            for paragraph in re.split(r'\n\s*\n', text):
                normalized = re.sub(r'\s+', ' ', paragraph).strip().lower()
                normalized = re.sub(r'[`*_#>]+', '', normalized)
                if len(normalized) < 150:
                    continue
                if re.search(r'(^|\n)#{1,6}.*(?:예시|example)|\[.*예시', paragraph, re.IGNORECASE):
                    continue
                paragraphs.setdefault(normalized, set()).add(path)

        duplicates = {
            paragraph: paths for paragraph, paths in paragraphs.items() if len(paths) > 1
        }
        self.assertFalse(duplicates, f'repeated hotpath prose: {duplicates}')


if __name__ == '__main__':
    unittest.main()
