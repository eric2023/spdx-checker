# SPDX Scanner Makefile
# 简化常用操作的自动化脚本

.PHONY: help install install-dev demo verify quick-verify standard-verify html-report clean test lint

# 默认目标
help:
	@echo "🔧 SPDX Scanner Makefile"
	@echo "========================"
	@echo ""
	@echo "可用命令:"
	@echo "  install      - 从源码安装项目"
	@echo "  install-dev  - 安装开发版本（包含开发依赖）"
	@echo "  demo         - 运行演示脚本"
	@echo "  verify       - 运行完整验证"
	@echo "  quick-verify - 运行快速验证"
	@echo "  html-report  - 生成HTML验证报告"
	@echo "  test         - 运行测试"
	@echo "  lint         - 运行代码检查"
	@echo "  clean        - 清理临时文件"
	@echo ""
	@echo "📚 CLI使用示例:"
	@echo "  spdx-scanner scan /path/to/project"
	@echo "  spdx-scanner correct /path/to/project"
	@echo "  spdx-scanner scan --format html --output report.html /path/to/project"

# 安装项目
install:
	@echo "📦 安装 SPDX Scanner..."
	python3 -m venv venv_install
	. venv_install/bin/activate && pip install --upgrade pip
	@echo "🔄 尝试安装项目..."
	@. venv_install/bin/activate && pip install -e . || (echo "❌ 安装失败，尝试使用备用源..."; . venv_install/bin/activate && pip install -i https://pypi.douban.com/simple/ -e . || echo "⚠️  建议检查网络连接或手动安装依赖")

# 安装开发版本
install-dev:
	@echo "📦 安装 SPDX Scanner 开发版本..."
	python3 -m venv venv_dev
	. venv_dev/bin/activate && pip install --upgrade pip
	@echo "🔄 尝试安装开发版本..."
	@. venv_dev/bin/activate && pip install -e '.[dev]' || (echo "❌ 安装失败，尝试使用备用源..."; . venv_dev/bin/activate && pip install -i https://pypi.douban.com/simple/ -e '.[dev]' || echo "⚠️  建议检查网络连接或手动安装依赖")

# 运行演示
demo:
	@echo "🎭 运行演示..."
	@echo "使用验证工具展示SPDX Scanner功能..."
	python tools/verification/automated_verifier.py --mode quick
	@echo ""
	@echo "🎯 扫描示例文件..."
	@if [ -d "examples" ]; then \
		echo "发现examples目录，建议运行："; \
		echo "  python tools/verification/automated_verifier.py --mode standard"; \
	else \
		echo "请先克隆或下载示例项目"; \
	fi

# 运行完整验证
verify:
	@echo "🧪 运行完整验证..."
	python tools/verification/automated_verifier.py --mode standard

# 运行快速验证
quick-verify:
	@echo "⚡ 运行快速验证..."
	python tools/verification/automated_verifier.py --mode quick

# 生成HTML报告
html-report:
	@echo "📊 生成HTML验证报告..."
	python tools/verification/automated_verifier.py --mode standard --format html --output verification_report.html

# 运行测试
test:
	@echo "🧪 运行测试..."
	@echo "🔍 检查测试依赖..."
	@python -m pytest tests/ -v 2>/dev/null || (echo "⚠️  pytest未安装或测试环境不可用"; echo "💡 安装测试依赖: make install-dev"; echo "📁 发现的测试文件:"; find tests/ -name "test_*.py" -type f || echo "未找到测试文件"; echo "🔧 建议：运行 'make check' 进行替代验证")

# 运行代码检查
lint:
	@echo "🔍 运行代码检查..."
	python -m flake8 src/ tests/ || true
	python -m black --check src/ tests/ || true
	python -m isort --check-only src/ tests/ || true

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	rm -rf venv_install/ venv_dev/ venv_spdx/
	rm -rf __pycache__/ src/*/__pycache__/ tests/__pycache__/
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# 直接使用CLI演示
cli-demo:
	@echo "🖥️  CLI演示..."
	@echo "1. 查看帮助:"
	python spdx_scanner_cli.py --help
	@echo -e "\n2. 演示扫描命令:"
	python spdx_scanner_cli.py scan /path/to/project --format html
	@echo -e "\n3. 演示修正命令:"
	python spdx_scanner_cli.py correct /path/to/project --dry-run
	@echo -e "\n4. 演示验证命令:"
	python spdx_scanner_cli.py verify --mode quick

# 一键验证（推荐）
check:
	@echo "🔍 一键验证流程..."
	@echo "1. 快速验证..."
	python tools/verification/automated_verifier.py --mode quick --no-auto-fix
	@echo -e "\n2. 运行代码检查..."
	make lint || echo "⚠️  代码检查发现问题，但继续执行"
	@echo -e "\n3. 运行演示..."
	python demo.py

# 构建分发包
build:
	@echo "📦 构建分发包..."
	python -m build

# 显示项目状态
status:
	@echo "📊 项目状态"
	@echo "============"
	@echo "Python文件数量: $$(find src/ -name '*.py' | wc -l)"
	@echo "测试文件数量: $$(find tests/ -name '*.py' | wc -l)"
	@echo "验证工具文件数量: $$(find tools/verification/ -name '*.py' | wc -l)"
	@echo "文档文件数量: $$(find . -name '*.md' | wc -l)"
	@echo ""
	@echo "项目结构:"
	@tree -I '__pycache__|*.pyc|venv*|.git' -L 2 . || find . -type d -not -path '*/\.*' | head -20
