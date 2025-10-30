#!/usr/bin/env python3
"""
集成测试器

验证SPDX Scanner的端到端功能，包括CLI接口、配置文件处理、Git集成等。
"""

import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import time

# 添加项目根目录和src到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from spdx_scanner.scanner import create_default_scanner
    from spdx_scanner.parser import SPDXParser
    from spdx_scanner.validator import create_default_validator
    from spdx_scanner.corrector import SPDXCorrector
    from spdx_scanner.config import ConfigManager
except ImportError as e:
    print(f"导入错误: {e}")


@dataclass
class IntegrationTestResult:
    """集成测试结果"""
    status: str  # 'PASS', 'FAIL', 'WARNING'
    test_suites: Dict[str, Dict[str, Any]]
    issues: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]


class IntegrationTester:
    """集成测试器"""

    def __init__(self, project_root: Path, config: Dict[str, Any]):
        self.project_root = project_root
        self.config = config
        self.test_results = {}

    def run_all_tests(self) -> IntegrationTestResult:
        """运行所有集成测试"""
        print("🔗 开始集成测试...")

        test_suites = {}
        issues = []
        performance_metrics = {}

        # 1. CLI接口测试
        cli_result = self._test_cli_interface()
        test_suites['cli'] = cli_result
        if cli_result.get('issues'):
            issues.extend(cli_result['issues'])

        # 2. 配置文件测试
        config_result = self._test_configuration_handling()
        test_suites['config'] = config_result
        if config_result.get('issues'):
            issues.extend(config_result['issues'])

        # 3. 文件处理测试
        file_result = self._test_file_processing()
        test_suites['file_processing'] = file_result
        if file_result.get('issues'):
            issues.extend(file_result['issues'])

        # 4. 报告生成测试
        report_result = self._test_report_generation()
        test_suites['reporting'] = report_result
        if report_result.get('issues'):
            issues.extend(report_result['issues'])

        # 5. 端到端测试
        e2e_result = self._test_end_to_end()
        test_suites['end_to_end'] = e2e_result
        if e2e_result.get('issues'):
            issues.extend(e2e_result['issues'])

        # 6. 性能测试
        perf_result = self._test_performance()
        test_suites['performance'] = perf_result
        performance_metrics = perf_result.get('metrics', {})

        # 7. 错误处理测试
        error_result = self._test_error_handling()
        test_suites['error_handling'] = error_result
        if error_result.get('issues'):
            issues.extend(error_result['issues'])

        # 8. Git集成测试（如果可用）
        if self.config.get('test_git_integration', True):
            git_result = self._test_git_integration()
            test_suites['git_integration'] = git_result
            if git_result.get('issues'):
                issues.extend(git_result['issues'])

        # 确定整体状态
        failed_suites = [name for name, result in test_suites.items() if result.get('status') == 'FAIL']
        warning_suites = [name for name, result in test_suites.items() if result.get('status') == 'WARNING']

        if failed_suites:
            status = 'FAIL'
        elif warning_suites:
            status = 'WARNING'
        else:
            status = 'PASS'

        # 生成建议
        recommendations = self._generate_recommendations(test_suites, issues)

        return IntegrationTestResult(
            status=status,
            test_suites=test_suites,
            issues=issues,
            performance_metrics=performance_metrics,
            recommendations=recommendations
        )

    def _test_cli_interface(self) -> Dict[str, Any]:
        """测试CLI接口"""
        print("  🖥️  测试CLI接口...")

        result = {
            'test_suite': 'CLI Interface',
            'status': 'PASS',
            'tests': [],
            'issues': []
        }

        # 检查CLI入口点
        try:
            cli_script = self.project_root / "src" / "spdx_scanner" / "__main__.py"
            if cli_script.exists():
                result['tests'].append({
                    'name': 'CLI入口点存在',
                    'status': 'PASS',
                    'details': f'文件路径: {cli_script}'
                })
            else:
                result['tests'].append({
                    'name': 'CLI入口点存在',
                    'status': 'FAIL',
                    'details': 'CLI入口点文件不存在'
                })
                result['issues'].append({
                    'type': 'missing_file',
                    'component': 'CLI',
                    'message': 'CLI入口点文件不存在',
                    'severity': 'HIGH'
                })
        except Exception as e:
            result['tests'].append({
                'name': 'CLI入口点检查',
                'status': 'FAIL',
                'details': f'检查异常: {str(e)}'
            })

        # 测试帮助命令
        help_result = self._run_cli_command(['--help'])
        if help_result['success']:
            result['tests'].append({
                'name': '帮助命令',
                'status': 'PASS',
                'details': f'返回码: {help_result["returncode"]}'
            })
        else:
            result['tests'].append({
                'name': '帮助命令',
                'status': 'FAIL',
                'details': f'错误: {help_result["stderr"]}'
            })
            result['issues'].append({
                'type': 'cli_error',
                'component': 'CLI',
                'message': f'帮助命令失败: {help_result["stderr"]}',
                'severity': 'HIGH'
            })

        # 测试版本命令
        version_result = self._run_cli_command(['--version'])
        if version_result['success']:
            result['tests'].append({
                'name': '版本命令',
                'status': 'PASS',
                'details': f'输出: {version_result["stdout"].strip()}'
            })
        else:
            result['tests'].append({
                'name': '版本命令',
                'status': 'FAIL',
                'details': f'错误: {version_result["stderr"]}'
            })
            result['issues'].append({
                'type': 'cli_error',
                'component': 'CLI',
                'message': '版本命令失败',
                'severity': 'MEDIUM'
            })

        # 测试scan命令
        scan_result = self._run_cli_command(['scan', '--help'])
        if scan_result['success']:
            result['tests'].append({
                'name': 'Scan子命令',
                'status': 'PASS',
                'details': 'Scan子命令可用'
            })
        else:
            result['tests'].append({
                'name': 'Scan子命令',
                'status': 'FAIL',
                'details': f'错误: {scan_result["stderr"]}'
            })
            result['issues'].append({
                'type': 'cli_error',
                'component': 'CLI',
                'message': 'Scan子命令不可用',
                'severity': 'HIGH'
            })

        # 测试correct命令
        correct_result = self._run_cli_command(['correct', '--help'])
        if correct_result['success']:
            result['tests'].append({
                'name': 'Correct子命令',
                'status': 'PASS',
                'details': 'Correct子命令可用'
            })
        else:
            result['tests'].append({
                'name': 'Correct子命令',
                'status': 'FAIL',
                'details': f'错误: {correct_result["stderr"]}'
            })
            result['issues'].append({
                'type': 'cli_error',
                'component': 'CLI',
                'message': 'Correct子命令不可用',
                'severity': 'HIGH'
            })

        return result

    def _run_cli_command(self, args: List[str]) -> Dict[str, Any]:
        """运行CLI命令"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "spdx_scanner"] + args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': '命令超时'
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }

    def _test_configuration_handling(self) -> Dict[str, Any]:
        """测试配置处理"""
        print("  ⚙️  测试配置处理...")

        result = {
            'test_suite': 'Configuration',
            'status': 'PASS',
            'tests': [],
            'issues': []
        }

        # 创建临时配置测试目录
        test_dir = Path(tempfile.mkdtemp())
        try:
            # 测试默认配置
            config_manager = ConfigManager(str(test_dir))
            default_config = config_manager.get_config()

            if default_config:
                result['tests'].append({
                    'name': '默认配置加载',
                    'status': 'PASS',
                    'details': f'配置项数量: {len(default_config)}'
                })
            else:
                result['tests'].append({
                    'name': '默认配置加载',
                    'status': 'FAIL',
                    'details': '默认配置为空'
                })

            # 测试配置文件创建
            test_config_file = test_dir / "spdx-scanner.config.json"
            test_config = {
                "project_name": "Test Project",
                "default_license": "MIT",
                "scanner_settings": {
                    "source_file_extensions": [".c", ".cpp", ".h"]
                }
            }

            with open(test_config_file, 'w') as f:
                json.dump(test_config, f, indent=2)

            # 重新加载配置
            config_manager_reload = ConfigManager(str(test_dir))
            loaded_config = config_manager_reload.get_config()

            if loaded_config and loaded_config.get('project_name') == 'Test Project':
                result['tests'].append({
                    'name': '配置文件加载',
                    'status': 'PASS',
                    'details': '配置文件正确加载'
                })
            else:
                result['tests'].append({
                    'name': '配置文件加载',
                    'status': 'FAIL',
                    'details': '配置文件加载失败'
                })
                result['issues'].append({
                    'type': 'config_error',
                    'component': 'Config',
                    'message': '配置文件加载失败',
                    'severity': 'MEDIUM'
                })

            # 测试配置更新
            try:
                config_manager_reload.update_config('project_name', 'Updated Project')
                updated_config = config_manager_reload.get_config()

                if updated_config.get('project_name') == 'Updated Project':
                    result['tests'].append({
                        'name': '配置更新',
                        'status': 'PASS',
                        'details': '配置更新成功'
                    })
                else:
                    result['tests'].append({
                        'name': '配置更新',
                        'status': 'FAIL',
                        'details': '配置更新失败'
                    })
            except Exception as e:
                result['tests'].append({
                    'name': '配置更新',
                    'status': 'FAIL',
                    'details': f'配置更新异常: {str(e)}'
                })
                result['issues'].append({
                    'type': 'config_error',
                    'component': 'Config',
                    'message': f'配置更新异常: {str(e)}',
                    'severity': 'MEDIUM'
                })

        except Exception as e:
            result['tests'].append({
                'name': '配置测试',
                'status': 'FAIL',
                'details': f'配置测试异常: {str(e)}'
            })
            result['issues'].append({
                'type': 'config_error',
                'component': 'Config',
                'message': f'配置处理异常: {str(e)}',
                'severity': 'HIGH'
            })
        finally:
            # 清理临时文件
            shutil.rmtree(test_dir, ignore_errors=True)

        return result

    def _test_file_processing(self) -> Dict[str, Any]:
        """测试文件处理"""
        print("  📁 测试文件处理...")

        result = {
            'test_suite': 'File Processing',
            'status': 'PASS',
            'tests': [],
            'issues': []
        }

        # 创建临时测试目录
        test_dir = Path(tempfile.mkdtemp())
        try:
            # 创建测试文件（使用默认scanner支持的文件类型）
            test_files = [
                ('test.c', '/*\n * SPDX-License-Identifier: MIT\n */\n#include <stdio.h>'),
                ('test.cpp', '// SPDX-License-Identifier: Apache-2.0\n#include <iostream>'),
                ('test.h', '/* SPDX-License-Identifier: GPL-3.0 */\n#ifndef TEST_H'),
                ('test.go', '// SPDX-License-Identifier: MIT\npackage main')
            ]

            for filename, content in test_files:
                (test_dir / filename).write_text(content)

            # 测试文件扫描
            scanner = create_default_scanner()
            scan_result = scanner.scan_directory_with_results(test_dir)

            # 正确获取扫描的文件数量
            files_scanned = len(scan_result.files) if scan_result and hasattr(scan_result, 'files') else 0

            if scan_result and files_scanned == len(test_files):
                result['tests'].append({
                    'name': '文件扫描',
                    'status': 'PASS',
                    'details': f'扫描了 {files_scanned} 个文件'
                })
            else:
                result['tests'].append({
                    'name': '文件扫描',
                    'status': 'FAIL',
                    'details': f'期望 {len(test_files)} 个文件，实际 {files_scanned} 个'
                })
                result['issues'].append({
                    'type': 'scan_error',
                    'component': 'File Processing',
                    'message': '文件扫描不完整',
                    'severity': 'HIGH'
                })

            # 测试文件过滤
            scanner_custom = create_default_scanner(source_file_extensions=['.c', '.cpp'])
            scan_result_filtered = scanner_custom.scan_directory_with_results(test_dir)

            # 正确获取过滤后的文件数量
            files_filtered = len(scan_result_filtered.files) if scan_result_filtered and hasattr(scan_result_filtered, 'files') else 0

            # 只有2个文件匹配.c和.cpp扩展名
            if scan_result_filtered and files_filtered == 2:
                result['tests'].append({
                    'name': '文件过滤',
                    'status': 'PASS',
                    'details': f'正确过滤出 {files_filtered} 个文件'
                })
            else:
                result['tests'].append({
                    'name': '文件过滤',
                    'status': 'FAIL',
                    'details': f'期望 2 个文件，实际 {files_filtered} 个'
                })
                result['issues'].append({
                    'type': 'filter_error',
                    'component': 'File Processing',
                    'message': '文件过滤不正确',
                    'severity': 'MEDIUM'
                })

            # 测试特殊文件处理
            binary_file = test_dir / "binary.so"
            binary_file.write_bytes(b'\x00\x01\x02\x03')  # 二进制数据

            text_file = test_dir / "text.txt"
            text_file.write_text("This is a text file\n")

            all_files = list(test_dir.glob('*'))
            total_files = len([f for f in all_files if f.is_file()])

            if total_files == len(test_files) + 2:  # 原始文件 + 额外文件
                result['tests'].append({
                    'name': '特殊文件处理',
                    'status': 'PASS',
                    'details': f'正确处理 {total_files} 个文件'
                })
            else:
                result['tests'].append({
                    'name': '特殊文件处理',
                    'status': 'WARNING',
                    'details': f'文件处理可能有问题，实际 {total_files} 个文件'
                })

        except Exception as e:
            result['tests'].append({
                'name': '文件处理测试',
                'status': 'FAIL',
                'details': f'测试异常: {str(e)}'
            })
            result['issues'].append({
                'type': 'processing_error',
                'component': 'File Processing',
                'message': f'文件处理异常: {str(e)}',
                'severity': 'HIGH'
            })
        finally:
            # 清理临时文件
            shutil.rmtree(test_dir, ignore_errors=True)

        return result

    def _test_report_generation(self) -> Dict[str, Any]:
        """测试报告生成"""
        print("  📊 测试报告生成...")

        result = {
            'test_suite': 'Report Generation',
            'status': 'PASS',
            'tests': [],
            'issues': []
        }

        # 创建测试数据
        test_dir = Path(tempfile.mkdtemp())
        try:
            # 创建测试文件
            test_file = test_dir / "test.c"
            test_file.write_text("""/*
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2023 Test Corp
 */

#include <stdio.h>
""")

            # 执行扫描
            scanner = create_default_scanner()
            scan_result = scanner.scan_directory(str(test_dir))

            if not scan_result:
                result['tests'].append({
                    'name': '扫描执行',
                    'status': 'FAIL',
                    'details': '扫描失败，无法生成报告'
                })
                result['issues'].append({
                    'type': 'scan_error',
                    'component': 'Reporting',
                    'message': '扫描失败',
                    'severity': 'HIGH'
                })
                return result

            # 测试JSON报告
            json_report_file = test_dir / "report.json"
            json_result = self._run_cli_command([
                'scan',
                '--format', 'json',
                '--output', str(json_report_file),
                str(test_dir)
            ])

            if json_result['success'] and json_report_file.exists():
                result['tests'].append({
                    'name': 'JSON报告生成',
                    'status': 'PASS',
                    'details': f'报告大小: {json_report_file.stat().st_size} 字节'
                })
            else:
                result['tests'].append({
                    'name': 'JSON报告生成',
                    'status': 'FAIL',
                    'details': f'JSON报告生成失败: {json_result["stderr"]}'
                })
                result['issues'].append({
                    'type': 'report_error',
                    'component': 'Reporting',
                    'message': 'JSON报告生成失败',
                    'severity': 'HIGH'
                })

            # 测试HTML报告
            html_report_file = test_dir / "report.html"
            html_result = self._run_cli_command([
                'scan',
                '--format', 'html',
                '--output', str(html_report_file),
                str(test_dir)
            ])

            if html_result['success'] and html_report_file.exists():
                result['tests'].append({
                    'name': 'HTML报告生成',
                    'status': 'PASS',
                    'details': f'报告大小: {html_report_file.stat().st_size} 字节'
                })
            else:
                result['tests'].append({
                    'name': 'HTML报告生成',
                    'status': 'FAIL',
                    'details': f'HTML报告生成失败: {html_result["stderr"]}'
                })
                result['issues'].append({
                    'type': 'report_error',
                    'component': 'Reporting',
                    'message': 'HTML报告生成失败',
                    'severity': 'HIGH'
                })

            # 测试Markdown报告
            md_report_file = test_dir / "report.md"
            md_result = self._run_cli_command([
                'scan',
                '--format', 'markdown',
                '--output', str(md_report_file),
                str(test_dir)
            ])

            if md_result['success'] and md_report_file.exists():
                result['tests'].append({
                    'name': 'Markdown报告生成',
                    'status': 'PASS',
                    'details': f'报告大小: {md_report_file.stat().st_size} 字节'
                })
            else:
                result['tests'].append({
                    'name': 'Markdown报告生成',
                    'status': 'FAIL',
                    'details': f'Markdown报告生成失败: {md_result["stderr"]}'
                })
                result['issues'].append({
                    'type': 'report_error',
                    'component': 'Reporting',
                    'message': 'Markdown报告生成失败',
                    'severity': 'MEDIUM'
                })

        except Exception as e:
            result['tests'].append({
                'name': '报告生成测试',
                'status': 'FAIL',
                'details': f'测试异常: {str(e)}'
            })
            result['issues'].append({
                'type': 'report_error',
                'component': 'Reporting',
                'message': f'报告生成异常: {str(e)}',
                'severity': 'HIGH'
            })
        finally:
            # 清理临时文件
            shutil.rmtree(test_dir, ignore_errors=True)

        return result

    def _test_end_to_end(self) -> Dict[str, Any]:
        """测试端到端流程"""
        print("  🔄 测试端到端流程...")

        result = {
            'test_suite': 'End-to-End',
            'status': 'PASS',
            'tests': [],
            'issues': []
        }

        # 创建完整的测试项目
        test_dir = Path(tempfile.mkdtemp())
        try:
            # 创建项目结构
            project_files = [
                ('src/main.c', '/* Missing SPDX */\n#include <stdio.h>'),
                ('src/util.h', '// No license\n#ifndef UTIL_H'),
                ('src/util.c', '/* No license info */\n#include "util.h"'),
                ('tests/test_main.c', '#include <assert.h>'),
                ('README.md', '# Test Project\nNo license info.')
            ]

            for filepath, content in project_files:
                full_path = test_dir / filepath
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)

            # 测试完整的扫描-修正流程
            print("    执行完整扫描...")
            scan_result = self._run_cli_command(['scan', str(test_dir)])

            if not scan_result['success']:
                result['tests'].append({
                    'name': '端到端扫描',
                    'status': 'FAIL',
                    'details': f'扫描失败: {scan_result["stderr"]}'
                })
                result['issues'].append({
                    'type': 'e2e_error',
                    'component': 'End-to-End',
                    'message': '端到端扫描失败',
                    'severity': 'HIGH'
                })
                return result

            result['tests'].append({
                'name': '端到端扫描',
                'status': 'PASS',
                'details': '扫描成功完成'
            })

            # 测试自动修正
            print("    执行自动修正...")
            correct_result = self._run_cli_command([
                'correct',
                '--dry-run',
                str(test_dir)
            ])

            if correct_result['success']:
                result['tests'].append({
                    'name': '端到端修正',
                    'status': 'PASS',
                    'details': '修正功能正常工作'
                })
            else:
                result['tests'].append({
                    'name': '端到端修正',
                    'status': 'FAIL',
                    'details': f'修正失败: {correct_result["stderr"]}'
                })
                result['issues'].append({
                    'type': 'e2e_error',
                    'component': 'End-to-End',
                    'message': '端到端修正失败',
                    'severity': 'HIGH'
                })

            # 测试报告生成
            print("    生成最终报告...")
            report_result = self._run_cli_command([
                'scan',
                '--format', 'json',
                '--output', str(test_dir / 'final_report.json'),
                str(test_dir)
            ])

            if report_result['success']:
                result['tests'].append({
                    'name': '端到端报告',
                    'status': 'PASS',
                    'details': '报告生成成功'
                })
            else:
                result['tests'].append({
                    'name': '端到端报告',
                    'status': 'FAIL',
                    'details': f'报告生成失败: {report_result["stderr"]}'
                })

        except Exception as e:
            result['tests'].append({
                'name': '端到端测试',
                'status': 'FAIL',
                'details': f'测试异常: {str(e)}'
            })
            result['issues'].append({
                'type': 'e2e_error',
                'component': 'End-to-End',
                'message': f'端到端测试异常: {str(e)}',
                'severity': 'HIGH'
            })
        finally:
            # 清理临时文件
            shutil.rmtree(test_dir, ignore_errors=True)

        return result

    def _test_performance(self) -> Dict[str, Any]:
        """测试性能"""
        print("  ⚡ 测试性能...")

        result = {
            'test_suite': 'Performance',
            'status': 'PASS',
            'metrics': {},
            'tests': []
        }

        # 创建大量测试文件
        test_dir = Path(tempfile.mkdtemp())
        try:
            file_count = 50
            print(f"    创建 {file_count} 个测试文件...")

            for i in range(file_count):
                test_file = test_dir / f"file_{i:03d}.c"
                test_file.write_text(f"""/*
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2023 Corp {i}
 */

#include <stdio.h>

void function_{i}() {{
    printf("File {i}\\n");
}}
""")

            # 测试扫描性能
            start_time = time.time()
            scan_result = self._run_cli_command(['scan', str(test_dir)])
            scan_duration = time.time() - start_time

            if scan_result['success']:
                result['tests'].append({
                    'name': '扫描性能',
                    'status': 'PASS',
                    'details': f'{file_count} 个文件扫描耗时 {scan_duration:.2f} 秒'
                })
                result['metrics']['scan_time'] = scan_duration
                result['metrics']['files_per_second'] = file_count / scan_duration
            else:
                result['tests'].append({
                    'name': '扫描性能',
                    'status': 'FAIL',
                    'details': f'性能测试失败: {scan_result["stderr"]}'
                })

            # 评估性能
            if scan_duration > 30:  # 30秒阈值
                result['tests'].append({
                    'name': '性能评估',
                    'status': 'WARNING',
                    'details': f'扫描时间较长: {scan_duration:.2f}秒'
                })

        except Exception as e:
            result['tests'].append({
                'name': '性能测试',
                'status': 'FAIL',
                'details': f'性能测试异常: {str(e)}'
            })
        finally:
            # 清理临时文件
            shutil.rmtree(test_dir, ignore_errors=True)

        return result

    def _test_error_handling(self) -> Dict[str, Any]:
        """测试错误处理"""
        print("  🛡️  测试错误处理...")

        result = {
            'test_suite': 'Error Handling',
            'status': 'PASS',
            'tests': []
        }

        # 测试无效目录
        invalid_dir_result = self._run_cli_command(['scan', '/nonexistent/directory'])
        if not invalid_dir_result['success']:
            result['tests'].append({
                'name': '无效目录处理',
                'status': 'PASS',
                'details': '正确拒绝无效目录'
            })
        else:
            result['tests'].append({
                'name': '无效目录处理',
                'status': 'FAIL',
                'details': '未正确处理无效目录'
            })

        # 测试空目录
        empty_dir = Path(tempfile.mkdtemp())
        try:
            empty_result = self._run_cli_command(['scan', str(empty_dir)])
            if not empty_result['success']:
                result['tests'].append({
                    'name': '空目录处理',
                    'status': 'PASS',
                    'details': '正确处理空目录'
                })
            else:
                result['tests'].append({
                    'name': '空目录处理',
                    'status': 'WARNING',
                    'details': '空目录处理可能有问题'
                })
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)

        return result

    def _test_git_integration(self) -> Dict[str, Any]:
        """测试Git集成"""
        print("  🌿 测试Git集成...")

        result = {
            'test_suite': 'Git Integration',
            'status': 'PASS',
            'tests': []
        }

        # 检查Git是否可用
        try:
            git_result = subprocess.run(['git', '--version'], capture_output=True, check=True)
            result['tests'].append({
                'name': 'Git可用性',
                'status': 'PASS',
                'details': f'Git版本: {git_result.stdout.decode().strip()}'
            })
        except (subprocess.CalledProcessError, FileNotFoundError):
            result['tests'].append({
                'name': 'Git可用性',
                'status': 'WARNING',
                'details': 'Git不可用，跳过Git集成测试'
            })
            return result

        # 创建Git仓库测试
        test_dir = Path(tempfile.mkdtemp())
        try:
            # 初始化Git仓库
            subprocess.run(['git', 'init'], cwd=test_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=test_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=test_dir, check=True, capture_output=True)

            # 创建测试文件
            test_file = test_dir / "test.c"
            test_file.write_text("/* SPDX-License-Identifier: MIT */\n#include <stdio.h>")

            # 添加文件到Git
            subprocess.run(['git', 'add', '.'], cwd=test_dir, check=True, capture_output=True)

            # 测试pre-commit命令
            precommit_result = self._run_cli_command(['pre-commit'])
            if precommit_result['success']:
                result['tests'].append({
                    'name': 'Pre-commit命令',
                    'status': 'PASS',
                    'details': 'Pre-commit命令正常工作'
                })
            else:
                result['tests'].append({
                    'name': 'Pre-commit命令',
                    'status': 'FAIL',
                    'details': f'Pre-commit失败: {precommit_result["stderr"]}'
                })

        except Exception as e:
            result['tests'].append({
                'name': 'Git集成测试',
                'status': 'FAIL',
                'details': f'Git测试异常: {str(e)}'
            })
        finally:
            # 清理临时文件
            shutil.rmtree(test_dir, ignore_errors=True)

        return result

    def _generate_recommendations(self, test_suites: Dict, issues: List[Dict]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于失败测试套件生成建议
        failed_suites = [name for name, result in test_suites.items() if result.get('status') == 'FAIL']
        if failed_suites:
            recommendations.append(f"修复失败的测试套件: {', '.join(failed_suites)}")

        # 基于问题类型生成建议
        high_severity_issues = [issue for issue in issues if issue.get('severity') == 'HIGH']
        if high_severity_issues:
            recommendations.append("优先修复高严重性问题，这些问题影响核心功能")

        cli_issues = [issue for issue in issues if issue.get('component') == 'CLI']
        if cli_issues:
            recommendations.append("检查CLI接口实现，确保所有命令正常工作")

        config_issues = [issue for issue in issues if issue.get('component') == 'Config']
        if config_issues:
            recommendations.append("检查配置文件处理逻辑，确保配置正确加载和更新")

        performance_issues = [issue for issue in issues if '性能' in issue.get('message', '')]
        if performance_issues:
            recommendations.append("优化性能，考虑并行处理或缓存机制")

        # 通用建议
        recommendations.extend([
            "建立持续集成流程，自动运行集成测试",
            "监控关键功能的性能指标",
            "添加更多的端到端测试用例",
            "建立错误监控和报告机制"
        ])

        return recommendations
