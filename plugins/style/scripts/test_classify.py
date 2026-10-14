"""Every backend's raw output parses to the same answers. Run: python3 -m unittest test_classify"""
import json
import unittest

import classify

ANSWERS = {
    "reply_mode": {"type": "choice", "choice": "short",
                   "probabilities": {"short": 0.7, "detailed": 0.05, "trace": 0.1, "code": 0.05, "design": 0.1},
                   "confidence": 0.6},
    "max_lines": {"type": "score", "score": 0,
                  "legend": {"0": "up to 3 lines", "1": "up to 8 lines", "2": "up to 20 lines", "3": "no limit"},
                  "probabilities": {"0": 0.7, "1": 0.2, "2": 0.05, "3": 0.05}, "confidence": 0.6},
    "go_ahead": {"type": "noul", "noul": 0.05},
    "prev_verdict": {"type": "choice", "choice": "none",
                     "probabilities": {"liked": 0.02, "disliked": 0.02, "none": 0.96}, "confidence": 0.95},
    "prev_issue": {"type": "choice", "choice": "none", "probabilities": {"none": 1.0}, "confidence": 0.95},
}
BODY = json.dumps({"answers": ANSWERS})

# Shapes seen live: claude -p --output-format json; opencode run's header line and ANSI colours;
# a model that wraps its JSON in a fence and a sentence; the TypeSafe /v1/systemone response.
RAW = {
    "claude": json.dumps({"type": "result", "subtype": "success", "is_error": False,
                          "result": "```json\n" + BODY + "\n```", "total_cost_usd": 0.0008}),
    "opencode": "\x1b[0m\n> build · deepseek-v4.1-flash\n\x1b[0m\n" + BODY + "\n",
    "pi": "Here is the classification:\n```json\n" + BODY + "\n```\n",
    "jev": json.dumps({"model": "jev-latest", "answers": ANSWERS,
                       "usage": {"input_tokens": 900, "output_tokens": 120}}),
}


class ParseTest(unittest.TestCase):
    def test_every_backend_parses_to_the_same_answers(self):
        for name, raw in RAW.items():
            with self.subTest(backend=name):
                self.assertEqual(classify.BACKENDS[name][1](raw), ANSWERS)

    def test_parsed_answers_build_the_directive(self):
        self.assertTrue(classify.directive(classify.parse_text(RAW["pi"]), True)
                        .startswith("[style] reply=short, up to 3 lines"))

    def test_cli_error_output_classifies_to_nothing(self):
        error = "\x1b[91m\x1b[1mError: \x1b[0mModel not found: opencode-go/x.\n"
        original = classify.BACKENDS["opencode"]
        classify.BACKENDS["opencode"] = (lambda model, request: error, *original[1:])
        try:
            self.assertEqual(classify.classify("opencode", {}), {})
        finally:
            classify.BACKENDS["opencode"] = original


if __name__ == "__main__":
    unittest.main()
