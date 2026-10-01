import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from eagle_prompt_rules import matching_tags, saved_positive_prompt


class PromptRulesTests(unittest.TestCase):
    def test_multiple_matches_and_deduplication(self):
        self.assertEqual(matching_tags("Blue_Hair, outdoors", [["blue hair", "青髪"], ["outdoors", "屋外"], ["Blue_Hair", "青髪"]]), ["青髪", "屋外"])

    def test_empty_and_invalid_rules(self):
        self.assertEqual(matching_tags("cat", [["", "全画像"], ["cat", ""], [None, "猫"], ["cat"], ["cat", " 猫 "]]), ["猫"])

    def test_token_weight_and_substrings(self):
        self.assertEqual(matching_tags("cathedral, ((blue_hair:1.2)), [outdoors]", [["cat", "猫"], ["blue hair", "青髪"], ["outdoors", "屋外"]], "token"), ["青髪", "屋外"])
        self.assertEqual(matching_tags("cathedral", [["cat", "猫"]]), ["猫"])

    def test_case_sensitive(self):
        self.assertEqual(matching_tags("Blue Hair", [["blue hair", "青髪"]], ignore_case=False), [])

    def test_saved_image_prompt_excludes_negative_and_parameters(self):
        info = "blue hair\noutdoors\nNegative prompt: red hair\nSteps: 20, Sampler: Euler, Seed: 2"
        self.assertEqual(saved_positive_prompt(info, "red hair"), "blue hair\noutdoors")
        self.assertEqual(matching_tags(saved_positive_prompt(info), [["red hair", "赤髪"]]), [])

    def test_no_negative_and_empty_positive(self):
        self.assertEqual(saved_positive_prompt("cat\nSteps: 20, Seed: 2"), "cat")
        self.assertEqual(saved_positive_prompt("Negative prompt: cat\nSteps: 20, Seed: 2", "cat"), "")
        self.assertEqual(saved_positive_prompt(None, "cat"), "cat")


if __name__ == "__main__":
    unittest.main()
