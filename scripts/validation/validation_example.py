#!/usr/bin/env python3
"""
SPDX验证器实际使用示例

演示如何使用SPDX验证器来检查项目中的代码文件。
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 使用之前简化的验证器代码
from simple_validation_test import SPDXValidator, SPDXInfo, ValidationSeverity, ValidationError, ValidationResult

def scan_python_files_for_spdx(directory: str):
    """扫描Python文件中的SPDX声明"""
    print(f"🔍 扫描目录: {directory}")

    validator = SPDXValidator()
    results = []

    # 获取所有Python文件
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过常见的无需扫描的目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules']]

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"📄 找到 {len(python_files)} 个Python文件")

    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 检查文件中是否包含SPDX相关信息
            spdx_info = extract_spdx_info(content)
            if spdx_info.license_identifier or spdx_info.copyright_text:
                result = validator.validate(spdx_info)
                results.append({
                    'file': file_path,
                    'spdx_info': spdx_info,
                    'validation_result': result
                })

        except Exception as e:
            print(f"⚠️  处理文件 {file_path} 时出错: {e}")

    return results

def extract_spdx_info(content: str) -> SPDXInfo:
    """从文件内容中提取SPDX信息"""
    spdx_info = SPDXInfo()

    lines = content.split('\n')

    for line in lines[:50]:  # 只检查前50行（通常SPDX声明在文件头部）
        line = line.strip()

        # 检查SPDX许可证标识符
        if line.startswith('SPDX-License-Identifier:'):
            spdx_info.license_identifier = line.split(':', 1)[1].strip()

        # 检查版权信息
        elif line.startswith('Copyright (c)') or line.startswith('Copyright ©'):
            spdx_info.copyright_text = line

        # 检查其他可能的版权格式
        elif line.startswith('©'):
            spdx_info.copyright_text = line

        # 检查SPDX版本
        elif line.startswith('SPDX-Version:'):
            spdx_info.spdx_version = line.split(':', 1)[1].strip()

    return spdx_info

def validate_specific_examples():
    """验证一些具体的例子"""
    print("\n📋 验证具体的SPDX声明示例")
    print("-" * 50)

    validator = SPDXValidator()

    # 测试用例
    examples = [
        {
            "name": "标准MIT许可证声明",
            "content": '''"""
Example module for testing SPDX validation.
SPDX-License-Identifier: MIT
Copyright (c) 2023 Example Corp

This module provides example functionality.
"""
'''
        },
        {
            "name": "Apache-2.0许可证声明",
            "content": '''/*
 * Copyright 2023 Example Corp
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0
 */
'''
        },
        {
            "name": "GPL-3.0许可证声明",
            "content": '''# SPDX-License-Identifier: GPL-3.0
# Copyright (C) 2023 Example Corp
#
# This program is free software: you can redistribute it under the terms of
# the GNU General Public License as published by the Free Software Foundation
'''
        },
        {
            "name": "不完整的声明（只有版权）",
            "content": '''/*
 * Copyright (c) 2023 Example Corp
 *
 * Missing license identifier
 */
'''
        },
        {
            "name": "无效的许可证标识符",
            "content": '''/*
 * SPDX-License-Identifier: FAKE-LICENSE
 * Copyright (c) 2023 Example Corp
 */
'''
        },
        {
            "name": "复杂许可证表达式",
            "content": '''/*
 * SPDX-License-Identifier: MIT OR Apache-2.0
 * Copyright (c) 2023 Example Corp
 */
'''
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n🔍 示例 {i}: {example['name']}")
        spdx_info = extract_spdx_info(example['content'])
        result = validator.validate(spdx_info)

        # 显示提取的信息
        print(f"  📝 提取的信息:")
        print(f"    许可证标识符: {spdx_info.license_identifier or '无'}")
        print(f"    版权信息: {spdx_info.copyright_text or '无'}")
        print(f"    SPDX版本: {spdx_info.spdx_version or '无'}")

        # 显示验证结果
        print(f"  ✅ 验证结果:")
        print(f"    状态: {'有效' if result.is_valid else '无效'}")
        print(f"    错误: {len(result.errors)}")
        print(f"    警告: {len(result.warnings)}")
        print(f"    建议: {len(result.suggestions)}")

        if result.errors:
            print("    错误详情:")
            for error in result.errors:
                print(f"      ❌ {error.message}")
                if error.suggestion:
                    print(f"         建议: {error.suggestion}")

        if result.warnings:
            print("    警告详情:")
            for warning in result.warnings:
                print(f"      ⚠️  {warning.message}")

        if result.suggestions:
            print("    建议:")
            for suggestion in result.suggestions:
                print(f"      💡 {suggestion}")

def generate_validation_report(results):
    """生成验证报告"""
    print("\n📊 项目SPDX验证报告")
    print("=" * 60)

    if not results:
        print("未发现任何包含SPDX声明的文件")
        return

    valid_count = sum(1 for r in results if r['validation_result'].is_valid)
    invalid_count = len(results) - valid_count

    print(f"📄 总文件数: {len(results)}")
    print(f"✅ 有效文件: {valid_count}")
    print(f"❌ 无效文件: {invalid_count}")
    print(f"📈 合格率: {valid_count/len(results)*100:.1f}%")

    if invalid_count > 0:
        print(f"\n🔧 需要修复的文件:")
        for result in results:
            if not result['validation_result'].is_valid:
                print(f"\n📁 {result['file']}")
                spdx_info = result['spdx_info']
                validation_result = result['validation_result']

                print(f"   当前许可证: {spdx_info.license_identifier or '无'}")
                print(f"   当前版权: {spdx_info.copyright_text or '无'}")
                print(f"   错误数量: {len(validation_result.errors)}")

                for error in validation_result.errors:
                    print(f"     ❌ {error.message}")
                    if error.suggestion:
                        print(f"        💡 {error.suggestion}")

def main():
    """主函数"""
    print("🚀 SPDX验证器实际使用示例")
    print("=" * 60)

    # 验证具体示例
    validate_specific_examples()

    # 扫描当前项目
    print(f"\n" + "="*60)
    print("🔍 扫描当前项目...")
    results = scan_python_files_for_spdx('.')

    # 生成报告
    generate_validation_report(results)

    print(f"\n" + "="*60)
    print("✅ 验证完成！")
    print("\n💡 使用建议:")
    print("1. 确保所有源文件都包含正确的SPDX许可证标识符")
    print("2. 使用标准的版权格式")
    print("3. 考虑添加SPDX版本信息")
    print("4. 对于复杂的许可证组合，使用括号明确分组")
    print("5. 定期运行验证程序确保合规性")

if __name__ == "__main__":
    main()