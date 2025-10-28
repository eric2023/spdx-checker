#!/usr/bin/env python3
"""
SPDX Scanner 自动化重构工具

此脚本用于自动执行SPDX Scanner项目的目录重构工作，
包括文件迁移、重复文件清理、目录标准化等。

使用方法:
    python tools/migration/refactor.py [--dry-run] [--backup] [--verbose]

参数:
    --dry-run: 预览模式，不实际执行文件操作
    --backup: 在操作前创建备份
    --verbose: 详细输出模式
    --skip-tests: 跳过测试文件迁移
    --skip-docs: 跳过文档文件迁移
"""

import os
import shutil
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MigrationStatus(Enum):
    """迁移状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileMigration:
    """文件迁移配置"""
    source: str
    destination: str
    description: str
    required: bool = True
    backup_required: bool = False


@dataclass
class MigrationResult:
    """迁移结果"""
    source: str
    destination: str
    status: MigrationStatus
    message: str
    backup_path: Optional[str] = None


class ProjectRefactor:
    """项目重构器"""

    def __init__(self, dry_run: bool = False, backup: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.backup = backup
        self.verbose = verbose
        self.project_root = Path.cwd()
        self.migration_results: List[MigrationResult] = []
        self.backup_dir = self.project_root / "refactor_backup"

        # 设置日志
        self._setup_logging()

        # 定义迁移规则
        self.migration_rules = self._define_migration_rules()

    def _setup_logging(self):
        """设置日志配置"""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('refactor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _define_migration_rules(self) -> List[FileMigration]:
        """定义迁移规则"""
        return [
            # 测试文件迁移
            FileMigration(
                source="integration_test.py",
                destination="tests/integration/test_integration_e2e.py",
                description="集成测试文件迁移"
            ),
            FileMigration(
                source="simple_validation_test.py",
                destination="tests/integration/test_simple_validation.py",
                description="简单验证测试迁移"
            ),
            FileMigration(
                source="test_coverage.py",
                destination="tests/tools/test_coverage.py",
                description="覆盖率测试工具迁移"
            ),
            FileMigration(
                source="test_examples.py",
                destination="tests/tools/test_examples.py",
                description="示例测试迁移"
            ),
            FileMigration(
                source="test_extensions_config.py",
                destination="tests/tools/test_extensions_config.py",
                description="扩展配置测试迁移"
            ),
            FileMigration(
                source="test_validation.py",
                destination="tests/test_validation_complete.py",
                description="验证测试迁移"
            ),
            FileMigration(
                source="validation_test.py",
                destination="tests/test_validation_helper.py",
                description="验证辅助测试迁移"
            ),
            FileMigration(
                source="validation_example.py",
                destination="tests/examples/test_validation_examples.py",
                description="验证示例迁移"
            ),
            FileMigration(
                source="validation_summary.py",
                destination="tests/tools/test_summary.py",
                description="摘要测试迁移"
            ),

            # 文档文件迁移
            FileMigration(
                source="BUILD_VALIDATION.md",
                destination="docs/development/build-validation.md",
                description="构建验证文档迁移"
            ),
            FileMigration(
                source="PRODUCTION_DEPLOYMENT.md",
                destination="docs/deployment/production-deployment.md",
                description="生产部署文档迁移"
            ),
            FileMigration(
                source="RELEASE_PREPARATION.md",
                destination="docs/development/release-preparation.md",
                description="发布准备文档迁移"
            ),
            FileMigration(
                source="EXAMPLES_VERIFICATION.md",
                destination="docs/testing/examples-verification.md",
                description="示例验证文档迁移"
            ),
            FileMigration(
                source="EXTENSIONS_CONFIG.md",
                destination="docs/testing/extensions-config.md",
                description="扩展配置文档迁移"
            ),
            FileMigration(
                source="README_VALIDATION.md",
                destination="docs/testing/README-validation.md",
                description="README验证文档迁移"
            ),
            FileMigration(
                source="VERIFICATION_REPORT.md",
                destination="docs/testing/verification-report.md",
                description="验证报告文档迁移"
            ),

            # 特殊目录处理
            FileMigration(
                source=".logs",
                destination="logs",
                description="日志目录标准化",
                required=False
            ),
            FileMigration(
                source="task",
                destination="scripts/task_management",
                description="任务管理目录迁移",
                required=False
            ),
        ]

    def run(self) -> bool:
        """执行重构"""
        self.logger.info("开始SPDX Scanner项目重构...")

        # 1. 预处理
        if not self._preprocess():
            return False

        # 2. 执行迁移
        if not self._execute_migrations():
            return False

        # 3. 后处理
        if not self._postprocess():
            return False

        # 4. 生成报告
        self._generate_report()

        return True

    def _preprocess(self) -> bool:
        """预处理阶段"""
        self.logger.info("执行预处理...")

        try:
            # 创建目录结构
            if not self._create_directory_structure():
                return False

            # 创建备份
            if self.backup:
                if not self._create_backup():
                    return False

            # 清理缓存文件
            if not self._clean_cache_files():
                return False

            return True

        except Exception as e:
            self.logger.error(f"预处理失败: {e}")
            return False

    def _create_directory_structure(self) -> bool:
        """创建标准目录结构"""
        directories = [
            "src/spdx_scanner/cli/commands",
            "src/spdx_scanner/cli/formatters",
            "src/spdx_scanner/core",
            "src/spdx_scanner/io",
            "src/spdx_scanner/config",
            "src/spdx_scanner/models",
            "src/spdx_scanner/utils",
            "tests/unit",
            "tests/integration",
            "tests/fixtures",
            "tests/utils",
            "tests/examples",
            "docs/usage",
            "docs/development",
            "docs/api",
            "docs/examples",
            "examples",
            "scripts",
            "tools/migration",
            "tools/analysis",
            "tools/maintenance",
            "logs",
            ".github/workflows"
        ]

        for directory in directories:
            dir_path = self.project_root / directory
            try:
                if not dir_path.exists():
                    if self.dry_run:
                        self.logger.info(f"[DRY RUN] 创建目录: {directory}")
                    else:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        self.logger.info(f"创建目录: {directory}")

            except Exception as e:
                self.logger.error(f"创建目录失败 {directory}: {e}")
                return False

        return True

    def _create_backup(self) -> bool:
        """创建备份"""
        try:
            if self.dry_run:
                self.logger.info(f"[DRY RUN] 创建备份到: {self.backup_dir}")
                return True

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.project_root / f"refactor_backup_{timestamp}"

            self.logger.info(f"创建备份: {backup_path}")
            shutil.copytree(self.project_root, backup_path,
                          ignore=shutil.ignore_patterns(
                              '.git', '__pycache__', '*.pyc',
                              '.pytest_cache', 'refactor.log'
                          ))

            self.backup_dir = backup_path
            return True

        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            return False

    def _clean_cache_files(self) -> bool:
        """清理缓存文件"""
        patterns_to_clean = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".pytest_cache",
            "*.egg-info"
        ]

        for pattern in patterns_to_clean:
            try:
                if self.dry_run:
                    self.logger.info(f"[DRY RUN] 清理缓存文件: {pattern}")
                    continue

                # 使用find命令清理
                if pattern == "__pycache__":
                    result = os.system(f"find {self.project_root} -type d -name '__pycache__' -exec rm -rf {{}} + 2>/dev/null")
                elif pattern in ["*.pyc", "*.pyo"]:
                    result = os.system(f"find {self.project_root} -name '{pattern}' -delete 2>/dev/null")
                else:
                    result = os.system(f"find {self.project_root} -name '{pattern}' -type d -exec rm -rf {{}} + 2>/dev/null")

                if result == 0:
                    self.logger.info(f"清理完成: {pattern}")
                else:
                    self.logger.warning(f"部分清理失败: {pattern}")

            except Exception as e:
                self.logger.warning(f"清理 {pattern} 时出错: {e}")

        return True

    def _execute_migrations(self) -> bool:
        """执行文件迁移"""
        self.logger.info("执行文件迁移...")

        success_count = 0
        for migration in self.migration_rules:
            if self._execute_single_migration(migration):
                success_count += 1
            else:
                if migration.required:
                    self.logger.error(f"必需迁移失败: {migration.source}")
                    return False

        self.logger.info(f"迁移完成: {success_count}/{len(self.migration_rules)}")
        return True

    def _execute_single_migration(self, migration: FileMigration) -> bool:
        """执行单个文件迁移"""
        source_path = self.project_root / migration.source
        dest_path = self.project_root / migration.destination

        try:
            # 检查源文件是否存在
            if not source_path.exists():
                message = f"源文件不存在: {migration.source}"
                self._record_migration_result(migration, MigrationStatus.SKIPPED, message)
                self.logger.warning(message)
                return not migration.required

            # 检查目标目录是否存在
            if not dest_path.parent.exists():
                if not self.dry_run:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

            # 执行迁移
            if self.dry_run:
                message = f"[DRY RUN] 迁移 {migration.source} -> {migration.destination}"
                self.logger.info(message)
                self._record_migration_result(migration, MigrationStatus.COMPLETED, message)
                return True

            # 创建备份（如果需要）
            backup_path = None
            if migration.backup_required and self.backup:
                backup_path = self.backup_dir / migration.source
                shutil.copy2(source_path, backup_path)

            # 移动文件
            if source_path.is_file():
                shutil.move(str(source_path), str(dest_path))
            else:
                shutil.move(str(source_path), str(dest_path))

            message = f"迁移完成: {migration.source} -> {migration.destination}"
            self.logger.info(message)
            self._record_migration_result(migration, MigrationStatus.COMPLETED, message, str(backup_path))
            return True

        except Exception as e:
            message = f"迁移失败 {migration.source}: {e}"
            self.logger.error(message)
            self._record_migration_result(migration, MigrationStatus.FAILED, message)
            return False

    def _record_migration_result(self, migration: FileMigration, status: MigrationStatus,
                               message: str, backup_path: Optional[str] = None):
        """记录迁移结果"""
        result = MigrationResult(
            source=migration.source,
            destination=migration.destination,
            status=status,
            message=message,
            backup_path=backup_path
        )
        self.migration_results.append(result)

    def _postprocess(self) -> bool:
        """后处理阶段"""
        self.logger.info("执行后处理...")

        try:
            # 更新.gitignore
            if not self._update_gitignore():
                return False

            # 生成迁移脚本的改进版本
            if not self._generate_improved_gitignore():
                return False

            return True

        except Exception as e:
            self.logger.error(f"后处理失败: {e}")
            return False

    def _update_gitignore(self) -> bool:
        """更新.gitignore文件"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Jupyter Notebook
.ipynb_checkpoints

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Editor specific
.cursor/
.cursorindexingignore

# Project specific
refactor_backup_*
refactor.log
"""

        try:
            gitignore_path = self.project_root / ".gitignore"
            if self.dry_run:
                self.logger.info(f"[DRY RUN] 更新 .gitignore")
                return True

            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)

            self.logger.info("更新 .gitignore 完成")
            return True

        except Exception as e:
            self.logger.error(f"更新 .gitignore 失败: {e}")
            return False

    def _generate_improved_gitignore(self) -> bool:
        """生成改进的.gitignore文件"""
        improved_gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Jupyter Notebook
.ipynb_checkpoints

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Editor specific
.cursor/
.cursorindexingignore

# Project specific
refactor_backup_*
refactor.log

# Development tools
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# profiling data
.prof

# Sphinx documentation
docs/_build/

# Backup files
*.bak
*.backup
*~

# Temporary files
*.tmp
*.temp
"""

        try:
            improved_path = self.project_root / ".gitignore_improved"
            with open(improved_path, 'w', encoding='utf-8') as f:
                f.write(improved_gitignore)

            self.logger.info("生成改进的 .gitignore 文件: .gitignore_improved")
            return True

        except Exception as e:
            self.logger.error(f"生成改进的 .gitignore 失败: {e}")
            return False

    def _generate_report(self):
        """生成重构报告"""
        self.logger.info("生成重构报告...")

        # 统计结果
        total = len(self.migration_results)
        completed = sum(1 for r in self.migration_results if r.status == MigrationStatus.COMPLETED)
        failed = sum(1 for r in self.migration_results if r.status == MigrationStatus.FAILED)
        skipped = sum(1 for r in self.migration_results if r.status == MigrationStatus.SKIPPED)

        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_migrations": total,
                "completed": completed,
                "failed": failed,
                "skipped": skipped,
                "success_rate": f"{(completed/total*100):.1f}%" if total > 0 else "0%"
            },
            "details": [
                {
                    "source": r.source,
                    "destination": r.destination,
                    "status": r.status.value,
                    "message": r.message,
                    "backup_path": r.backup_path
                }
                for r in self.migration_results
            ],
            "recommendations": self._generate_recommendations()
        }

        # 保存报告
        report_path = self.project_root / "refactor_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"重构报告已生成: {report_path}")

            # 打印摘要
            print("\\n" + "="*50)
            print("重构完成摘要")
            print("="*50)
            print(f"总迁移数: {total}")
            print(f"成功: {completed}")
            print(f"失败: {failed}")
            print(f"跳过: {skipped}")
            print(f"成功率: {report['summary']['success_rate']}")
            print("="*50)

        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")

    def _generate_recommendations(self) -> List[str]:
        """生成后续建议"""
        recommendations = [
            "运行所有测试以确保功能完整性",
            "检查新目录结构是否符合预期",
            "更新CI/CD配置以适应新结构",
            "更新开发文档中的路径引用",
            "考虑重构源代码模块结构",
            "建立持续的文件组织维护机制"
        ]

        # 根据迁移结果添加特定建议
        failed_migrations = [r for r in self.migration_results if r.status == MigrationStatus.FAILED]
        if failed_migrations:
            recommendations.append(f"手动处理 {len(failed_migrations)} 个失败的迁移")

        return recommendations


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SPDX Scanner自动化重构工具")
    parser.add_argument("--dry-run", action="store_true",
                       help="预览模式，不实际执行文件操作")
    parser.add_argument("--backup", action="store_true",
                       help="在操作前创建备份")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出模式")
    parser.add_argument("--skip-tests", action="store_true",
                       help="跳过测试文件迁移")
    parser.add_argument("--skip-docs", action="store_true",
                       help="跳过文档文件迁移")

    args = parser.parse_args()

    # 创建重构器
    refactor = ProjectRefactor(
        dry_run=args.dry_run,
        backup=args.backup,
        verbose=args.verbose
    )

    print("SPDX Scanner 自动化重构工具")
    print("="*40)

    if args.dry_run:
        print("⚠️  运行在预览模式下 - 不会实际修改文件")

    if args.backup:
        print("💾 将创建备份文件")

    print("\\n开始重构...")

    # 执行重构
    success = refactor.run()

    if success:
        print("\\n✅ 重构完成!")
        if not args.dry_run:
            print("请检查重构报告并运行测试以验证结果。")
    else:
        print("\\n❌ 重构失败! 请检查日志文件获取详细信息。")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())