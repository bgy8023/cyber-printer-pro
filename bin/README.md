# bin/ 目录

此目录用于存放可选的 Rust 高性能扩展二进制文件。

## 用途

- `claw-core` / `claw-core.exe` - Rust 核心高性能计算模块（可选）
- 当 Rust 扩展存在时，系统会自动使用以获得更好的性能
- 如果 Rust 扩展不存在，系统会回退到 Python 原生实现

## 说明

本项目完全开源，Rust 扩展是可选的。没有 Rust 扩展时，Python 原生实现也能正常工作。

## 构建（可选）

如果你需要构建 Rust 扩展：

```bash
cd src/rust_core
cargo build --release
cp target/release/claw-core ../../bin/
```

> 注意：Rust 扩展需要 Rust 编译器环境，普通用户不需要构建。
