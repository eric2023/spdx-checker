#!/usr/bin/env python3
"""
完整的集成测试脚本
测试 SPDX Scanner 工具链的完整工作流程
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_end_to_end_workflow():
    """端到端工作流测试"""
    print("=" * 60)
    print("端到端工作流测试")
    print("=" * 60)

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # 创建测试文件
        test_files = {
            'python_file.py': '''#!/usr/bin/env python3
"""Python test file"""

def hello():
    print("Hello, World!")
''',
            'javascript_file.js': '''// JavaScript test file
function hello() {
    console.log("Hello, World!");
}
''',
            'java_file.java': '''// Java test file
public class Test {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
''',
            'c_file.c': '''// C test file
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
''',
        }

        # 写入测试文件
        for filename, content in test_files.items():
            filepath = tmppath / filename
            filepath.write_text(content)
            print(f"✓ 创建测试文件: {filename}")

        print(f"\n临时目录: {tmppath}")
        print(f"创建文件数: {len(test_files)}\n")

        # 测试1: 扫描文件
        print("测试1: 文件扫描")
        print("-" * 60)
        try:
            from spdx_scanner.scanner import FileScanner

            scanner = FileScanner()
            file_count = 0
            for file_info in scanner.scan_directory(tmppath):
                file_count += 1
                print(f"  - 扫描: {file_info.filepath.name}")
                print(f"    语言: {file_info.language}")
                print(f"    编码: {file_info.encoding}")
                print(f"    大小: {file_info.size} bytes")

            print(f"✓ 扫描完成，共 {file_count} 个文件\n")
            assert file_count == 4, f"期望扫描4个文件，实际扫描 {file_count} 个"
        except Exception as e:
            print(f"❌ 扫描失败: {e}\n")
            return False

        # 测试2: 解析SPDX信息
        print("测试2: SPDX信息解析")
        print("-" * 60)
        try:
            from spdx_scanner.parser import SPDXParser
            from spdx_scanner.scanner import FileScanner

            parser = SPDXParser()
            scanner = FileScanner()

            valid_files = 0
            for file_info in scanner.scan_directory(tmppath):
                spdx_info = parser.parse_file(file_info)
                file_info.spdx_info = spdx_info

                if spdx_info.has_minimal_info():
                    valid_files += 1
                    print(f"  - {file_info.filepath.name}: 已有SPDX声明")
                else:
                    print(f"  - {file_info.filepath.name}: 缺失SPDX声明")

            print(f"✓ 解析完成，{valid_files}/{file_count} 文件已有SPDX声明\n")
        except Exception as e:
            print(f"❌ 解析失败: {e}\n")
            import traceback
            traceback.print_exc()
            return False

        # 测试3: 验证SPDX信息
        print("测试3: SPDX信息验证")
        print("-" * 60)
        try:
            from spdx_scanner.validator import SPDXValidator

            validator = SPDXValidator()
            scanner = FileScanner()

            valid_count = 0
            invalid_count = 0
            for file_info in scanner.scan_directory(tmppath):
                spdx_info = parser.parse_file(file_info)
                result = validator.validate(spdx_info)

                if result.is_valid:
                    valid_count += 1
                    print(f"  - {file_info.filepath.name}: 验证通过")
                else:
                    invalid_count += 1
                    print(f"  - {file_info.filepath.name}: 验证失败 ({len(result.errors)} 错误)")

            print(f"✓ 验证完成，通过: {valid_count}, 失败: {invalid_count}\n")
        except Exception as e:
            print(f"❌ 验证失败: {e}\n")
            import traceback
            traceback.print_exc()
            return False

        # 测试4: 自动修正
        print("测试4: 自动修正SPDX声明")
        print("-" * 60)
        try:
            from spdx_scanner.corrector import SPDXCorrector
            from spdx_scanner.scanner import FileScanner

            corrector = SPDXCorrector({
                'default_license': 'MIT',
                'default_copyright_holder': 'Test Company',
                'default_project_name': 'Test Project',
                'dry_run': True  # 使用干运行模式
            })
            scanner = FileScanner()

            corrected_count = 0
            for file_info in scanner.scan_directory(tmppath):
                result = corrector.correct_file(file_info, dry_run=True)

                if result.success:
                    corrected_count += 1
                    print(f"  - {file_info.filepath.name}: 修正成功")
                    if result.changes_made:
                        print(f"    修改: {result.changes_made[0]}")
                else:
                    print(f"  - {file_info.filepath.name}: 修正失败")

            print(f"✓ 修正测试完成，{corrected_count}/{file_count} 文件可修正\n")
        except Exception as e:
            print(f"❌ 修正失败: {e}\n")
            import traceback
            traceback.print_exc()
            return False

        # 测试5: 生成报告
        print("测试5: 生成扫描报告")
        print("-" * 60)
        try:
            from spdx_scanner.reporter import TextReportGenerator, JSONReportGenerator
            from spdx_scanner.models import ScanResult, ScanSummary
            from spdx_scanner.parser import SPDXParser
            from spdx_scanner.validator import SPDXValidator
            from spdx_scanner.scanner import FileScanner

            scanner = FileScanner()
            parser = SPDXParser()
            validator = SPDXValidator()

            results = []
            for file_info in scanner.scan_directory(tmppath):
                spdx_info = parser.parse_file(file_info)
                validation_result = validator.validate(spdx_info)

                scan_result = ScanResult(
                    file_info=file_info,
                    validation_result=validation_result
                )
                results.append(scan_result)

            summary = ScanSummary()
            for result in results:
                summary.add_result(result)

            # 测试文本报告
            text_gen = TextReportGenerator()
            import io
            text_output = io.StringIO()
            text_gen.generate(results, summary, text_output)
            text_content = text_output.getvalue()
            print(f"  - 文本报告生成成功 ({len(text_content)} 字符)")

            # 测试JSON报告
            json_gen = JSONReportGenerator()
            json_output = io.StringIO()
            json_gen.generate(results, summary, json_output)
            print(f"  - JSON报告生成成功")

            print(f"✓ 报告生成完成")
            print(f"  - 总文件: {summary.total_files}")
            print(f"  - 有效文件: {summary.valid_files}")
            print(f"  - 无效文件: {summary.invalid_files}")
            print(f"  - 成功率: {summary.get_success_rate():.1f}%\n")
        except Exception as e:
            print(f"❌ 报告生成失败: {e}\n")
            import traceback
            traceback.print_exc()
            return False

        # 测试6: 实际修正文件
        print("测试6: 实际修正文件（创建备份）")
        print("-" * 60)
        try:
            from spdx_scanner.corrector import SPDXCorrector
            from spdx_scanner.scanner import FileScanner

            corrector = SPDXCorrector({
                'default_license': 'MIT',
                'default_copyright_holder': 'Test Company',
                'default_project_name': 'Test Project',
                'create_backups': True,
                'dry_run': False  # 实际修改
            })
            scanner = FileScanner()

            corrected_count = 0
            for file_info in scanner.scan_directory(tmppath):
                result = corrector.correct_file(file_info, dry_run=False)

                if result.success:
                    corrected_count += 1
                    print(f"  - {file_info.filepath.name}: 修正成功")

                    # 检查备份文件
                    if result.backup_created and result.backup_path:
                        backup_exists = result.backup_path.exists()
                        print(f"    备份文件: {result.backup_path.name} ({'存在' if backup_exists else '不存在'})")

                    # 检查文件内容
                    updated_content = file_info.filepath.read_text()
                    has_spdx = 'SPDX-License-Identifier' in updated_content
                    print(f"    包含SPDX声明: {'是' if has_spdx else '否'}")
                else:
                    print(f"  - {file_info.filepath.name}: 修正失败")

            print(f"✓ 实际修正完成，{corrected_count}/{file_count} 文件已修正\n")
        except Exception as e:
            print(f"❌ 实际修正失败: {e}\n")
            import traceback
            traceback.print_exc()
            return False

        # 测试7: 配置管理
        print("测试7: 配置管理")
        print("-" * 60)
        try:
            from spdx_scanner.config import ConfigManager, Configuration

            config_manager = ConfigManager()
            config = Configuration(
                project_name='Integration Test',
                default_license='Apache-2.0',
                copyright_holder='Integration Test Company'
            )

            # 保存配置
            config_path = tmppath / 'test_config.json'
            config_manager.config = config
            config_manager.save_config(config_path)

            print(f"  - 配置已保存到: {config_path.name}")

            # 加载配置
            loaded_config = config_manager.load_config(config_path)
            print(f"  - 配置已加载")
            print(f"    项目名称: {loaded_config.project_name}")
            print(f"    默认许可证: {loaded_config.default_license}")
            print(f"    版权持有者: {loaded_config.copyright_holder}")

            print(f"✓ 配置管理测试通过\n")
        except Exception as e:
            print(f"❌ 配置管理失败: {e}\n")
            import traceback
            traceback.print_exc()
            return False

    print("=" * 60)
    print("✅ 端到端工作流测试全部通过！")
    print("=" * 60)
    return True


def test_multilang_spdx_parsing():
    """多语言SPDX解析测试"""
    print("\n" + "=" * 60)
    print("多语言SPDX解析测试")
    print("=" * 60)

    test_cases = {
        'Python': {
            'content': '''#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Python Project
# Python Test Module
''',
            'language': 'python',
            'expected_license': 'MIT',
            'expected_copyright': 'Copyright (c) 2025 Python Project'
        },
        'JavaScript': {
            'content': '''// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2025 JavaScript Project
// JavaScript Test File
''',
            'language': 'javascript',
            'expected_license': 'Apache-2.0',
            'expected_copyright': 'Copyright (c) 2025 JavaScript Project'
        },
        'Java': {
            'content': '''/* SPDX-License-Identifier: GPL-3.0
 * Copyright (c) 2025 Java Project
 * Java Test Class
 */
''',
            'language': 'java',
            'expected_license': 'GPL-3.0',
            'expected_copyright': 'Copyright (c) 2025 Java Project'
        },
        'C': {
            'content': '''/* SPDX-License-Identifier: BSD-3-Clause
 * Copyright (c) 2025 C Project
 * C Test Header
 */
''',
            'language': 'c',
            'expected_license': 'BSD-3-Clause',
            'expected_copyright': 'Copyright (c) 2025 C Project'
        },
        'Shell': {
            'content': '''#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Shell Project
# Shell Test Script
''',
            'language': 'shell',
            'expected_license': 'MIT',
            'expected_copyright': 'Copyright (c) 2025 Shell Project'
        },
    }

    try:
        from spdx_scanner.parser import SPDXParser
        from spdx_scanner.models import FileInfo
        from pathlib import Path

        parser = SPDXParser()
        passed = 0
        failed = 0

        for lang_name, test_case in test_cases.items():
            file_info = FileInfo(
                filepath=Path(f'test.{lang_name.lower()}'),
                language=test_case['language'],
                content=test_case['content']
            )

            spdx_info = parser.parse_file(file_info)

            license_match = spdx_info.license_identifier == test_case['expected_license']
            copyright_match = spdx_info.copyright_text == test_case['expected_copyright']

            if license_match and copyright_match:
                print(f"✓ {lang_name}: 解析正确")
                passed += 1
            else:
                print(f"❌ {lang_name}: 解析错误")
                if not license_match:
                    print(f"  期望许可证: {test_case['expected_license']}")
                    print(f"  实际许可证: {spdx_info.license_identifier}")
                if not copyright_match:
                    print(f"  期望版权: {test_case['expected_copyright']}")
                    print(f"  实际版权: {spdx_info.copyright_text}")
                failed += 1

        print(f"\n多语言解析测试完成: {passed} 通过, {failed} 失败")
        return failed == 0

    except Exception as e:
        print(f"❌ 多语言解析测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_validation_rules():
    """验证规则测试"""
    print("\n" + "=" * 60)
    print("验证规则测试")
    print("=" * 60)

    try:
        from spdx_scanner.validator import SPDXValidator
        from spdx_scanner.models import SPDXInfo

        validator = SPDXValidator()

        # 测试用例
        test_cases = [
            {
                'name': '有效许可证 (MIT)',
                'spdx': SPDXInfo(
                    license_identifier='MIT',
                    copyright_text='Copyright (c) 2025 Test'
                ),
                'should_be_valid': True
            },
            {
                'name': '有效许可证 (Apache-2.0)',
                'spdx': SPDXInfo(
                    license_identifier='Apache-2.0',
                    copyright_text='Copyright (c) 2025 Test'
                ),
                'should_be_valid': True
            },
            {
                'name': '无效许可证',
                'spdx': SPDXInfo(
                    license_identifier='Invalid-License-XYZ',
                    copyright_text='Copyright (c) 2025 Test'
                ),
                'should_be_valid': False
            },
            {
                'name': '缺失许可证',
                'spdx': SPDXInfo(
                    copyright_text='Copyright (c) 2025 Test'
                ),
                'should_be_valid': False
            },
            {
                'name': '缺失版权',
                'spdx': SPDXInfo(
                    license_identifier='MIT'
                ),
                'should_be_valid': False
            },
        ]

        passed = 0
        failed = 0

        for test_case in test_cases:
            result = validator.validate(test_case['spdx'])
            is_valid = result.is_valid

            if is_valid == test_case['should_be_valid']:
                print(f"✓ {test_case['name']}: {'通过' if is_valid else '失败'} (期望: {'通过' if test_case['should_be_valid'] else '失败'})")
                passed += 1
            else:
                print(f"❌ {test_case['name']}: 实际结果与期望不符")
                print(f"  期望: {'通过' if test_case['should_be_valid'] else '失败'}")
                print(f"  实际: {'通过' if is_valid else '失败'}")
                if result.errors:
                    print(f"  错误数: {len(result.errors)}")
                failed += 1

        print(f"\n验证规则测试完成: {passed} 通过, {failed} 失败")
        return failed == 0

    except Exception as e:
        print(f"❌ 验证规则测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("SPDX Scanner - 完整集成测试")
    print("=" * 80 + "\n")

    tests = [
        ("端到端工作流测试", test_end_to_end_workflow),
        ("多语言SPDX解析测试", test_multilang_spdx_parsing),
        ("验证规则测试", test_validation_rules),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}测试出现异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 汇总结果
    print("\n" + "=" * 80)
    print("集成测试结果汇总")
    print("=" * 80)

    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"成功率: {(passed / len(results) * 100):.1f}%")

    if passed == len(results):
        print("\n🎉 所有集成测试通过！")
        print("\n" + "=" * 80)
        print("功能完备性验证完成")
        print("✅ 所有核心功能模块工作正常")
        print("✅ 端到端工作流运行流畅")
        print("✅ 多语言支持完整")
        print("✅ 验证规则准确")
        print("=" * 80)
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个集成测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
