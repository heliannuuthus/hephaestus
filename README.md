<h1 align="center">⚒️ hephaestus</h1>

Reusable GitHub Actions workflows and composite actions for **Golang**, **Rust**, **Node.js**, and **Tauri** projects.

## Architecture

```
actions/                          # Composite Actions (reusable steps)
├── setup-go/action.yml           # Go + cache + golangci-lint/gosec
├── setup-rust/action.yml         # Rust toolchain + cache + cargo tools
├── setup-node/action.yml         # Node + pnpm + cache (backend)
├── setup-pnpm/action.yml         # Node + pnpm + cache + eslint/prettier (frontend)
├── version/action.yml            # Unified version/project name extraction
└── containerize/action.yml       # Docker build + push to GHCR

.github/workflows/                # Reusable Workflows (job orchestration)
├── ci-golang.yml                 # setup → lint → security → build
├── ci-rust.yml                   # setup → lint → build
├── ci-node.yml                   # setup → lint → build (backend)
├── ci-frontend.yml               # setup → lint/type-check → build/test/pack
├── ci-release-node-package.yml    # pnpm pack → GitHub Release asset
├── ci-compose-integration.yml    # submodules → scripts → Compose validation
├── ci-deploy-pages.yml           # pnpm build → GitHub Pages deploy
├── ci-containerize-source.yml    # source tree → one or more GHCR images
├── ci-promote-gitops.yml         # stable image → private overlay update
├── ci-rust-tauri.yml             # multi-platform Tauri build
└── ci-containerize.yml           # Docker containerization
```

## Usage

### Compose integration repository

```yaml
jobs:
  ci:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-compose-integration.yml@main
    permissions:
      contents: read
    with:
      workdir: "./"
```

The workflow checks out submodules, installs `scripts/requirements.txt` when
present, runs `scripts/test_*.py`, and validates the development and production
Compose overlays.

### Golang

```yaml
jobs:
  ci:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-golang.yml@main
    permissions:
      contents: read
      packages: write
    with:
      workdir: "./"
      ENTRANCE: cmd/main.go

  containerize:
    needs: [ci]
    uses: heliannuuthus/hephaestus/.github/workflows/ci-containerize.yml@main
    permissions:
      contents: read
      packages: write
    with:
      version: ${{ needs.ci.outputs.version }}
      targets: "build"
```

### Rust

```yaml
jobs:
  ci:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-rust.yml@main
    permissions:
      contents: read
      packages: write
    with:
      workdir: "./"
```

### Frontend (pnpm + eslint + prettier)

```yaml
jobs:
  ci:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-frontend.yml@main
    with:
      workdir: "./"
      type-check: type-check
      pack: true
```

`type-check`, `test`, and `pack` are opt-in so applications and publishable
packages can share the same workflow. `type-check` and `test` name package
scripts; `pack: true` validates the publishable tarball with `pnpm pack`.

### Frontend GitHub Pages Deploy

```yaml
jobs:
  deploy:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-deploy-pages.yml@main
    permissions:
      contents: read
      pages: write
      id-token: write
    with:
      workdir: "./"
      artifact-path: dist
```

### Frontend container delivery

Frontend repositories can declare one or more source-built images in
`.hephaestus/containers.json`:

```json
[
  {
    "image": "ghcr.io/heliannuuthus/example-web",
    "context": ".",
    "dockerfile": "Dockerfile",
    "buildArgs": "APP=portal"
  }
]
```

The caller remains a thin reusable-workflow invocation:

```yaml
jobs:
  ci:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-frontend.yml@main

  containerize:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [ci]
    uses: heliannuuthus/hephaestus/.github/workflows/ci-containerize-source.yml@main
    permissions:
      contents: read
      packages: write
    with:
      manifest: .hephaestus/containers.json
      version: ${{ needs.ci.outputs.version }}
```

Source container workflows and callers that set `release-tags: true` publish
the exact release version plus a `sha-*` traceability tag. Existing artifact
callers retain their legacy prerelease tagging until they opt in. New release
callers invoke delivery only for `v*` tags.

### GitOps promotion

`ci-promote-gitops.yml` accepts a stable semantic version and a constrained
list of `<component>/overlay/release*.yaml=ghcr.io/<owner>/<image>` mappings.
It rejects paths outside component overlays and never edits component-owned
`deploy/` contracts. The desired-state repository defaults to
`heliantheons/applications`.

Callers must make promotion depend on successful CI and image publishing. New
callers pass `gitops_app_id` and forward `gitops_app_private_key`; the reusable
workflow mints a repository-scoped GitHub App installation token that expires
after one hour, requests only `contents: write`, and is revoked by the action
when the job finishes. The legacy `gitops_token` secret remains as a deprecated
fallback for existing callers. Normal branch builds and `sha-*` tags are not
promotable.

### Node.js Backend

```yaml
jobs:
  ci:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-node.yml@main
    with:
      workdir: "./"
      format-check: format:check
      type-check: type-check
      test: test
      pack: true
```

### Node.js Package Publish

```yaml
jobs:
  publish:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-publish-node.yml@main
    permissions:
      contents: read
      id-token: write
```

The publish job uses the caller repository's `publish` environment. For a new
package, temporarily add `NPM_TOKEN` to that environment to bootstrap the first
release. Afterward, configure npm Trusted Publishing with the caller workflow
filename and the `publish` environment, then remove the token. When no token is
present, npm authenticates through GitHub OIDC.

### Node.js Package Tarball Release

```yaml
jobs:
  release-package:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [ci]
    uses: heliannuuthus/hephaestus/.github/workflows/ci-release-node-package.yml@main
    permissions:
      contents: write
    with:
      workdir: "./"
      node-version: "24.x"
```

Use this delivery path when consumers need an immutable, publicly downloadable
package but an npm registry publisher is not available. The workflow accepts
only an exact `v*` tag, sets the manifest version from that tag, requires
exactly one `pnpm pack` tarball, and creates or updates the matching GitHub
Release asset. Consumers should pin the complete release asset URL.

### Rust Tauri

```yaml
jobs:
  ci:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-rust-tauri.yml@main
    permissions:
      contents: read
    with:
      workdir: "./"
      release: false

  release:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [ci]
    uses: heliannuuthus/hephaestus/.github/workflows/ci-rust-tauri.yml@main
    permissions:
      contents: write
    with:
      workdir: "./"
      release: true
```
