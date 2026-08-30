from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ACTION_SCRIPT = (
    Path(__file__).resolve().parents[2] / "actions" / "promote-gitops" / "promote.py"
)


def git(directory: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(directory), *args], text=True
    ).strip()


class PromoteGitOpsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.remote = self.root / "remote.git"
        self.repository = self.root / "repository"
        self.output = self.root / "output"

        subprocess.run(
            ["git", "init", "--bare", "--initial-branch=main", str(self.remote)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "init", "--initial-branch=main", str(self.repository)],
            check=True,
            capture_output=True,
        )
        git(self.repository, "config", "user.name", "test")
        git(self.repository, "config", "user.email", "test@example.com")

        release_file = self.repository / "deploy" / "01" / "aegis" / "release.yaml"
        release_file.parent.mkdir(parents=True)
        release_file.write_text(
            "apiVersion: apps/v1\n"
            "kind: Deployment\n"
            "spec:\n"
            "  template:\n"
            "    spec:\n"
            "      containers:\n"
            "        - name: aegis\n"
            "          image: ghcr.io/heliantheons/aegis:1.0.0\n"
        )
        git(self.repository, "add", ".")
        git(self.repository, "commit", "-m", "initial")
        git(self.repository, "remote", "add", "origin", str(self.remote))
        git(self.repository, "push", "-u", "origin", "main")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_action(self, updates: str, version: str = "2.0.0") -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "GITHUB_OUTPUT": str(self.output),
                "PROMOTION_BRANCH": "main",
                "PROMOTION_UPDATES": updates,
                "PROMOTION_VERSION": version,
            }
        )
        return subprocess.run(
            ["python3", str(ACTION_SCRIPT)],
            cwd=self.repository,
            env=environment,
            text=True,
            capture_output=True,
        )

    def test_promotes_and_is_idempotent(self) -> None:
        mapping = "deploy/01/aegis/release.yaml=ghcr.io/heliantheons/aegis"

        first = self.run_action(mapping)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("changed=true", self.output.read_text())
        self.assertIn(
            "ghcr.io/heliantheons/aegis:2.0.0",
            git(self.remote, "show", "main:deploy/01/aegis/release.yaml"),
        )
        promoted_commit = git(self.remote, "rev-parse", "main")

        self.output.unlink()
        second = self.run_action(mapping)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("changed=false", self.output.read_text())
        self.assertEqual(git(self.remote, "rev-parse", "main"), promoted_commit)

    def test_rejects_unsafe_or_malformed_updates(self) -> None:
        invalid_updates = (
            "../release.yaml=ghcr.io/heliantheons/aegis",
            "deploy/01/aegis/config.yaml=ghcr.io/heliantheons/aegis",
            "deploy/01/aegis/release.yaml=docker.io/heliantheons/aegis",
            "deploy/01/aegis/release.yaml=",
        )

        for mapping in invalid_updates:
            with self.subTest(mapping=mapping):
                result = self.run_action(mapping)
                self.assertNotEqual(result.returncode, 0)
        self.assertEqual(git(self.remote, "rev-list", "--count", "main"), "1")


if __name__ == "__main__":
    unittest.main()
