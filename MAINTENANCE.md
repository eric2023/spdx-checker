# SPDX Scanner 项目维护指南

## 概述

本文档提供了SPDX Scanner项目的全面维护指南，确保项目始终保持在高质量标准。

## 🛠️ 开发工作流

### 1. 预提交检查

每次提交代码前，请运行以下检查：

```bash
# 运行快速验证
python tools/verification/automated_verifier.py --mode quick

# 或者使用新的质量管理工具
python tools/quality_manager.py
```

### 2. 代码质量工具

项目集成了多种代码质量工具：

- **Black**: 代码格式化
- **isort**: 导入语句排序
- **flake8**: 代码风格检查
- **mypy**: 静态类型检查
- **pytest**: 测试框架

#### 运行完整质量检查

```bash
python tools/quality_manager.py
```

#### 单独运行各工具

```bash
# 代码格式化
python -m black src/ tests/ tools/

# 导入排序
python -m isort src/ tests/ tools/

# 代码风格检查
python -m flake8 src/ tests/ tools/

# 类型检查
python -m mypy src/

# 运行测试
python -m pytest tests/ --cov=src/spdx_scanner
```

## 🔄 持续集成

### GitHub Actions

项目配置了完整的CI/CD流程 (`.github/workflows/ci.yml`)：

- **多Python版本测试**: 3.8-3.12
- **代码质量检查**: 格式、风格、类型检查
- **测试覆盖率**: 要求≥80%
- **自动化验证**: 运行验证工具

### 本地CI模拟

```bash
# 运行完整的CI检查
python tools/quality_manager.py

# 模拟GitHub Actions的测试流程
python -m pytest tests/ --cov=src/spdx_scanner --cov-report=xml
```

## 🧪 测试策略

### 测试覆盖率要求

- **最低覆盖率**: 80%
- **分支覆盖率**: 开启
- **覆盖报告**: HTML和XML格式

### 运行测试

```bash
# 基础测试
python -m pytest tests/

# 带覆盖率的测试
python -m pytest tests/ --cov=src/spdx_scanner --cov-report=html

# 只运行特定测试
python -m pytest tests/test_scanner.py
```

### 测试标记

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.slow`: 慢速测试

## 🔍 验证工具

### 验证模式

1. **quick模式**: 快速基础检查 (< 1秒)
2. **standard模式**: 标准验证 (推荐使用)
3. **full模式**: 完整验证 (15-30分钟)
4. **ci模式**: CI/CD优化验证

### 运行验证

```bash
# 快速验证
python tools/verification/automated_verifier.py --mode quick

# 标准验证
python tools/verification/automated_verifier.py --mode standard

# 生成HTML报告
python tools/verification/automated_verifier.py --mode standard --format html --output report.html
```

## 🏗️ 架构维护

### 模块职责

```
src/spdx_scanner/
├── cli.py          # 命令行接口
├── scanner.py      # 文件扫描
├── parser.py       # SPDX解析
├── validator.py    # SPDX验证
├── corrector.py    # SPDX修正
├── reporter.py     # 报告生成
├── models.py       # 数据模型
└── config.py       # 配置管理
```

### 添加新功能

1. 在对应模块中添加功能
2. 添加单元测试
3. 更新文档
4. 运行质量检查
5. 提交PR

## 🔧 配置管理

### 项目配置 (`pyproject.toml`)

- **测试配置**: pytest.ini_options
- **覆盖率配置**: coverage.run, coverage.report
- **代码质量配置**: black, isort, mypy, flake8

### 覆盖率配置

```toml
[tool.coverage.report]
fail_under = 80  # 最低80%覆盖率
show_missing = true
precision = 2
```

## 🚀 发布流程

### 版本发布前检查

1. 运行完整质量检查
2. 确保测试覆盖率≥80%
3. 验证所有验证模式通过
4. 更新版本号和changelog
5. 运行CI流程

### 质量门禁

```bash
# 必须通过的所有检查
python tools/quality_manager.py
python -m pytest tests/ --cov=src/spdx_scanner --cov-fail-under=80
python tools/verification/automated_verifier.py --mode standard
```

## 📊 监控指标

### 关键指标

- **测试覆盖率**: ≥80%
- **代码质量分数**: ≥90%
- **验证状态**: PASS
- **CI通过率**: 100%

### 质量报告

```bash
# 生成综合质量报告
python tools/quality_manager.py

# 查看测试覆盖率详情
python -m pytest tests/ --cov=src/spdx_scanner --cov-report=html
# 打开 htmlcov/index.html 查看报告
```

## 🐛 问题解决

### 常见问题

1. **测试覆盖率不足**
   ```bash
   # 查看缺失覆盖的行
   python -m pytest tests/ --cov=src/spdx_scanner --cov-report=term-missing

   # 添加缺失的测试
   ```

2. **代码格式问题**
   ```bash
   # 自动修复格式问题
   python -m black src/ tests/ tools/
   python -m isort src/ tests/ tools/
   ```

3. **验证失败**
   ```bash
   # 运行详细验证
   python tools/verification/automated_verifier.py --mode standard --format json
   ```

### 获取帮助

```bash
# 查看可用命令
make help

# 运行演示
make demo

# 查看项目状态
make status
```

## 📝 更新日志

### 维护历史

- **2025-10-30**: 添加CI/CD流程、质量管理工具、覆盖率配置
- **2025-10-30**: 建立预提交钩子、持续集成
- **2025-10-30**: 修复所有验证错误，实现100%通过率

---

**维护目标**: 保持项目质量在最高标准，确保代码可靠性和用户体验。