"""Regression coverage for the Bigao usability and execution fixes."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from istream.__main__ import main
from istream.catalog import Catalog
from istream.cost import video_cost
from istream.environment import inspect_environment
from istream.lipsync import NotConfigured, make_jobs, runs

ROOT = Path(__file__).resolve().parents[1]


class TestCatalogConflicts(unittest.TestCase):
    def test_duplicates_do_not_silently_replace_assets(self):
        for plates, shots, message in (([{"id": "P1"}, {"id": "P1"}], [], "duplicate plate id: P1"),
                                       ([], [{"id": "s1"}, {"id": "s1"}], "duplicate shot id: s1")):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                Catalog(plates, shots, ".")


class TestRouting(unittest.TestCase):
    def test_gaps_and_hidden_clips_are_not_billed_as_speech(self):
        timeline = {"host": [
            {"shot": "s1", "layout": "full", "rec": {"in": 0, "out": 2}},
            {"shot": "s2", "layout": "full", "rec": {"in": 5, "out": 7}},
            {"shot": "s3", "layout": "hidden", "rec": {"in": 7, "out": 9}},
            {"shot": "s4", "layout": "full", "rec": {"in": 9, "out": 10}},
        ]}
        self.assertEqual([(r["in"], r["out"]) for r in runs(timeline)], [(0, 2), (5, 7), (9, 10)])

    def test_unknown_engine_rejected_before_planning(self):
        with self.assertRaisesRegex(ValueError, "unknown lip-sync engine"):
            make_jobs({}, None, engine_override="typo")

    def test_invalid_cost_inputs_fail_clearly(self):
        for invalid in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "finite positive"):
                video_cost({"duration": 10}, lifetime_minutes=invalid)
        with self.assertRaisesRegex(ValueError, "duration"):
            video_cost({"duration": 0})


class TestCLI(unittest.TestCase):
    def invoke(self, args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                main(args)
            except SystemExit as exc:
                return exc.code, output.getvalue()
        return 0, output.getvalue()

    def test_alias_and_version(self):
        result = subprocess.run([sys.executable, "-m", "bigao_shuziren", "--version"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "bigao-shuziren 1.4.0")

    def test_invalid_render_parameters_stop_before_io(self):
        base = ["render", "missing.json", "--cat", "missing-plates.json", "--jobs", "missing-jobs.json", "--out", "out.mp4"]
        for flag, value in (("--scale", "nan"), ("--scale", "0"), ("--workers", "0"), ("--crf", "52"), ("--engine", "typo")):
            with self.subTest(flag=flag, value=value):
                code, text = self.invoke(base + [flag, value])
                self.assertEqual(code, 2)
                self.assertNotIn("Traceback", text)
                self.assertNotIn("No such file", text)

    def test_required_action_arguments_are_reported(self):
        for args in (["catalog", "build-spec"], ["catalog", "merge-review"], ["catalog", "stats"],
                     ["lipsync", "plan", "t.json", "--cat", "p.json"], ["lipsync", "run", "t.json", "--cat", "p.json"]):
            with self.subTest(args=args):
                code, text = self.invoke(args)
                self.assertEqual(code, 2)
                self.assertIn("requires", text)

    def test_missing_file_has_actionable_error(self):
        code, text = self.invoke(["catalog", "validate", "--cat", "nonexistent.json"])
        self.assertEqual(code, 2)
        self.assertIn("error:", text)
        self.assertNotIn("Traceback", text)

    def test_unconfigured_lipsync_exits_unsuccessfully(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "jobs.json"
            path.write_text(json.dumps({"jobs": [{"id": "j01"}]}), encoding="utf-8")
            with patch("istream.__main__._cat"), patch("istream.__main__.lsm.run_job", side_effect=NotConfigured("template adapter")):
                code, text = self.invoke(["lipsync", "run", "unused.json", "--cat", "p.json", "--jobs", str(path)])
            self.assertEqual(code, 2)
            self.assertIn("NOT run", text)

    def test_unconfigured_engine_cannot_continue_to_composite(self):
        with tempfile.TemporaryDirectory() as td:
            timeline = Path(td) / "timeline.json"
            jobs = Path(td) / "jobs.json"
            timeline.write_text("{}", encoding="utf-8")
            jobs.write_text(json.dumps({"jobs": [{"id": "j01"}]}), encoding="utf-8")
            with patch("istream.__main__._cat"), patch("istream.render.Renderer") as renderer, \
                    patch("istream.__main__.lsm.run_job", side_effect=NotConfigured("template adapter")):
                code, _ = self.invoke(["render", str(timeline), "--cat", "p.json", "--jobs", str(jobs), "--out", "out.mp4", "--engine", "latentsync"])
                renderer.return_value.stage_composite.assert_not_called()
                self.assertEqual(code, 2)

    def test_doctor_json_matches_exit_status(self):
        code, text = self.invoke(["doctor", "--json"])
        self.assertEqual(code, 0)
        report = json.loads(text)
        self.assertTrue(report["ok"])

    def test_missing_media_tools_reported_without_spawning_them(self):
        with patch("istream.environment.shutil.which", return_value=None), patch("istream.environment.subprocess.run") as run:
            report = inspect_environment(render=True)
        self.assertFalse(report["ok"])
        run.assert_not_called()
        missing = {c["name"] for c in report["checks"] if c["required"] and not c["ok"]}
        self.assertTrue({"ffmpeg", "ffprobe"}.issubset(missing))


if __name__ == "__main__":
    unittest.main()
