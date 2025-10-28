#!/usr/bin/env python3
"""
自动修正器

自动发现并修复验证过程中发现的问题，包括代码质量问题、配置文件问题等。
"""

import sys
import os
import re
import ast
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import subprocess
import logging

# 添加项目根目录和src到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from spdx_scanner.corrector import SPDXCorrector
    from spdx_scanner.config import ConfigManager
except ImportError as e:
    print(f"导入错误: {e}")


@dataclass
class AutoFixResult:
    """自动修正结果"""
    success: bool
    fixes_applied: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    backup_files: List[str]
    recommendations: List[str]


class AutoCorrector:
    """自动修正器"""

    def __init__(self, project_root: Path, config: Dict[str, Any]):
        self.project_root = project_root
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.backup_dir = project_root / ".verification_backups"

        # 修正策略配置
        self.strategies = {
            'fix_code_quality': config.get('fix_code_quality', True),
            'fix_test_issues': config.get('fix_test_issues', True),
            'fix_configuration': config.get('fix_configuration', True),
            'fix_imports': config.get('fix_imports', True),
            'fix_formatting': config.get('fix_formatting', True)
        }

        # 备份设置
        self.create_backups = config.get('backup_files', True)

    def auto_fix_issues(self, issues: List[Dict[str, Any]]) -> AutoFixResult:
        """自动修复发现的问题"""
        print("🔧 开始自动修复问题...")

        fixes_applied = []
        errors = []
        backup_files = []

        # 创建备份目录
        if self.create_backups:
            self.backup_dir.mkdir(exist_ok=True)

        try:
            # 按严重级别分组问题
            high_priority = [issue for issue in issues if issue.get('severity') == 'HIGH']
            medium_priority = [issue for issue in issues if issue.get('severity') == 'MEDIUM']
            low_priority = [issue for issue in issues if issue.get('severity') == 'LOW']

            print(f"  发现 {len(high_priority)} 个高优先级问题")
            print(f"  发现 {len(medium_priority)} 个中优先级问题")
            print(f"  发现 {len(low_priority)} 个低优先级问题")

            # 1. 修复高优先级问题
            if high_priority:
                print("  修复高优先级问题...")
                high_fixes, high_errors = self._fix_high_priority_issues(high_priority)
                fixes_applied.extend(high_fixes)
                errors.extend(high_errors)

            # 2. 修复中优先级问题
            if medium_priority:
                print("  修复中优先级问题...")
                medium_fixes, medium_errors = self._fix_medium_priority_issues(medium_priority)
                fixes_applied.extend(medium_fixes)
                errors.extend(medium_errors)

            # 3. 修复低优先级问题
            if low_priority:
                print("  修复低优先级问题...")
                low_fixes, low_errors = self._fix_low_priority_issues(low_priority)
                fixes_applied.extend(low_fixes)
                errors.extend(low_errors)

            # 4. 清理备份文件（如果不需要）
            if not self.config.get('keep_backups', False):
                self._cleanup_backups()

            print(f"  修复完成: {len(fixes_applied)} 个修复, {len(errors)} 个错误")

        except Exception as e:
            self.logger.error(f"自动修复过程中发生错误: {e}")
            errors.append({
                'type': 'auto_fix_error',
                'message': f'自动修复异常: {str(e)}',
                'severity': 'HIGH'
            })

        return AutoFixResult(
            success=len(errors) == 0,
            fixes_applied=fixes_applied,
            errors=errors,
            backup_files=backup_files,
            recommendations=self._generate_fix_recommendations(fixes_applied, errors)
        )

    def _fix_high_priority_issues(self, issues: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """修复高优先级问题"""
        fixes = []
        errors = []

        for issue in issues:
            try:
                fix_result = self._fix_single_issue(issue, priority='HIGH')
                if fix_result['success']:
                    fixes.append(fix_result['fix'])
                else:
                    errors.append(fix_result['error'])
            except Exception as e:
                errors.append({
                    'type': 'fix_error',
                    'issue': issue,
                    'message': f'修复高优先级问题时异常: {str(e)}',
                    'severity': 'HIGH'
                })

        return fixes, errors

    def _fix_medium_priority_issues(self, issues: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """修复中优先级问题"""
        fixes = []
        errors = []

        for issue in issues:
            try:
                fix_result = self._fix_single_issue(issue, priority='MEDIUM')
                if fix_result['success']:
                    fixes.append(fix_result['fix'])
                else:
                    errors.append(fix_result['error'])
            except Exception as e:
                errors.append({
                    'type': 'fix_error',
                    'issue': issue,
                    'message': f'修复中优先级问题时异常: {str(e)}',
                    'severity': 'MEDIUM'
                })

        return fixes, errors

    def _fix_low_priority_issues(self, issues: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """修复低优先级问题"""
        fixes = []
        errors = []

        for issue in issues:
            try:
                fix_result = self._fix_single_issue(issue, priority='LOW')
                if fix_result['success']:
                    fixes.append(fix_result['fix'])
                else:
                    errors.append(fix_result['error'])
            except Exception as e:
                errors.append({
                    'type': 'fix_error',
                    'issue': issue,
                    'message': f'修复低优先级问题时异常: {str(e)}',
                    'severity': 'LOW'
                })

        return fixes, errors

    def _fix_single_issue(self, issue: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """修复单个问题"""
        issue_type = issue.get('type')
        file_path = issue.get('file')
        message = issue.get('message', '')

        if issue_type == 'import_error':
            return self._fix_import_error(issue)
        elif issue_type == 'high_complexity':
            return self._fix_high_complexity(issue)
        elif issue_type == 'long_function':
            return self._fix_long_function(issue)
        elif issue_type == 'format_violation':
            return self._fix_format_violation(issue)
        elif issue_type == 'config_error':
            return self._fix_config_error(issue)
        elif issue_type == 'missing_file':
            return self._fix_missing_file(issue)
        elif issue_type == 'style_violation':
            return self._fix_style_violation(issue)
        else:
            return {
                'success': False,
                'error': {
                    'type': 'unsupported_issue',
                    'issue': issue,
                    'message': f'不支持的问题类型: {issue_type}',
                    'severity': priority
                }
            }

    def _fix_import_error(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """修复导入错误"""
        module = issue.get('module')

        # 尝试安装缺失的模块
        if module:
            try:
                # 简单的pip install尝试
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', module
                ], capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    return {
                        'success': True,
                        'fix': {
                            'type': 'install_dependency',
                            'module': module,
                            'description': f'自动安装缺失的依赖: {module}',
                            'method': 'pip install'
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': {
                            'type': 'install_failed',
                            'module': module,
                            'message': f'无法安装依赖 {module}: {result.stderr}',
                            'severity': 'HIGH'
                        }
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': {
                        'type': 'install_error',
                        'module': module,
                        'message': f'安装依赖时异常: {str(e)}',
                        'severity': 'HIGH'
                    }
                }

        return {
            'success': False,
            'error': {
                'type': 'invalid_import_issue',
                'message': '无效的导入错误信息',
                'severity': 'HIGH'
            }
        }

    def _fix_high_complexity(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """修复高复杂度代码"""
        file_path = issue.get('file')
        complexity = issue.get('metric', 0)

        if not file_path:
            return {
                'success': False,
                'error': {
                    'type': 'missing_file_path',
                    'message': '缺少文件路径信息',
                    'severity': 'MEDIUM'
                }
            }

        full_path = self.project_root / file_path
        if not full_path.exists():
            return {
                'success': False,
                'error': {
                    'type': 'file_not_found',
                    'file': file_path,
                    'message': '文件不存在',
                    'severity': 'MEDIUM'
                }
            }

        # 尝试提取复杂函数并提供重构建议
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            complex_functions = self._find_complex_functions(tree)

            if complex_functions:
                # 创建重构建议文件
                suggestion_file = full_path.with_suffix('.refactor_suggestions.txt')
                with open(suggestion_file, 'w', encoding='utf-8') as f:
                    f.write(f"代码重构建议 - {file_path}\n")
                    f.write("=" * 50 + "\n\n")
                    for func_name, func_complexity in complex_functions:
                        f.write(f"函数: {func_name}\n")
                        f.write(f"复杂度: {func_complexity}\n")
                        f.write("建议:\n")
                        f.write("- 拆分为更小的函数\n")
                        f.write("- 减少嵌套层级\n")
                        f.write("- 使用早期返回减少分支\n")
                        f.write("\n" + "-" * 30 + "\n\n")

                return {
                    'success': True,
                    'fix': {
                        'type': 'complexity_refactor',
                        'file': file_path,
                        'description': f'为高复杂度文件生成重构建议: {file_path}',
                        'suggestion_file': str(suggestion_file),
                        'complex_functions': complex_functions
                    }
                }
            else:
                return {
                    'success': False,
                    'error': {
                        'type': 'no_complex_functions',
                        'file': file_path,
                        'message': '未找到复杂函数',
                        'severity': 'MEDIUM'
                    }
                }

        except Exception as e:
            return {
                'success': False,
                'error': {
                    'type': 'complexity_analysis_error',
                    'file': file_path,
                    'message': f'复杂度分析异常: {str(e)}',
                    'severity': 'MEDIUM'
                }
            }

    def _find_complex_functions(self, tree: ast.AST) -> List[Tuple[str, int]]:
        """查找复杂函数"""
        complex_functions = []

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_complexity = 0
                self.current_function = None

            def visit_FunctionDef(self, node):
                old_complexity = self.current_complexity
                old_function = self.current_function

                self.current_function = node.name
                self.current_complexity = 1  # 基础复杂度

                self.generic_visit(node)

                if self.current_complexity > 10:  # 复杂度阈值
                    complex_functions.append((node.name, self.current_complexity))

                self.current_complexity = old_complexity
                self.current_function = old_function

            def visit_If(self, node):
                self.current_complexity += 1
                self.generic_visit(node)

            def visit_While(self, node):
                self.current_complexity += 1
                self.generic_visit(node)

            def visit_For(self, node):
                self.current_complexity += 1
                self.generic_visit(node)

            def visit_ExceptHandler(self, node):
                self.current_complexity += 1
                self.generic_visit(node)

        visitor = ComplexityVisitor()
        visitor.visit(tree)
        return complex_functions

    def _fix_long_function(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """修复长函数"""
        file_path = issue.get('file')
        function_length = issue.get('metric', 0)

        if not file_path:
            return {'success': False, 'error': {'type': 'missing_file_path', 'message': '缺少文件路径', 'severity': 'MEDIUM'}}

        full_path = self.project_root / file_path
        if not full_path.exists():
            return {'success': False, 'error': {'type': 'file_not_found', 'file': file_path, 'message': '文件不存在', 'severity': 'MEDIUM'}}

        # 创建函数拆分建议
        suggestion_file = full_path.with_suffix('.function_split_suggestions.txt')
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            with open(suggestion_file, 'w', encoding='utf-8') as f:
                f.write(f"函数拆分建议 - {file_path}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"检测到长度超过50行的函数 (当前: {function_length} 行)\n\n")
                f.write("建议:\n")
                f.write("1. 将长函数拆分为多个较小的函数\n")
                f.write("2. 每个函数应该只负责一个任务\n")
                f.write("3. 使用有意义的函数名\n")
                f.write("4. 考虑使用装饰器或生成器模式\n")

            return {
                'success': True,
                'fix': {
                    'type': 'function_split',
                    'file': file_path,
                    'description': f'为长函数生成拆分建议: {file_path}',
                    'suggestion_file': str(suggestion_file),
                    'current_length': function_length
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': {
                    'type': 'split_suggestion_error',
                    'file': file_path,
                    'message': f'生成拆分建议异常: {str(e)}',
                    'severity': 'MEDIUM'
                }
            }

    def _fix_format_violation(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """修复格式违规"""
        # 尝试运行black格式化工具
        try:
            result = subprocess.run([
                'black', '--check', '--diff', 'src/', 'tests/'
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                # 尝试自动格式化
                format_result = subprocess.run([
                    'black', 'src/', 'tests/'
                ], cwd=self.project_root, capture_output=True, text=True, timeout=60)

                if format_result.returncode == 0:
                    return {
                        'success': True,
                        'fix': {
                            'type': 'format_fix',
                            'tool': 'black',
                            'description': '使用black自动格式化代码',
                            'changes': format_result.stdout
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': {
                            'type': 'format_fix_failed',
                            'tool': 'black',
                            'message': f'自动格式化失败: {format_result.stderr}',
                            'severity': 'LOW'
                        }
                    }
            else:
                return {
                    'success': True,
                    'fix': {
                        'type': 'format_check',
                        'tool': 'black',
                        'description': '代码格式检查通过'
                    }
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': {
                    'type': 'format_timeout',
                    'tool': 'black',
                    'message': '格式化工具超时',
                    'severity': 'LOW'
                }
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': {
                    'type': 'tool_not_found',
                    'tool': 'black',
                    'message': 'black格式化工具未安装',
                    'severity': 'LOW'
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': {
                    'type': 'format_error',
                    'tool': 'black',
                    'message': f'格式化异常: {str(e)}',
                    'severity': 'LOW'
                }
            }

    def _fix_config_error(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """修复配置错误"""
        try:
            config_manager = ConfigManager(str(self.project_root))

            # 检查并创建默认配置文件
            config_file = self.project_root / "spdx-scanner.config.json"
            if not config_file.exists():
                default_config = {
                    "project_name": "SPDX Scanner",
                    "default_license": "MIT",
                    "copyright_holder": "SPDX Scanner Team",
                    "scanner_settings": {
                        "source_file_extensions": [".c", ".cpp", ".h", ".go"],
                        "exclude_patterns": ["**/node_modules/**", "**/build/**"]
                    },
                    "correction_settings": {
                        "default_license": "MIT",
                        "create_backups": True,
                        "dry_run": False
                    },
                    "validation_rules": {
                        "require_license_identifier": True,
                        "require_copyright": True,
                        "allow_unknown_licenses": False
                    }
                }

                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)

                return {
                    'success': True,
                    'fix': {
                        'type': 'config_creation',
                        'file': str(config_file),
                        'description': '创建默认配置文件',
                        'config': default_config
                    }
                }
            else:
                return {
                    'success': True,
                    'fix': {
                        'type': 'config_check',
                        'file': str(config_file),
                        'description': '配置文件存在，检查通过'
                    }
                }

        except Exception as e:
            return {
                'success': False,
                'error': {
                    'type': 'config_fix_error',
                    'message': f'配置文件修复异常: {str(e)}',
                    'severity': 'MEDIUM'
                }
            }

    def _fix_missing_file(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """修复缺失文件"""
        file_name = issue.get('file', '')

        # 尝试创建必要的文件
        if file_name == 'CLI入口点':
            cli_file = self.project_root / "src" / "spdx_scanner" / "__main__.py"
            cli_content = '''#!/usr/bin/env python3
"""SPDX Scanner CLI入口点"""

import sys
from spdx_scanner.cli import main

if __name__ == "__main__":
    sys.exit(main())
'''

            try:
                cli_file.parent.mkdir(parents=True, exist_ok=True)
                cli_file.write_text(cli_content)

                return {
                    'success': True,
                    'fix': {
                        'type': 'file_creation',
                        'file': str(cli_file),
                        'description': '创建CLI入口点文件',
                        'content': 'CLI入口点脚本'
                    }
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': {
                        'type': 'file_creation_error',
                        'file': str(cli_file),
                        'message': f'创建CLI文件异常: {str(e)}',
                        'severity': 'MEDIUM'
                    }
                }

        return {
            'success': False,
            'error': {
                'type': 'unsupported_missing_file',
                'file': file_name,
                'message': f'不支持的缺失文件类型: {file_name}',
                'severity': 'MEDIUM'
            }
        }

    def _fix_style_violation(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """修复样式违规"""
        # 尝试使用flake8自动修复某些问题
        try:
            result = subprocess.run([
                'flake8', 'src/', 'tests/', '--fix', '--ignore=E501'
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {
                    'success': True,
                    'fix': {
                        'type': 'style_fix',
                        'tool': 'flake8',
                        'description': '使用flake8自动修复样式问题'
                    }
                }
            else:
                return {
                    'success': False,
                    'error': {
                        'type': 'style_fix_failed',
                        'tool': 'flake8',
                        'message': f'自动修复样式问题失败: {result.stderr}',
                        'severity': 'LOW'
                    }
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': {
                    'type': 'style_timeout',
                    'tool': 'flake8',
                    'message': '样式修复工具超时',
                    'severity': 'LOW'
                }
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': {
                    'type': 'tool_not_found',
                    'tool': 'flake8',
                    'message': 'flake8工具未安装',
                    'severity': 'LOW'
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': {
                    'type': 'style_error',
                    'tool': 'flake8',
                    'message': f'样式修复异常: {str(e)}',
                    'severity': 'LOW'
                }
            }

    def _cleanup_backups(self):
        """清理备份文件"""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
                print(f"  清理备份目录: {self.backup_dir}")
        except Exception as e:
            self.logger.warning(f"清理备份文件失败: {e}")

    def _generate_fix_recommendations(self, fixes: List[Dict], errors: List[Dict]) -> List[str]:
        """生成修复建议"""
        recommendations = []

        # 基于修复的类型生成建议
        fix_types = {}
        for fix in fixes:
            fix_type = fix.get('type')
            fix_types[fix_type] = fix_types.get(fix_type, 0) + 1

        if 'install_dependency' in fix_types:
            recommendations.append("检查项目的依赖管理，确保所有依赖都正确声明")

        if 'format_fix' in fix_types:
            recommendations.append("建立代码格式化流程，在代码提交前自动格式化")

        if 'config_creation' in fix_types:
            recommendations.append("根据项目需求自定义配置文件，设置合适的默认值")

        if 'complexity_refactor' in fix_types:
            recommendations.append("优先重构高复杂度代码，提高代码可维护性")

        if errors:
            recommendations.append("检查自动修复失败的错误，手动解决遗留问题")

        # 通用建议
        recommendations.extend([
            "定期运行自动化验证，及时发现和修复问题",
            "建立代码质量监控，跟踪质量指标变化",
            "设置预提交钩子，防止问题代码提交",
            "建立代码审查流程，确保代码质量"
        ])

        return recommendations
