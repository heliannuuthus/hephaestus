<h1 align="center">🌻🌻integration 🌻 deployment🌻🌻</h1>

## Introduction

A github **continuous integration** and **continuous deployment**, built-in `java`, `rust`, `golang`, `node` different programming languages reusable workflow.

## Getting Started

For **Java** projects that use **gradle** as a build tool, it provides integrated configuration, supporting `single applications`, `cloud services`, `single project libraries`, and `multi-project libraries`.

### rust

[![rust](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/rust-ci.yml/badge.svg)](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/rust-ci.yml)

```yaml
name: rust

on:
  pull_request:
    types: [opened, reopened, synchronize]
  pull_request_target:
    types: [closed]
jobs:
  setup:
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-rust-setup.yml
    with:
      workdir: "tests/rust/"

  lint:
    if: ${{ github.event.pull_request.merged != true }}
    needs: setup
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-rust-lint.yml
    with:
      workdir: "tests/rust/"

  build:
    if: ${{ always() && needs.setup.result == 'success' }}
    needs: [setup, lint]
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-rust-build.yml
    with:
      workdir: "tests/rust/"

  containeraized:
    if: ${{ always() && github.event.pull_request.merged == true }}
    needs: build
    permissions:
      contents: read
      packages: write
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-containerize.yml
    with:
      version: ${{ needs.build.outputs.version }}
      workdir: "tests/rust/"
```

### gradle-cloud

[![gradle-cloud](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/golang-cloud-ci.yml/badge.svg)](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/golang-cloud-ci.yml)

> use **Dockerfile** to build the project image, the default build jar package name is `app.jar`, output directory is `build/libs/`

```yaml
name: gradle-cloud

on:
  pull_request:
    types: [opened, reopened, synchronize]
  pull_request_target:
    types: [closed]

jobs:
  lint:
    if: ${{ github.event.pull_request.merged != true }}
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-gradle-lint.yml
    with:
      workdir: "tests/gradle-cloud/"

  build:
    if: always()
    needs: lint
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-gradle-build.yml
    with:
      workdir: "tests/gradle-cloud/"

  containerize:
    if: ${{ always() && github.event.pull_request.merged == true }}
    needs: build
    permissions:
      contents: read
      packages: write
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-containerize.yml
    with:
      workdir: "tests/gradle-cloud/"
      version: ${{ needs.build.outputs.version }}
```

### gradle-library

[![gradle-library](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/gradle-library-ci.yml/badge.svg)](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/gradle-library-ci.yml)

> publish the package to github pakcage

```yaml
name: gradle-library

on:
  pull_request:
    types: [opened, reopened, synchronize]
  pull_request_target:
    types: [closed]

jobs:
  lint:
    if: ${{ github.event.pull_request.merged != true }}
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-gradle-lint.yml
    with:
      workdir: "tests/gradle-library/"

  build:
    if: always()
    needs: lint
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-gradle-build.yml
    with:
      workdir: "tests/gradle-library/"

  containerize:
    if: ${{ always() && github.event.pull_request.merged == true }}
    needs: build
    permissions:
      contents: read
      packages: write
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-gradle-publish.yml
    with:
      workdir: "tests/gradle/"
      user: ${{ github.actor }}
    secrets:
      token: ${{ secrets.GITHUB_TOKEN }}
```

### golang

[![golang](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/golang-ci.yaml/badge.svg)](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/golang-ci.yaml)

```yaml
name: golang

on:
  pull_request:
    types: [opened, reopened, synchronize]
  pull_request_target:
    types: [closed]

env:
  GOOS: linux
  GOARCH: amd64

jobs:
  setup:
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-golang-setup.yml
    with:
      workdir: "tests/golang/"

  lint:
    if: ${{ github.event.pull_request.merged != true }}
    needs: setup
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-golang-lint.yml
    with:
      workdir: "tests/golang/"

  build:
    if: ${{ always() && needs.setup.result == 'success' }}
    needs: [setup, lint]
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-golang-build.yml
    with:
      workdir: "tests/golang/"
      entrance: cmd/main.go

  containeraized:
    if: ${{ always() && github.event.pull_request.merged }}
    needs: build
    permissions:
      contents: read
      packages: write
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-containerize.yml
    with:
      workdir: "tests/golang/"
```

### node

[![node](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/node-ci.yaml/badge.svg)](https://github.com/heliannuuthus/integrate-deploy/actions/workflows/node-ci.yaml)

```yaml
name: node

on:
  pull_request:
    types: [opened, reopened, synchronize]
  pull_request_target:
    types: [closed]
jobs:
  setup:
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-node-setup.yml
    with:
      workdir: "tests/node/"

  lint:
    if: ${{ github.event.pull_request.merged != true }}
    needs: setup
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-node-lint.yml
    with:
      workdir: "tests/node/"
      PNPM_STORE: ${{ needs.setup.outputs.PNPM_STORE }}

  build:
    if: ${{ always() && needs.setup.result == 'success' }}
    needs: [setup, lint]
    uses: heliannuuthus/integrate-deploy/.github/workflows/call-node-build.yml
    with:
      workdir: "tests/node/"
      PNPM_STORE: ${{ needs.setup.outputs.PNPM_STORE }}
```
