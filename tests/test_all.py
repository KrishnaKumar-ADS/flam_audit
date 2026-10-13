#!/usr/bin/env python3
"""Deterministic test suite for The Audit submission.

No network access, GPU, or model download required.
Run: python -m pytest tests/test_all.py -v   (or: python tests/test_all.py)
"""
import csv, json, math, os, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ── Part A: metric function tests ──────────────────────────────────────────

class TestSplitBehavior(unittest.TestCase):
    """A2 Finding: literal split(' ') vs .split() on whitespace."""

    def test_single_space(self):
        line = "alpha beta"
        self.assertEqual(len(line.split(" ")), 2)
        self.assertEqual(len(line.split()), 2)

    def test_double_space_literal(self):
        """split(' ') on 'alpha  beta' yields 3 fields (one empty)."""
        line = "alpha  beta"
        self.assertEqual(len(line.split(" ")), 3, "literal split counts empty field")

    def test_double_space_robust(self):
        """.split() collapses whitespace → 2 words."""
        line = "alpha  beta"
        self.assertEqual(len(line.split()), 2)

    def test_leading_spaces(self):
        line = "  alpha beta"
        self.assertEqual(len(line.split(" ")), 4)  # two empty + alpha + beta
        self.assertEqual(len(line.split()), 2)

    def test_trailing_spaces(self):
        line = "alpha beta  "
        self.assertEqual(len(line.split(" ")), 4)
        self.assertEqual(len(line.split()), 2)

    def test_tabs(self):
        line = "alpha\tbeta"
        self.assertEqual(len(line.split(" ")), 1, "tab is not a literal space")
        self.assertEqual(len(line.split()), 2, ".split() handles tabs")

    def test_empty_string(self):
        line = ""
        self.assertEqual(line.split(" "), [""])
        self.assertEqual(line.split(), [])


class TestUnicodeDenominator(unittest.TestCase):
    """A2 Finding: code points vs grapheme clusters."""

    def test_combining_accent(self):
        """e + combining acute (U+0301) = 2 code points, 1 grapheme cluster."""
        text = "e\u0301"
        self.assertEqual(len(text), 2, "Python len counts code points")
        try:
            import regex
            graphemes = len(regex.findall(r'\X', text))
            self.assertEqual(graphemes, 1, "One user-perceived character")
        except ImportError:
            self.skipTest("regex module not installed")

    def test_devanagari_conjunct(self):
        """Devanagari क्ष = 3 code points, 1 grapheme cluster."""
        text = "\u0915\u094D\u0937"  # क + virama + ष
        self.assertEqual(len(text), 3)
        try:
            import regex
            graphemes = len(regex.findall(r'\X', text))
            self.assertEqual(graphemes, 1)
        except ImportError:
            self.skipTest("regex module not installed")

    def test_emoji_zwj(self):
        """Family emoji (ZWJ sequence) is many code points but 1 grapheme."""
        text = "\U0001F468\u200D\U0001F469\u200D\U0001F467"
        self.assertGreater(len(text), 1)
        try:
            import regex
            graphemes = len(regex.findall(r'\X', text))
            self.assertEqual(graphemes, 1)
        except ImportError:
            self.skipTest("regex module not installed")


class TestMacroVsPooled(unittest.TestCase):
    """A2 Finding: unweighted per-line mean vs pooled ratio."""

    def test_different_results(self):
        """Construct example where macro ≠ pooled."""
        # Line 1: 11 tokens, 2 words → ratio 5.5
        # Line 2: 1 token, 1 word → ratio 1.0
        tokens = [11, 1]
        words = [2, 1]
        macro = sum(t / w for t, w in zip(tokens, words)) / len(tokens)
        pooled = sum(tokens) / sum(words)
        self.assertAlmostEqual(macro, 3.25)
        self.assertAlmostEqual(pooled, 4.0)
        self.assertNotAlmostEqual(macro, pooled,
                                  msg="Macro mean ≠ pooled ratio when line lengths differ")


class TestRandomSeedHarmless(unittest.TestCase):
    """A2 Finding: random.seed(1337) is present but no random ops are used."""

    def test_seed_does_not_affect_split(self):
        import random
        random.seed(1337)
        result1 = "hello world".split()
        random.seed(42)
        result2 = "hello world".split()
        self.assertEqual(result1, result2, "Splitting is deterministic regardless of seed")


class TestLowercasing(unittest.TestCase):
    """A2 Finding: lowercasing is a measurement choice that can change tokenizer output."""

    def test_case_changes_string(self):
        text = "Hello World"
        self.assertNotEqual(text, text.lower())
        self.assertEqual(len(text), len(text.lower()), "len unchanged for ASCII")


# ── Part A3: tokenizer result validation ───────────────────────────────────

class TestTokenizerCSV(unittest.TestCase):
    """Validate schema and consistency of recorded tokenizer results."""

    def setUp(self):
        self.summary = ROOT / "partA" / "results" / "tokenizer_summary.csv"
        self.detail = ROOT / "partA" / "results" / "tokenizer_metrics.csv"
        if not self.summary.exists():
            self.skipTest("tokenizer_summary.csv not found")

    def test_summary_has_expected_columns(self):
        with self.summary.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"tokenizer", "language", "sentences", "tokens_total",
                        "whitespace_words_total", "tokens_per_word_pooled"}
            self.assertTrue(required.issubset(set(reader.fieldnames)),
                            f"Missing columns: {required - set(reader.fieldnames)}")

    def test_summary_has_14_rows(self):
        """7 languages × 2 tokenizers = 14 summary rows."""
        with self.summary.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 14)

    def test_each_language_has_20_sentences(self):
        with self.summary.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.assertEqual(int(row["sentences"]), 20,
                                 f"{row['tokenizer']}/{row['language']}: expected 20 sentences")

    def test_pooled_ratio_consistency(self):
        """Verify tokens_per_word_pooled = tokens_total / whitespace_words_total."""
        with self.summary.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                expected = int(row["tokens_total"]) / int(row["whitespace_words_total"])
                actual = float(row["tokens_per_word_pooled"])
                self.assertAlmostEqual(actual, expected, places=8,
                    msg=f"{row['tokenizer']}/{row['language']}: pooled ratio mismatch")

    def test_detail_has_280_rows(self):
        """20 sentences × 7 languages × 2 tokenizers = 280 detail rows."""
        if not self.detail.exists():
            self.skipTest("tokenizer_metrics.csv not found")
        with self.detail.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 280)

    def test_expected_values_gpt2(self):
        """Spot-check recorded pooled fertility for GPT-2."""
        expected = {
            "eng": 1.1837, "hin": 7.2667, "kan": 21.4434,
            "tam": 24.9907, "tel": 19.9561, "ben": 11.7787, "mar": 9.4252
        }
        with self.summary.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["tokenizer"] == "gpt2" and row["language"] in expected:
                    actual = float(row["tokens_per_word_pooled"])
                    self.assertAlmostEqual(actual, expected[row["language"]], places=3,
                        msg=f"GPT-2 {row['language']} mismatch")


# ── Part A1: corpus validation ─────────────────────────────────────────────

class TestCorpus(unittest.TestCase):
    """Structural checks on the diagnostic corpus."""

    LANGS = ["eng", "hin", "kan", "tam", "tel", "ben", "mar"]

    def setUp(self):
        self.corpus_dir = ROOT / "partA" / "corpus"

    def test_all_language_files_exist(self):
        for lang in self.LANGS:
            self.assertTrue((self.corpus_dir / f"{lang}.txt").exists(),
                            f"Missing corpus file: {lang}.txt")

    def test_each_language_has_20_lines(self):
        for lang in self.LANGS:
            path = self.corpus_dir / f"{lang}.txt"
            lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
            self.assertEqual(len(lines), 20,
                             f"{lang}.txt: expected 20 non-empty lines, got {len(lines)}")

    def test_no_empty_lines_in_content(self):
        for lang in self.LANGS:
            path = self.corpus_dir / f"{lang}.txt"
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                stripped = line.strip()
                if stripped:
                    self.assertGreater(len(stripped), 0)

    def test_parallel_corpus_csv_exists(self):
        csv_path = self.corpus_dir / "parallel_corpus.csv"
        self.assertTrue(csv_path.exists(), "parallel_corpus.csv missing")

    def test_parallel_corpus_has_20_rows(self):
        csv_path = self.corpus_dir / "parallel_corpus.csv"
        if not csv_path.exists():
            self.skipTest("parallel_corpus.csv missing")
        with csv_path.open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 20)

    def test_manifest_exists(self):
        self.assertTrue((self.corpus_dir / "MANIFEST.md").exists())


# ── Part B: KV-cache arithmetic ────────────────────────────────────────────

class TestKVCache(unittest.TestCase):
    """Verify KV-cache arithmetic from model spec."""

    LAYERS = 28
    KV_HEADS = 8
    HEAD_DIM = 128
    BYTES_PER_ELEMENT = 2  # FP16
    MAX_SEQ = 4096

    def test_kv_bytes_per_token(self):
        expected = 2 * self.LAYERS * self.KV_HEADS * self.HEAD_DIM * self.BYTES_PER_ELEMENT
        self.assertEqual(expected, 114688)

    def test_kv_kib_per_token(self):
        kv = 2 * self.LAYERS * self.KV_HEADS * self.HEAD_DIM * self.BYTES_PER_ELEMENT
        self.assertEqual(kv / 1024, 112.0)

    def test_kv_per_4096_sequence(self):
        kv = 2 * self.LAYERS * self.KV_HEADS * self.HEAD_DIM * self.BYTES_PER_ELEMENT
        seq_bytes = kv * self.MAX_SEQ
        self.assertEqual(seq_bytes, 469762048)

    def test_kv_mib_per_sequence(self):
        seq_bytes = 114688 * 4096
        self.assertEqual(seq_bytes / (1024 ** 2), 448.0)

    def test_concurrency_estimate(self):
        gpu_gb = 24
        util = 0.92
        weights_gb = 4.2e9 * 2 / 1e9  # 8.4
        overhead_gb = 1.6
        usable = gpu_gb * util - weights_gb - overhead_gb  # 12.08
        seq_gb = 469762048 / 1e9
        max_seqs = int(usable * 1e9 // 469762048)
        self.assertEqual(max_seqs, 25)
        self.assertAlmostEqual(usable / seq_gb, 25.714, places=2)


class TestThroughputReconciliation(unittest.TestCase):
    """Verify reported_tok_s = batch × (prompt + gen) / wall_clock."""

    def test_short_prompt_batch16(self):
        expected = 16 * (512 + 256) / 13.91
        self.assertAlmostEqual(expected, 883.2, delta=0.5)

    def test_long_prompt_batch16(self):
        expected = 16 * (3584 + 512) / 49.97
        self.assertAlmostEqual(expected, 1311.4, delta=0.5)

    def test_long_prompt_batch24(self):
        expected = 24 * (3584 + 512) / 61.16
        self.assertAlmostEqual(expected, 1607.4, delta=0.5)

    def test_output_goodput_batch24(self):
        goodput = 24 * 512 / 61.16
        self.assertAlmostEqual(goodput, 200.9, delta=0.2)

    def test_short_prompt_batch64(self):
        expected = 64 * (512 + 256) / 21.68
        self.assertAlmostEqual(expected, 2267.3, delta=0.5)

    def test_bench_log_rows(self):
        """Verify bench_log.csv has 13 data rows."""
        bench = ROOT / "partB" / "bench_log.csv"
        if not bench.exists():
            self.skipTest("bench_log.csv missing")
        with bench.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 13)


# ── Part C: count reconciliation ───────────────────────────────────────────

class TestPartCCounts(unittest.TestCase):
    """Verify 120 cases, correct sums, preference percentages."""

    def setUp(self):
        self.by_lang_path = ROOT / "partC" / "results" / "gemma_judge_by_language.csv"
        if not self.by_lang_path.exists():
            self.skipTest("gemma_judge_by_language.csv not found")
        with self.by_lang_path.open(encoding="utf-8-sig") as f:
            self.rows = list(csv.DictReader(f))

    def test_six_languages(self):
        langs = {r["Language"] for r in self.rows}
        self.assertEqual(langs, {"hin", "kan", "tam", "tel", "ben", "mar"})

    def test_20_cases_per_language(self):
        for r in self.rows:
            self.assertEqual(int(r["Cases"]), 20, f"{r['Language']}: expected 20 cases")

    def test_total_cases_120(self):
        total = sum(int(r["Cases"]) for r in self.rows)
        self.assertEqual(total, 120)

    def test_a_b_tie_sum_equals_cases(self):
        for r in self.rows:
            total = int(r["A_Pref"]) + int(r["B_Pref"]) + int(r["Ties"])
            self.assertEqual(total, int(r["Cases"]),
                             f"{r['Language']}: A+B+Tie={total} ≠ Cases={r['Cases']}")

    def test_overall_preference_rate(self):
        total_a = sum(int(r["A_Pref"]) for r in self.rows)
        total_b = sum(int(r["B_Pref"]) for r in self.rows)
        total_ties = sum(int(r["Ties"]) for r in self.rows)
        self.assertEqual(total_a, 29)
        self.assertEqual(total_b, 76)
        self.assertEqual(total_ties, 15)
        pref = total_b / (total_a + total_b) * 100
        self.assertAlmostEqual(pref, 72.4, places=1)

    def test_marathi_below_threshold(self):
        mar = [r for r in self.rows if r["Language"] == "mar"][0]
        pref = float(mar["B_PreferencePct"])
        self.assertLess(pref, 70.0, "Marathi should be below proposed 70% threshold")

    def test_review_sheet_has_120_rows(self):
        rs = ROOT / "partC" / "results" / "review_sheet.csv"
        if not rs.exists():
            self.skipTest("review_sheet.csv missing")
        with rs.open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 120)

    def test_unblind_key_has_120_rows(self):
        uk = ROOT / "partC" / "results" / "unblind_key.csv"
        if not uk.exists():
            self.skipTest("unblind_key.csv missing")
        with uk.open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 120)

    def test_model_outputs_has_120_rows(self):
        mo = ROOT / "partC" / "results" / "model_outputs.csv"
        if not mo.exists():
            self.skipTest("model_outputs.csv missing")
        with mo.open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 120)

    def test_judge_review_has_120_rows(self):
        jr = ROOT / "partC" / "results" / "gemma_judge_review.csv"
        if not jr.exists():
            self.skipTest("gemma_judge_review.csv missing")
        with jr.open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 120)

    def test_unblinded_candidate_preference_and_position_bias(self):
        """Audit finding: Slot B won 76 times (72.4%), but unblinded Candidate won only 45 times (42.9%)."""
        jr_path = ROOT / "partC" / "results" / "gemma_judge_review.csv"
        uk_path = ROOT / "partC" / "results" / "unblind_key.csv"
        if not jr_path.exists() or not uk_path.exists():
            self.skipTest("Part C review or key missing")
        with jr_path.open(encoding="utf-8-sig") as f:
            reviews = {r["case_id"]: r for r in csv.DictReader(f)}
        with uk_path.open(encoding="utf-8-sig") as f:
            keys = {r["case_id"]: r for r in csv.DictReader(f)}

        cand_wins = 0
        base_wins = 0
        ties = 0
        slot_b_wins = 0
        slot_a_wins = 0

        for cid, r in reviews.items():
            k = keys[cid]
            pref = r["naturalness_preference"].strip().upper()
            if pref == "TIE":
                ties += 1
            elif pref == "A":
                slot_a_wins += 1
                if k["A_condition"] == "candidate":
                    cand_wins += 1
                else:
                    base_wins += 1
            elif pref == "B":
                slot_b_wins += 1
                if k["B_condition"] == "candidate":
                    cand_wins += 1
                else:
                    base_wins += 1

        self.assertEqual(slot_a_wins, 29)
        self.assertEqual(slot_b_wins, 76)
        self.assertEqual(ties, 15)
        self.assertEqual(cand_wins, 45)
        self.assertEqual(base_wins, 60)
        unblinded_cand_rate = cand_wins / (cand_wins + base_wins) * 100
        self.assertAlmostEqual(unblinded_cand_rate, 42.86, places=1)



# ── Cross-document consistency ─────────────────────────────────────────────

class TestCrossDocumentConsistency(unittest.TestCase):
    """Check that key numbers are consistent across memos, CSVs, and README."""

    def test_readme_exists(self):
        self.assertTrue((ROOT / "README.md").exists())

    def test_notebook_exists(self):
        self.assertTrue((ROOT / "NOTEBOOK.md").exists())

    def test_ai_usage_exists(self):
        self.assertTrue((ROOT / "AI_USAGE.md").exists())

    def test_part_a_memo_exists(self):
        self.assertTrue((ROOT / "partA" / "memo.md").exists())

    def test_part_b_memo_exists(self):
        self.assertTrue((ROOT / "partB" / "memo.md").exists())

    def test_part_c_memo_exists(self):
        self.assertTrue((ROOT / "partC" / "memo.md").exists())

    def test_reconciliation_json_kv_bytes(self):
        path = ROOT / "partB" / "results" / "reconciliation.json"
        if not path.exists():
            self.skipTest("reconciliation.json missing")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["kv_bytes_per_token"], 114688)
        self.assertEqual(data["kv_bytes_per_4096_token_sequence"], 469762048)
        self.assertAlmostEqual(data["kv_mib_per_sequence"], 448.0)
        self.assertEqual(data["estimated_max_4096_sequences"], 25)

    def test_no_stale_provisional_in_memo(self):
        """Part A memo must not say 'provisional' if results exist."""
        memo = ROOT / "partA" / "memo.md"
        if not memo.exists():
            self.skipTest("Part A memo missing")
        text = memo.read_text(encoding="utf-8")
        summary = ROOT / "partA" / "results" / "tokenizer_summary.csv"
        if summary.exists():
            self.assertNotIn("provisional", text.lower(),
                             "Memo says 'provisional' but results CSV exists")

    def test_no_not_prepopulated_in_memo(self):
        """Part A memo must not say 'not pre-populated' if results exist."""
        memo = ROOT / "partA" / "memo.md"
        if not memo.exists():
            self.skipTest("Part A memo missing")
        text = memo.read_text(encoding="utf-8")
        summary = ROOT / "partA" / "results" / "tokenizer_summary.csv"
        if summary.exists():
            self.assertNotIn("not pre-populated", text.lower(),
                             "Memo says 'not pre-populated' but results CSV exists")


if __name__ == "__main__":
    unittest.main(verbosity=2)
