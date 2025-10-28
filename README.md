# SPDX Scanner

**立即可用的SPDX许可证声明扫描和修正工具**

🔍 扫描源代码文件中的SPDX许可证声明 | 🔧 自动修正缺失或错误的声明 | 📊 生成详细报告 | 🧪 内置验证和测试工具

> **新手友好** - 无需复杂配置，下载即可使用！查看下方[🚀 立即开始](#立即开始)开始体验。

## ✨ 项目特色

- **📦 立即可用** - 无需复杂安装，下载即用
- **🔍 智能扫描** - 自动识别多种编程语言的SPDX声明
- **🔧 自动修正** - 一键修复缺失或错误的许可证声明
- **📊 详细报告** - 生成HTML、JSON、Markdown格式报告
- **🧪 验证工具** - 内置自动化验证和测试工具
- **🌐 多语言支持** - C/C++、Go、Python、JavaScript等
- **⚙️ 灵活配置** - 支持自定义规则和模板

## 🚀 立即开始

> **💡 获取仓库地址**: 运行 `git remote -v` 可以查看当前项目的仓库地址，或直接使用当前目录作为项目根目录。

### 方式一：快速体验（推荐新手）

无需安装，下载即可使用：

```bash
# 方法1: 克隆真实仓库（当前项目）
git clone https://github.com/eric2023/spdx-checker.git
cd spdx-checker

# 方法2: 使用当前项目目录（推荐）
# cd /path/to/current/spdx-checker/project

# 2. 立即体验演示（推荐）
make demo

# 3. 查看可用功能
make help

# 4. 体验验证工具（无需安装，直接运行）
python tools/verification/automated_verifier.py --mode quick

# 5. 标准验证（扫描项目示例）
python tools/verification/automated_verifier.py --mode standard

# ⚠️ 注意：standard模式可能会发现项目中的问题，这是正常的验证功能
```

> **💡 重要提示**: 验证工具可以直接使用，无需安装Python依赖！

### 方法二：开发环境安装（适合开发者）

> **⚠️ 重要提醒**:
> - 由于使用了externally-managed-environment，必须使用虚拟环境安装！
> - 安装过程需要网络下载依赖包，可能会超时失败
> - 如果安装失败，建议直接使用方法一的验证工具

```bash
# 1. 克隆或下载项目
# git clone https://github.com/eric2023/spdx-checker.git
# cd spdx-checker

# 或者直接使用当前项目目录
# cd /path/to/current/spdx-checker

# 2. 创建虚拟环境（必需！）
rm -rf venv_spdx  # 如果已存在，先删除
python3 -m venv venv_spdx
source venv_spdx/bin/activate  # Linux/Mac
# venv_spdx\Scripts\activate  # Windows

# 3. 安装开发依赖
# 注意：此步骤需要网络连接下载依赖包
pip install -e ".[dev]"

# 4. 验证安装
spdx-scanner --help

# 5. 替代方案：使用验证工具（无需安装）
python tools/verification/automated_verifier.py --mode quick
```

> **💡 提示**:
> - 如果网络受限或安装失败，请直接使用方法一使用验证工具
> - 验证工具提供完整功能，无需安装命令行工具

### 方法三：体验验证工具

```bash
# 运行自动化验证（检测项目健康度）
python tools/verification/automated_verifier.py --mode quick

# 生成HTML验证报告
python tools/verification/automated_verifier.py --mode standard --format html --output report.html

# 查看项目状态
make status
```

### 方法四：实际扫描项目

```bash
# 使用验证工具扫描示例文件
python tools/verification/automated_verifier.py --mode standard

# 如果已安装CLI，使用以下命令（需要先安装依赖）
# python -m spdx_scanner scan examples/
```

## 🛠️ 基本使用

> **💡 推荐**: 对于大多数用户，建议直接使用验证工具，无需安装任何依赖！

### 扫描项目中的SPDX问题

```bash
# 推荐方法：使用验证工具（无需安装依赖）
python tools/verification/automated_verifier.py --mode standard

# ⚠️ 注意：验证工具目前不支持指定路径，默认扫描当前项目目录

# 如果已安装CLI工具包，可以使用以下命令（需要先安装依赖）：
# 扫描当前目录
# spdx-scanner scan .

# 扫描指定目录
# spdx-scanner scan /path/to/your/project

# 扫描特定文件类型
# spdx-scanner scan -e .c -e .cpp -e .h /path/to/project

# 生成HTML报告
# spdx-scanner scan --format html --output report.html /path/to/project
```

### 自动修正SPDX声明

```bash
# 使用验证工具的自动修正功能
python tools/verification/automated_verifier.py --mode standard --no-auto-fix false

# 如果已安装CLI工具包，可以使用以下命令（需要先安装依赖）：
# 预览修正（不修改文件）
# spdx-scanner correct --dry-run /path/to/project

# 执行修正
# spdx-scanner correct /path/to/project

# 指定默认许可证
# spdx-scanner correct --license MIT /path/to/project
```

### 运行验证工具

```bash
# 快速验证
python tools/verification/automated_verifier.py --mode quick

# 标准验证（推荐）
python tools/verification/automated_verifier.py --mode standard

# 完整验证
python tools/verification/automated_verifier.py --mode full

# 生成不同格式报告
python tools/verification/automated_verifier.py --mode standard --format json
python tools/verification/automated_verifier.py --mode standard --format markdown
```

## 📁 项目结构

```
spdx-scanner/
├── src/spdx_scanner/          # 核心源代码
│   ├── cli.py                 # 命令行界面
│   ├── scanner.py             # 文件扫描器
│   ├── parser.py              # SPDX解析器
│   ├── validator.py           # SPDX验证器
│   ├── corrector.py           # SPDX修正器
│   ├── reporter.py            # 报告生成器
│   ├── models.py              # 数据模型
│   └── config.py              # 配置管理
├── tools/verification/        # 验证工具
│   ├── automated_verifier.py  # 主验证器 ⭐
│   ├── spdx_validator.py      # SPDX组件验证
│   ├── quality_checker.py     # 代码质量检查
│   ├── integration_tester.py  # 集成测试
│   ├── auto_corrector.py      # 自动修正器
│   └── report_generator.py    # 报告生成器
├── examples/                  # 示例文件 ⭐
│   ├── example.c              # C语言示例
│   ├── example.py             # Python示例
│   ├── example.js             # JavaScript示例
│   └── spdx-scanner.config.json  # 配置文件示例
├── test_project/              # 测试项目
│   ├── python/                # Python测试文件
│   ├── go/                    # Go测试文件
│   ├── js/                    # JavaScript测试文件
│   └── rust/                  # Rust测试文件
├── Makefile                   # 自动化操作 ⭐
└── README.md                  # 本文档
```

## 🔧 高级功能

### 使用自动化脚本

```bash
# 查看所有可用命令
make help

# 安装项目
make install

# 运行演示
make demo

# 快速验证
make quick-verify

# 生成HTML报告
make html-report

# 清理临时文件
make clean
```

### 验证工具详解

验证工具提供5种验证模式：

1. **quick** - 2分钟基础检查
2. **standard** - 5-10分钟标准验证（推荐）
3. **full** - 15-30分钟完整验证
4. **ci** - CI/CD模式验证

### 配置文件

项目根目录的`spdx-scanner.config.json`：

```json
{
  "project_name": "Your Project",
  "copyright_holder": "Your Organization",
  "default_license": "MIT",
  "scanner_settings": {
    "source_file_extensions": [".c", ".cpp", ".h", ".go", ".py"],
    "exclude_patterns": ["**/node_modules/**", "**/build/**"]
  },
  "correction_settings": {
    "default_license": "MIT",
    "create_backups": true,
    "dry_run": false
  }
}
```

## 📊 实际示例

### 查看项目中的实际示例

```bash
# 查看示例文件
ls examples/

# 查看C语言示例
cat examples/example.c

# 查看Python示例
cat examples/example.py

# 查看配置文件示例
cat examples/spdx-scanner.config.json
```

### 运行实际扫描

```bash
# 扫描examples目录（推荐方法）
python tools/verification/automated_verifier.py --mode standard

# 扫描test_project
python tools/verification/automated_verifier.py --mode full

# 生成详细报告
python tools/verification/automated_verifier.py --mode standard --format html --output verification_report.html

# 如果已安装CLI工具包，可以使用以下命令（需要先安装依赖）：
# python -m spdx_scanner scan examples/
# python -m spdx_scanner scan test_project/
# python -m spdx_scanner scan --format html --output examples_report.html examples/
```

## ❓ 问题解决

### 常见问题

**Q: `spdx-scanner` 命令无法运行？**
```bash
# 确保安装了命令行工具（需要虚拟环境）
python3 -m venv venv_spdx
source venv_spdx/bin/activate
pip install -e .

# 或者直接使用验证工具（推荐，无需安装）
python tools/verification/automated_verifier.py --mode quick
```

**Q: pip安装失败（externally-managed-environment）？**
```bash
# 错误提示：This environment is externally managed
# 解决方案：必须使用虚拟环境
python3 -m venv venv_myproject
source venv_myproject/bin/activate
pip install -e ".[dev]"

# 或者直接使用验证工具，无需安装
python tools/verification/automated_verifier.py --mode standard
```

**Q: 依赖安装网络超时？**
```bash
# 问题：网络连接超时或下载失败
# 解决方案1：使用验证工具（无需安装）
python tools/verification/automated_verifier.py --mode standard

# 解决方案2：使用离线安装（如果已下载依赖包）
# pip install --no-index --find-links /path/to/packages -e ".[dev]"

# 解决方案3：重新尝试安装
pip install -e ".[dev]" --timeout 60
```

**Q: 命令无法运行？**
```bash
# 确保在项目根目录
pwd
# 应该显示 spdx-checker 目录

# 检查Python版本（需要3.7+）
python --version

# 运行演示确认环境
make demo
```

**Q: 扫描结果为空？**
```bash
# 检查目录是否存在
ls -la /path/to/project

# 使用验证工具检查项目
python tools/verification/automated_verifier.py --mode quick

# 如果使用CLI（需要先安装依赖）
# spdx-scanner --help
# spdx-scanner scan -e .py -e .c -e .js /path/to/project
```

**Q: 验证工具报错？**
```bash
# 使用快速模式
python tools/verification/automated_verifier.py --mode quick --no-auto-fix

# 查看详细错误
python tools/verification/automated_verifier.py --mode quick --verbose
```

### 获取帮助

```bash
# 查看Makefile命令
make help

# 查看验证工具帮助
python tools/verification/automated_verifier.py --help

# 如果已安装CLI工具包，可以使用以下命令（需要先安装依赖）：
# spdx-scanner --help

# 运行项目演示
make demo

# 使用验证工具
python tools/verification/automated_verifier.py --mode standard
```

## 🎯 完整使用流程

### 新手推荐流程

1. **立即体验**
   ```bash
   make demo
   ```

2. **了解项目**
   ```bash
   make status
   ls examples/
   ```

3. **实际使用（推荐：无需安装）**
   ```bash
   # 使用验证工具进行标准扫描
   python tools/verification/automated_verifier.py --mode standard
   ```

4. **验证工具**
   ```bash
   # 快速验证项目健康度
   python tools/verification/automated_verifier.py --mode quick
   ```

5. **深入学习**
   ```bash
   make help
   ```

> **💡 重要提示**: 验证工具提供完整功能，无需安装任何Python依赖！

### 开发者流程

1. **安装开发环境（需要虚拟环境）**
   ```bash
   # 创建虚拟环境（必须）
   python3 -m venv venv_dev
   source venv_dev/bin/activate  # Linux/Mac
   # venv_dev\Scripts\activate  # Windows

   # 安装开发依赖
   pip install -e ".[dev]"
   ```

2. **运行完整验证**
   ```bash
   make verify
   make html-report
   ```

3. **查看测试**
   ```bash
   python -m pytest tests/
   ```

4. **代码质量检查**
   ```bash
   make lint
   ```

> **💡 替代方案**: 如果安装失败，可以使用验证工具
> ```bash
> python tools/verification/automated_verifier.py --mode full --format html --output dev_report.html
> ```

## 🔍 支持的文件类型

### 默认支持（无需配置）
- **C/C++** (.c, .cpp, .h, .hpp)
- **Go** (.go)
- **Python** (.py)
- **JavaScript** (.js, .jsx)
- **TypeScript** (.ts, .tsx)

### 配置支持
通过配置文件或命令行参数可支持更多类型：
- Java, Rust, Shell, HTML, CSS, SCSS等

### 示例文件
查看`examples/`目录中的实际示例文件，了解不同语言的SPDX声明格式。

## 📈 验证和测试

### 项目健康度检查

```bash
# 一键检查项目健康度
make check

# 快速验证
python tools/verification/automated_verifier.py --mode quick

# 生成健康报告
python tools/verification/automated_verifier.py --mode standard --format html --output health_report.html
```

### 测试覆盖率

```bash
# 运行测试
python -m pytest tests/ -v

# 查看测试覆盖率
python -m pytest tests/ --cov=src/spdx_scanner --cov-report=html
```

## 🤝 贡献指南

欢迎贡献代码！以下是快速开始：

### 开发环境设置

```bash
# 方法1: 如果有Git仓库地址
git clone https://github.com/eric2023/spdx-checker.git
cd spdx-checker

# 方法2: 使用当前项目目录
# cd /path/to/current/spdx-checker

# 方法3: 使用Makefile自动安装（推荐）
make install-dev

# 方法4: 手动安装
rm -rf venv_dev  # 如果已存在，先删除
python3 -m venv venv_dev
source venv_dev/bin/activate  # Linux/Mac
# venv_dev\Scripts\activate  # Windows
pip install -e ".[dev]"

# 运行测试
make test

# 运行验证
make verify
```

### 代码规范

- 遵循PEP 8代码风格
- 使用black格式化代码
- 添加适当的测试用例
- 更新相关文档

### 贡献流程

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 运行验证工具
5. 提交Pull Request

## 📊 项目统计

- **核心文件**: 13个Python模块
- **测试文件**: 11个测试文件
- **验证工具**: 6个验证模块
- **示例文件**: 多种语言示例
- **文档文件**: 完整的使用文档

## 📄 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 📞 支持

- 📖 查看本README文档
- 🧪 运行`make demo`了解功能
- 🔧 运行`make help`查看所有命令
- 🐛 运行`make verify`检查项目健康
- 🔍 **推荐**运行验证工具进行快速验证：
  ```bash
  python tools/verification/automated_verifier.py --mode quick
  ```
- 📊 **完整功能**使用验证工具：
  ```bash
  python tools/verification/automated_verifier.py --mode standard
  ```

> **💡 最佳实践**: 验证工具提供完整功能且无需安装，推荐优先使用！

---

**🎉 现在就开始体验吧！运行 `make demo` 了解所有功能。**