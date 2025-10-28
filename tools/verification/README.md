# SPDX Scanner 自动化验证工具

统一的全自动验证框架，确保SPDX Scanner各组件正常工作，发现问题并自动修复。

## 📋 概述

这个自动化验证工具集成了多个验证模块，提供全面的质量保证和自动修复功能：

- **🔍 SPDX组件验证**: 验证解析器、验证器、修正器等核心功能
- **📊 代码质量检查**: 分析代码复杂度、重复代码、依赖关系等
- **🔗 集成测试**: 测试CLI接口、配置文件、文件处理等
- **🔧 自动修复**: 自动发现并修复常见问题
- **📄 多格式报告**: 生成控制台、JSON、HTML、Markdown格式报告

## 🚀 快速开始

### 基本使用

```bash
# 标准验证（推荐）
python tools/verification/automated_verifier.py --mode standard

# 快速验证（基础检查）
python tools/verification/automated_verifier.py --mode quick

# 完整验证（全功能）
python tools/verification/automated_verifier.py --mode full

# CI/CD模式（持续集成）
python tools/verification/automated_verifier.py --mode ci
```

### 生成报告

```bash
# 生成HTML报告
python tools/verification/automated_verifier.py --mode standard --format html --output verification_report.html

# 生成JSON报告（便于程序解析）
python tools/verification/automated_verifier.py --mode standard --format json --output verification_report.json

# 生成Markdown报告
python tools/verification/automated_verifier.py --mode standard --format markdown --output verification_report.md
```

## 📖 详细用法

### 验证模式

| 模式 | 描述 | 耗时 | 包含内容 |
|------|------|------|----------|
| `quick` | 快速基础检查 | ~1-2分钟 | 核心模块导入、配置文件、CLI入口点 |
| `standard` | 标准验证（推荐） | ~5-10分钟 | SPDX组件验证、代码质量检查 |
| `full` | 完整验证 | ~15-30分钟 | 所有验证内容 + 集成测试 + 性能测试 |
| `ci` | CI/CD模式 | ~5-10分钟 | 适合持续集成的快速全面检查 |

### 选择性验证

```bash
# 仅验证SPDX组件
python tools/verification/automated_verifier.py --verify-spdx

# 仅验证代码质量
python tools/verification/automated_verifier.py --verify-quality

# 仅验证集成功能
python tools/verification/automated_verifier.py --verify-integration

# 组合使用
python tools/verification/automated_verifier.py --verify-spdx --verify-quality
```

### 高级选项

```bash
# 禁用自动修正
python tools/verification/automated_verifier.py --mode standard --no-auto-fix

# 详细输出
python tools/verification/automated_verifier.py --mode standard --verbose

# 指定输出文件
python tools/verification/automated_verifier.py --mode standard --format html --output my_report.html
```

## 🔧 配置选项

### 配置文件

工具使用 `tools/verification/config.yaml` 进行配置。主要配置项包括：

```yaml
# SPDX组件验证
spdx:
  accuracy_threshold: 0.95      # 期望准确率
  test_coverage_threshold: 0.80 # 期望覆盖率

# 代码质量
quality:
  max_complexity: 15            # 最大复杂度
  min_coverage: 0.80            # 最小覆盖率

# 自动修正
auto_fix:
  enable_auto_fix: true         # 启用自动修正
  backup_files: true            # 创建备份
  keep_backups: false          # 保留备份文件

# 报告格式
report:
  format: 'console'             # 默认格式
  include_details: true         # 包含详细信息
```

### 环境变量

可以通过环境变量覆盖配置：

```bash
# 覆盖默认模式
export SPDX_VERIFICATION_MODE=full

# 覆盖报告格式
export SPDX_REPORT_FORMAT=html

# 禁用自动修正
export SPDX_AUTO_FIX=false
```

## 📊 验证内容详解

### SPDX组件验证

验证SPDX Scanner的核心功能组件：

- **解析器 (Parser)**: 验证SPDX声明解析的正确性
- **验证器 (Validator)**: 检查许可证标识符和版权格式
- **修正器 (Corrector)**: 测试自动修正功能
- **报告器 (Reporter)**: 验证报告生成
- **扫描器 (Scanner)**: 测试文件扫描和过滤

### 代码质量检查

分析项目代码质量指标：

- **复杂度分析**: 圈复杂度和认知复杂度
- **代码长度**: 函数和类的长度检查
- **重复代码**: 检测代码重复模式
- **依赖关系**: 分析模块依赖和循环导入
- **外部工具集成**: flake8、mypy、black等工具

### 集成测试

验证端到端功能：

- **CLI接口**: 测试所有命令行功能
- **配置文件**: 验证配置加载和更新
- **文件处理**: 测试多文件类型处理
- **报告生成**: 验证各种报告格式
- **错误处理**: 测试异常情况处理
- **Git集成**: 测试Git钩子和集成功能
- **性能测试**: 评估扫描和处理性能

## 🔧 自动修复功能

工具能够自动修复以下类型的问题：

### 高优先级修复

- **导入错误**: 自动安装缺失的依赖包
- **缺失文件**: 创建必需的配置文件
- **配置错误**: 修复配置文件格式

### 中优先级修复

- **代码复杂度**: 生成重构建议文件
- **代码格式**: 使用black自动格式化
- **代码风格**: 使用flake8修复风格问题

### 低优先级修复

- **函数长度**: 生成拆分建议
- **命名规范**: 提供命名改进建议

### 备份和安全

- 自动创建备份文件到 `.verification_backups/`
- 可配置备份保留策略
- 对高风险修复需要确认

## 📄 报告格式

### 控制台输出

默认格式，适合开发时使用：

```
🔍 SPDX Scanner 自动化验证报告
==================================================
生成时间: 2024-01-15T10:30:00
验证模式: standard
验证耗时: 45.32秒
整体状态: ✅ 通过

📊 验证摘要
----------------------------------------
发现问题数量: 3
自动修复数量: 2
验证组件数量: 3

📋 SPDX 组件验证
----------------------------------------
状态: ✅ 通过
准确率: 98.50%
测试覆盖率: 85.20%
```

### HTML报告

适合查看和分享，包含丰富的样式和图表：

- 响应式设计，适配各种设备
- 彩色状态指示和进度条
- 可折叠的详细信息
- 包含度量指标可视化

### JSON报告

适合程序处理和自动化：

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "mode": "standard",
  "duration": 45.32,
  "overall_status": "PASS",
  "components": {
    "spdx": {
      "status": "PASS",
      "accuracy": 0.985,
      "test_coverage": 0.852
    }
  },
  "issues_found": [...],
  "auto_fixes_applied": [...],
  "recommendations": [...]
}
```

### Markdown报告

适合文档化和Git查看：

- GitHub兼容的Markdown格式
- 清晰的标题层级
- 适合转换为PDF或文档

## 🔄 持续集成集成

### GitHub Actions

```yaml
name: SPDX Verification
on: [push, pull_request]

jobs:
  verification:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run verification
      run: python tools/verification/automated_verifier.py --mode ci
    - name: Upload reports
      uses: actions/upload-artifact@v2
      with:
        name: verification-reports
        path: verification_reports/
```

### GitLab CI

```yaml
stages:
  - verification

verification:
  stage: verification
  script:
    - python tools/verification/automated_verifier.py --mode ci --format json --output report.json
  artifacts:
    paths:
      - verification_reports/
    expire_in: 1 week
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: spdx-verification
        name: SPDX Verification
        entry: python tools/verification/automated_verifier.py --mode quick --no-auto-fix
        language: system
        pass_filenames: false
```

## 🛠️ 故障排除

### 常见问题

**问题1: 导入错误**
```
ImportError: No module named 'spdx_scanner'
```
**解决方案**: 确保在项目根目录运行，并且Python路径正确设置。

**问题2: 权限错误**
```
PermissionError: [Errno 13] Permission denied
```
**解决方案**: 检查文件权限，确保有读写权限。

**问题3: 超时错误**
```
TimeoutExpired: Command timed out
```
**解决方案**: 增加超时时间或使用快速模式。

**问题4: 外部工具未找到**
```
FileNotFoundError: [Errno 2] No such file or directory: 'black'
```
**解决方案**: 安装缺失的工具 `pip install black flake8 mypy`

### 调试模式

启用详细调试信息：

```bash
python tools/verification/automated_verifier.py --mode standard --verbose
```

查看日志文件：

```bash
tail -f verification.log
```

### 重置工具

如果遇到问题，可以重置工具状态：

```bash
# 清理备份文件
rm -rf .verification_backups/

# 清理报告文件
rm -rf verification_reports/

# 重新运行验证
python tools/verification/automated_verifier.py --mode quick
```

## 📚 API参考

### Python API

```python
from tools.verification.automated_verifier import AutomatedVerifier
from pathlib import Path

# 创建验证器实例
verifier = AutomatedVerifier(Path.cwd())

# 运行验证
result = verifier.verify_all('standard')

# 生成报告
report = verifier.generate_report('html', 'report.html')

# 检查结果
print(f"状态: {result.overall_status}")
print(f"问题数: {len(result.issues_found)}")
print(f"修复数: {len(result.auto_fixes_applied)}")
```

### 自定义验证

```python
from tools.verification.spdx_validator import SPDXComponentValidator
from tools.verification.quality_checker import CodeQualityChecker

# 仅运行SPDX验证
spdx_validator = SPDXComponentValidator(project_root, config)
result = spdx_validator.verify_all()

# 仅运行代码质量检查
quality_checker = CodeQualityChecker(project_root, config)
result = quality_checker.analyze()
```

## 🤝 贡献指南

欢迎贡献代码和建议！

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd spdx-checker

# 安装开发依赖
pip install -e ".[dev]"

# 运行验证工具
python tools/verification/automated_verifier.py --mode standard
```

### 添加新验证

1. 在相应的验证器中添加新的检查方法
2. 更新配置文件的默认设置
3. 添加相应的测试用例
4. 更新文档

### 代码风格

- 遵循PEP 8代码风格
- 使用类型注解
- 添加适当的文档字符串
- 确保通过所有现有测试

## 📄 许可证

本工具遵循SPDX Scanner项目的MIT许可证。

## 🆘 支持

- 📖 [项目文档](https://github.com/example/spdx-scanner/wiki)
- 🐛 [问题反馈](https://github.com/example/spdx-scanner/issues)
- 💬 [讨论区](https://github.com/example/spdx-scanner/discussions)
- 📧 邮件支持: support@spdx-scanner.example

---

**最后更新**: 2024年1月15日
**版本**: 1.0.0
**维护者**: SPDX Scanner 团队
