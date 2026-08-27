import json
import pathlib
import subprocess
import tempfile
import unittest

import resolve_version


class ResolveVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.temp.name)
        self.upstream = root / "upstream"
        self.versions = root / "versions"
        self.upstream.mkdir()
        subprocess.run(["git", "init", "-q", self.upstream], check=True)
        subprocess.run(
            ["git", "-C", self.upstream, "config", "user.name", "Test"], check=True
        )
        subprocess.run(
            ["git", "-C", self.upstream, "config", "user.email", "test@example.com"],
            check=True,
        )
        (self.upstream / "source").write_text("one\n")
        subprocess.run(["git", "-C", self.upstream, "add", "source"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                self.upstream,
                "commit",
                "-q",
                "-m",
                "initial",
                "--date=2026-08-24T20:54:03Z",
            ],
            check=True,
            env={
                **__import__("os").environ,
                "GIT_COMMITTER_DATE": "2026-08-24T20:54:03Z",
            },
        )

    def tearDown(self):
        self.temp.cleanup()

    def write_record(self, revision, builder="builder-one"):
        self.versions.mkdir(exist_ok=True)
        sha = resolve_version.git(self.upstream, "rev-parse", "HEAD")
        record = {
            "version": f"2026.8.24-g{sha[:7]}-r{revision}",
            "upstreamCommit": sha,
            "builderCommit": builder,
            "buildRevision": revision,
        }
        (self.versions / f"record-{revision}.json").write_text(json.dumps(record))

    def test_first_build_is_r1(self):
        result = resolve_version.resolve(
            self.upstream, self.versions, "builder-one", "schedule"
        )
        self.assertTrue(result["should_build"])
        self.assertEqual(result["build_revision"], 1)
        self.assertRegex(result["version"], r"^2026\.8\.24-g[0-9a-f]{7}-r1$")

    def test_schedule_skips_existing_upstream(self):
        self.write_record(1)
        result = resolve_version.resolve(
            self.upstream, self.versions, "builder-two", "schedule"
        )
        self.assertFalse(result["should_build"])

    def test_recipe_change_increments_revision(self):
        self.write_record(1)
        result = resolve_version.resolve(
            self.upstream, self.versions, "builder-two", "push"
        )
        self.assertTrue(result["should_build"])
        self.assertEqual(result["build_revision"], 2)
        self.assertTrue(result["version"].endswith("-r2"))

    def test_identical_inputs_are_skipped(self):
        self.write_record(1)
        result = resolve_version.resolve(
            self.upstream, self.versions, "builder-one", "manual"
        )
        self.assertFalse(result["should_build"])


if __name__ == "__main__":
    unittest.main()
