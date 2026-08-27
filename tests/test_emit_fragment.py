import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


HOSTS = (
    "x86_64-pc-linux-gnu",
    "aarch64-linux-gnu",
    "x86_64-apple-darwin",
    "arm64-apple-darwin",
    "x86_64-mingw32",
    "i686-mingw32",
)


class EmitFragmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.dist = self.root / "dist"
        self.versions = self.root / "versions"
        for host in HOSTS:
            host_dir = self.dist / host
            host_dir.mkdir(parents=True)
            archive = host_dir / f"minichlink-test-{host}.zip"
            archive.write_bytes(host.encode())
            record = {
                "host": host,
                "archiveFileName": archive.name,
                "runner": "test-runner",
                "cc": "cc",
                "ccVersion": "cc test",
                "cflags": "-O2",
                "ldflags": "-static",
                "dynamicDependencies": [],
                "binaryFormat": "test binary",
                "executionChecks": "skipped: test fixture",
            }
            (host_dir / "build.json").write_text(json.dumps(record))
        self.source_bundle = self.dist / "minichlink-test-sources.tar.gz"
        self.source_bundle.write_bytes(b"sources")

    def tearDown(self):
        self.temp.cleanup()

    def command(self, revision=1, version="2026.8.24-g6c4dd53-r1"):
        script = pathlib.Path(__file__).parents[1] / "emit_fragment.py"
        return [
            sys.executable,
            str(script),
            "--version",
            version,
            "--upstream-sha",
            "6c4dd539a422aaea0ba6ce45630eed1b49728579",
            "--upstream-date",
            "2026-08-24T20:54:03Z",
            "--builder-sha",
            "1234567890abcdef1234567890abcdef12345678",
            "--build-revision",
            str(revision),
            "--libusb-version",
            "1.0.29",
            "--libusb-sha256",
            "5977fc950f8d1395ccea9bd48c06b3f808fd3c2c961b44b0c2e6e29fc3a70a85",
            "--repo",
            "example/build-minichlink",
            "--source-bundle",
            str(self.source_bundle),
            "--dist",
            str(self.dist),
            "--versions",
            str(self.versions),
        ]

    def test_generates_fragment_and_complete_record(self):
        subprocess.run(self.command(), check=True, capture_output=True, text=True)
        record = json.loads(
            (self.versions / "2026.8.24-g6c4dd53-r1.json").read_text()
        )
        self.assertEqual(record["buildRevision"], 1)
        self.assertEqual(len(record["systems"]), 6)
        self.assertEqual(len(record["builds"]), 6)
        self.assertEqual(record["builds"][0]["executionChecks"], "skipped: test fixture")
        self.assertIn("sourceBundle", record)

    def test_rejects_revision_suffix_mismatch(self):
        result = subprocess.run(
            self.command(revision=2), capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("suffix must match", result.stderr)

    def test_rejects_missing_host(self):
        missing = self.dist / HOSTS[-1]
        for child in missing.iterdir():
            child.unlink()
        missing.rmdir()
        result = subprocess.run(self.command(), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no build for", result.stderr)


if __name__ == "__main__":
    unittest.main()
