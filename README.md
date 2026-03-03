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
├── ci-frontend.yml               # setup → lint → build (frontend)
├── ci-rust-tauri.yml             # multi-platform Tauri build
└── ci-containerize.yml           # Docker containerization
```

## Usage

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
```

### Node.js Backend

```yaml
jobs:
  ci:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-node.yml@main
    with:
      workdir: "./"
```

### Rust Tauri

```yaml
jobs:
  ci:
    uses: heliannuuthus/hephaestus/.github/workflows/ci-rust-tauri.yml@main
    permissions:
      contents: write
      packages: write
    with:
      workdir: "./"
```
