# Hephaestus

Hephaestus 提供可复用 GitHub Actions workflows 与 composite actions，覆盖 Go、Rust、Node.js、pnpm 前端、Tauri、容器构建与 GitHub Pages 部署。

## 目录结构

| 路径 | 说明 |
|------|------|
| `actions/` | Composite actions，可被 workflow 复用 |
| `.github/workflows/` | Reusable workflows，对外通过 `uses:` 调用 |
| `tests/` | Go/Node/Rust 示例项目，用于验证 workflow 行为 |

## 主要入口

- `.github/workflows/ci-golang.yml`
- `.github/workflows/ci-rust.yml`
- `.github/workflows/ci-node.yml`
- `.github/workflows/ci-frontend.yml`
- `.github/workflows/ci-deploy-pages.yml`
- `.github/workflows/ci-containerize.yml`
- `actions/setup-go/action.yml`
- `actions/setup-node/action.yml`
- `actions/setup-pnpm/action.yml`
- `actions/setup-rust/action.yml`
- `actions/version/action.yml`

## 开发规则

- 修改 workflow 输入/输出时，同步 README 示例。
- Composite action 的 shell 脚本保持可读，避免把复杂逻辑塞进单行 YAML。
- 默认权限遵循最小权限；需要 `packages: write`、`pages: write`、`id-token: write` 时在示例中显式说明。
- 对跨语言 workflow 的缓存、版本探测、工作目录参数保持一致命名。

## 验证 Checklist

1. YAML 变更后检查缩进、`uses:`、`with:`、`outputs:`。
2. 修改某语言 setup action 后，对应检查 `tests/<lang>/` 示例仍匹配。
3. 涉及版本输出或镜像 tag 时，重点检查 `actions/version` 与 `ci-containerize` 的衔接。
