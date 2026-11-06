import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("auto_promote_gitops.py")
SPEC = importlib.util.spec_from_file_location("auto_promote_gitops", SCRIPT)
assert SPEC and SPEC.loader
PROMOTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROMOTER)


class AutoPromoteTests(unittest.TestCase):
    def test_selects_newest_successful_complete_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release = root / "apps/demo/release.yaml"
            release.parent.mkdir(parents=True)
            release.write_text("  image: ghcr.io/example/demo:1.0.0\n")
            config = [{
                "repository": "example/demo",
                "workflow": "pipeline.yml",
                "releases": [{"file": "apps/demo/release.yaml", "image": "ghcr.io/example/demo"}],
            }]
            PROMOTER.validate_config(config, root)
            tags = [((1, 2, 0), "v1.2.0", "sha2"), ((1, 1, 0), "v1.1.0", "sha1")]
            with patch.object(PROMOTER, "stable_tags", return_value=tags), \
                 patch.object(PROMOTER, "successful_release", side_effect=[False, True]), \
                 patch.object(PROMOTER, "image_exists", return_value=True):
                changes = PROMOTER.promote(config, root, "token")
            self.assertEqual(changes, ["apps/demo/release.yaml: 1.1.0"])
            self.assertIn("ghcr.io/example/demo:1.1.0", release.read_text())

    def test_multi_image_release_waits_for_every_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            releases = []
            for name in ("one", "two"):
                path = root / f"apps/demo/release-{name}.yaml"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"  image: ghcr.io/example/{name}:1.0.0\n")
                releases.append({"file": f"apps/demo/release-{name}.yaml", "image": f"ghcr.io/example/{name}"})
            config = [{"repository": "example/demo", "workflow": "ci.yml", "releases": releases}]
            with patch.object(PROMOTER, "stable_tags", return_value=[((1, 1, 0), "v1.1.0", "sha")]), \
                 patch.object(PROMOTER, "successful_release", return_value=True), \
                 patch.object(PROMOTER, "image_exists", side_effect=[True, False]):
                self.assertEqual(PROMOTER.promote(config, root, "token"), [])
            for release in releases:
                self.assertIn(":1.0.0", (root / release["file"]).read_text())

    def test_rejects_invalid_and_duplicate_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "apps/demo/release.yaml"
            target.parent.mkdir(parents=True)
            target.write_text("  image: ghcr.io/example/demo:1.0.0\n")
            source = {"repository": "example/demo", "workflow": "ci.yml", "releases": [
                {"file": "apps/demo/release.yaml", "image": "ghcr.io/example/demo"}
            ]}
            with self.assertRaises(ValueError):
                PROMOTER.validate_config([source, source], root)
            source["releases"][0]["file"] = "../release.yaml"
            with self.assertRaises(ValueError):
                PROMOTER.validate_config([source], root)

    def test_stable_tags_only_include_newer_versions(self) -> None:
        tags = [{"name": name, "commit": {"sha": name}} for name in
                ("v1.0.0", "v1.2.0-rc1", "v1.1.0", "v2.0.0")]
        with patch.object(PROMOTER, "github", return_value=tags):
            result = PROMOTER.stable_tags("example/demo", (1, 0, 0), "token")
        self.assertEqual([item[1] for item in result], ["v2.0.0", "v1.1.0"])


if __name__ == "__main__":
    unittest.main()
