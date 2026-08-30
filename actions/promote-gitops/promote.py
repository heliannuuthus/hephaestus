from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
RELEASE_FILE_PATTERN = re.compile(r"^release(?:-[a-z0-9-]+)?\.yaml$")
PATH_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
IMAGE_PATTERN = re.compile(r"^ghcr\.io/[a-z0-9._-]+/[a-z0-9._-]+$")


class PromotionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Update:
    path: Path
    image: str


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        capture_output=True,
    )


def validate_branch(branch: str) -> None:
    result = git("check-ref-format", "--branch", branch, check=False)
    if result.returncode != 0:
        raise PromotionError(f"invalid GitOps branch: {branch}")


def parse_updates(raw_updates: str, repository_root: Path) -> list[Update]:
    updates: list[Update] = []
    for raw_line in raw_updates.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        raw_path, separator, image = line.partition("=")
        if not separator or not raw_path or not image:
            raise PromotionError("each update must be a release-file=image mapping")
        if raw_path.startswith("/") or "\\" in raw_path:
            raise PromotionError(f"update target must be a relative POSIX path: {raw_path}")

        parts = raw_path.split("/")
        if len(parts) < 2:
            raise PromotionError(f"update target must be below a repository directory: {raw_path}")
        if any(
            not part
            or part in {".", ".."}
            or not PATH_SEGMENT_PATTERN.fullmatch(part)
            for part in parts
        ):
            raise PromotionError(f"unsafe update target: {raw_path}")
        if not RELEASE_FILE_PATTERN.fullmatch(parts[-1]):
            raise PromotionError(f"update target must end in release*.yaml: {raw_path}")
        if not IMAGE_PATTERN.fullmatch(image):
            raise PromotionError(f"unsupported image name: {image}")

        relative_path = Path(PurePosixPath(raw_path))
        target = repository_root / relative_path
        tracked = git("ls-files", "--error-unmatch", "--", raw_path, check=False)
        if not target.is_file() or tracked.returncode != 0:
            raise PromotionError(f"release file must exist and be tracked: {raw_path}")
        try:
            target.resolve(strict=True).relative_to(repository_root)
        except ValueError as error:
            raise PromotionError(
                f"release file resolves outside the repository: {raw_path}"
            ) from error

        updates.append(Update(path=relative_path, image=image))

    if not updates:
        raise PromotionError("at least one release-file=image mapping is required")
    return updates


def update_release_files(
    updates: list[Update], version: str, repository_root: Path
) -> list[str]:
    content_by_path: dict[Path, str] = {}
    for update in updates:
        target = repository_root / update.path
        source = content_by_path.get(update.path, target.read_text())
        pattern = re.compile(
            rf"^(\s+image:\s+){re.escape(update.image)}:[^\s]+\s*$",
            re.MULTILINE,
        )
        rendered, count = pattern.subn(
            rf"\g<1>{update.image}:{version}", source
        )
        if count != 1:
            raise PromotionError(
                f"expected exactly one {update.image} image in {update.path}, found {count}"
            )
        content_by_path[update.path] = rendered

    for path, content in content_by_path.items():
        (repository_root / path).write_text(content)
    return [path.as_posix() for path in content_by_path]


def write_outputs(changed: bool, commit_sha: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a") as output:
        output.write(f"changed={str(changed).lower()}\n")
        output.write(f"commit-sha={commit_sha}\n")


def promote(version: str, raw_updates: str, branch: str) -> None:
    if not VERSION_PATTERN.fullmatch(version):
        raise PromotionError("only stable semantic versions can be promoted")
    validate_branch(branch)

    repository_root = Path(git("rev-parse", "--show-toplevel").stdout.strip()).resolve()
    updates = parse_updates(raw_updates, repository_root)
    files = update_release_files(updates, version, repository_root)

    diff = git("diff", "--quiet", "--", *files, check=False)
    if diff.returncode == 0:
        commit_sha = git("rev-parse", "HEAD").stdout.strip()
        print(f"Desired state already references {version}")
        write_outputs(False, commit_sha)
        return
    if diff.returncode != 1:
        raise PromotionError("unable to inspect desired-state changes")

    git("config", "user.name", "github-actions[bot]")
    git(
        "config",
        "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com",
    )
    git("add", "--", *files)
    git("commit", "-m", f"chore(release): promote desired state to {version}")
    git("push", "origin", f"HEAD:{branch}")
    write_outputs(True, git("rev-parse", "HEAD").stdout.strip())


def main() -> int:
    try:
        promote(
            version=os.environ.get("PROMOTION_VERSION", ""),
            raw_updates=os.environ.get("PROMOTION_UPDATES", ""),
            branch=os.environ.get("PROMOTION_BRANCH", "main"),
        )
    except (PromotionError, subprocess.CalledProcessError) as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
