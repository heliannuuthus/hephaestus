#!/usr/bin/env python3
"""Advance GitOps release files after successful, published source tags."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


VERSION = re.compile(r"v?([0-9]+)\.([0-9]+)\.([0-9]+)\Z")
REPOSITORY = re.compile(r"[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\Z")
RELEASE_FILE = re.compile(r"apps/[a-z0-9-]+/release(?:-[a-z0-9-]+)?\.yaml\Z")
IMAGE = re.compile(r"ghcr\.io/[a-z0-9._-]+/[a-z0-9._-]+\Z")
ACCEPT_MANIFEST = ",".join(
    (
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)


def version(value: str) -> tuple[int, int, int] | None:
    match = VERSION.fullmatch(value)
    return tuple(map(int, match.groups())) if match else None


def request(
    url: str,
    *,
    token: str = "",
    method: str = "GET",
    accept: str = "application/vnd.github+json",
):
    headers = {"Accept": accept, "User-Agent": "hephaestus-gitops-promoter"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=headers, method=method), timeout=30
    )


def github(path: str, token: str) -> dict | list:
    with request(f"https://api.github.com/{path}", token=token) as response:
        return json.load(response)


def stable_tags(
    repository: str, current: tuple[int, int, int], token: str
) -> list[tuple[tuple[int, int, int], str, str]]:
    candidates = []
    for page in range(1, 11):
        tags = github(f"repos/{repository}/tags?per_page=100&page={page}", token)
        if not tags:
            break
        for tag in tags:
            parsed = version(tag["name"])
            if parsed and tag["name"].startswith("v") and parsed > current:
                candidates.append((parsed, tag["name"], tag["commit"]["sha"]))
        if len(tags) < 100:
            break
    else:
        raise RuntimeError(f"More than 1000 tags in {repository}; refusing an incomplete scan")
    return sorted(candidates, reverse=True)


def successful_release(repository: str, workflow: str, tag: str, sha: str, token: str) -> bool:
    query = urllib.parse.urlencode(
        {"branch": tag, "event": "push", "status": "success", "per_page": 100}
    )
    path = (
        f"repos/{repository}/actions/workflows/"
        f"{urllib.parse.quote(workflow, safe='')}/runs?{query}"
    )
    runs = github(path, token)["workflow_runs"]
    return any(
        run["head_branch"] == tag
        and run["head_sha"] == sha
        and run["conclusion"] == "success"
        for run in runs
    )


def image_exists(image: str, tag: str) -> bool:
    name = image.removeprefix("ghcr.io/")
    query = urllib.parse.urlencode({"scope": f"repository:{name}:pull", "service": "ghcr.io"})
    with request(f"https://ghcr.io/token?{query}", accept="application/json") as response:
        token = json.load(response)["token"]
    try:
        with request(
            f"https://ghcr.io/v2/{name}/manifests/{tag}",
            token=token,
            method="HEAD",
            accept=ACCEPT_MANIFEST,
        ) as response:
            return response.status == 200
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise


def release_pattern(image: str) -> re.Pattern[str]:
    return re.compile(
        rf"^(\s*image:\s*){re.escape(image)}:([0-9]+\.[0-9]+\.[0-9]+)\s*$",
        re.MULTILINE,
    )


def read_release(path: Path, image: str) -> tuple[str, tuple[int, int, int]]:
    source = path.read_text(encoding="utf-8")
    matches = list(release_pattern(image).finditer(source))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {image} release in {path}, found {len(matches)}")
    current = version(matches[0].group(2))
    assert current is not None
    return source, current


def validate_config(config: object, root: Path) -> list[dict]:
    if not isinstance(config, list) or not config:
        raise ValueError("Promotion config must be a non-empty array")
    files = set()
    for source in config:
        if (
            not isinstance(source, dict)
            or not isinstance(source.get("repository"), str)
            or not REPOSITORY.fullmatch(source["repository"])
        ):
            raise ValueError("Each source requires a valid repository")
        if not isinstance(source.get("workflow"), str) or not re.fullmatch(
            r"[a-zA-Z0-9_.-]+\.ya?ml", source["workflow"]
        ):
            raise ValueError(f"Invalid workflow for {source['repository']}")
        if not isinstance(source.get("releases"), list) or not source["releases"]:
            raise ValueError(f"No release mappings for {source['repository']}")
        for release in source["releases"]:
            if (
                not isinstance(release, dict)
                or not isinstance(release.get("file"), str)
                or not RELEASE_FILE.fullmatch(release["file"])
                or not isinstance(release.get("image"), str)
                or not IMAGE.fullmatch(release["image"])
            ):
                raise ValueError(f"Invalid release mapping for {source['repository']}")
            if release["file"] in files:
                raise ValueError(f"Duplicate release file: {release['file']}")
            files.add(release["file"])
            if not (root / release["file"]).is_file():
                raise ValueError(f"Release file does not exist: {release['file']}")
    return config


def promote(config: list[dict], root: Path, token: str) -> list[str]:
    changes = []
    for source in config:
        releases = []
        current_versions = set()
        for release in source["releases"]:
            path = root / release["file"]
            content, current = read_release(path, release["image"])
            releases.append((release, path, content))
            current_versions.add(current)
        if len(current_versions) != 1:
            raise RuntimeError(f"Release versions disagree for {source['repository']}")
        current = current_versions.pop()
        for candidate, tag, sha in stable_tags(source["repository"], current, token):
            if not successful_release(source["repository"], source["workflow"], tag, sha, token):
                continue
            version_tag = ".".join(map(str, candidate))
            if not all(image_exists(release["image"], version_tag) for release, _, _ in releases):
                print(f"Waiting for all {source['repository']} images at {version_tag}")
                continue
            for release, path, content in releases:
                updated, count = release_pattern(release["image"]).subn(
                    lambda match: f"{match.group(1)}{release['image']}:{version_tag}", content
                )
                assert count == 1
                path.write_text(updated, encoding="utf-8")
                changes.append(f"{release['file']}: {version_tag}")
            break
    return changes


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: auto_promote_gitops.py <config.json>")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    config_path = Path(sys.argv[1]).resolve()
    root = Path.cwd().resolve()
    config = validate_config(json.loads(config_path.read_text(encoding="utf-8")), root)
    changes = promote(config, root, token)
    print("\n".join(changes) if changes else "No promotable releases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
