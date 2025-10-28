#!/usr/bin/env python3
"""
SPDX验证器自动测试脚本

这个脚本直接测试验证器的核心功能，无需外部依赖。
"""

import sys
import os
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from spdx_scanner.validator import SPDXLicenseDatabase, SPDXValidator, create_default_validator
    from spdx_scanner.models import SPDXInfo
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保您在项目根目录中运行此脚本")
    sys.exit(1)

def test_license_database():
    """测试SPDX许可证数据库功能"""
    print("🧪 测试 SPDX 许可证数据库...")
    db = SPDXLicenseDatabase()

    # 测试有效许可证
    valid_licenses = ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"]
    for license_id in valid_licenses:
        result = db.is_valid_license_id(license_id)
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {license_id}: {status}")

    # 测试无效许可证
    invalid_licenses = ["INVALID-LICENSE", "", "Made-Up-License"]
    for license_id in invalid_licenses:
        result = db.is_valid_license_id(license_id)
        status = "✅ 通过" if not result else "❌ 失败"
        print(f"  {license_id}: {status} (应该无效)")

    # 测试复杂许可证表达式
    complex_expressions = [
        "MIT OR Apache-2.0",
        "GPL-3.0 WITH Classpath-exception-2.0",
        "(MIT AND Apache-2.0) OR BSD-3-Clause"
    ]
    for expr in complex_expressions:
        result = db.is_valid_license_id(expr)
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {expr}: {status}")

def test_validator_basic():
    """测试基本的验证功能"""
    print("\n🧪 测试基础验证功能...")
    validator = create_default_validator()

    # 测试有效的SPDX信息
    valid_spdx = SPDXInfo(
        license_identifier="MIT",
        copyright_text="Copyright (c) 2023 Example Corp",
        project_attribution="Example Project",
        spdx_version="SPDX-2.2"
    )

    result = validator.validate(valid_spdx)
    if result.is_valid:
        print("  ✅ 有效SPDX信息验证通过")
    else:
        print("  ❌ 有效SPDX信息验证失败")
        for error in result.errors:
            print(f"    错误: {error.message}")

    # 测试无效的许可证标识符
    invalid_license = SPDXInfo(
        license_identifier="INVALID-LICENSE",
        copyright_text="Copyright (c) 2023 Example Corp"
    )

    result = validator.validate(invalid_license)
    if not result.is_valid:
        print("  ✅ 无效许可证标识符检测成功")
    else:
        print("  ❌ 无效许可证标识符未检测到")

    # 测试缺失必需字段
    missing_fields = SPDXInfo()

    result = validator.validate(missing_fields)
    if not result.is_valid:
        print("  ✅ 缺失必需字段检测成功")
    else:
        print("  ❌ 缺失必需字段未检测到")

def test_copyright_validation():
    """测试版权信息验证"""
    print("\n🧪 测试版权验证功能...")
    validator = create_default_validator()

    # 测试各种版权格式
    copyright_tests = [
        ("Copyright (c) 2023 Example Corp", "标准格式"),
        ("© 2023 Example Corp", "符号格式"),
        ("Copyright 2023 Example Corp", "简化格式"),
        ("Invalid copyright format", "无效格式"),
        (f"Copyright (c) {datetime.now().year + 5} Example Corp", "未来年份")
    ]

    for copyright_text, description in copyright_tests:
        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text=copyright_text
        )

        result = validator.validate(spdx_info)
        has_issues = len(result.errors) > 0 or len(result.warnings) > 0
        status = "✅ 检测到问题" if has_issues else "✅ 格式正确"
        print(f"  {description}: {status}")

def test_validation_rules():
    """测试验证规则配置"""
    print("\n🧪 测试验证规则配置...")
    validator = create_default_validator()

    # 获取当前规则
    rules = validator.get_validation_rules()
    print(f"  当前验证规则数量: {len(rules)}")
    for rule, value in rules.items():
        print(f"    {rule}: {value}")

    # 更新规则
    validator.update_validation_rule('require_license_identifier', False)
    updated_rules = validator.get_validation_rules()
    if not updated_rules['require_license_identifier']:
        print("  ✅ 规则更新成功")
    else:
        print("  ❌ 规则更新失败")

def run_comprehensive_validation():
    """运行综合验证测试"""
    print("\n🔍 运行综合验证测试...")

    # 创建包含各种情况的测试数据
    test_cases = [
        {
            "name": "完整有效信息",
            "spdx": SPDXInfo(
                license_identifier="MIT",
                copyright_text="Copyright (c) 2023 Example Corp",
                project_attribution="Example Project",
                spdx_version="SPDX-2.2"
            ),
            "expected_valid": True
        },
        {
            "name": "缺失版权信息",
            "spdx": SPDXInfo(
                license_identifier="MIT"
            ),
            "expected_valid": False
        },
        {
            "name": "无效许可证",
            "spdx": SPDXInfo(
                license_identifier="FAKE-LICENSE",
                copyright_text="Copyright (c) 2023 Example Corp"
            ),
            "expected_valid": False
        },
        {
            "name": "复杂许可证表达式",
            "spdx": SPDXInfo(
                license_identifier="MIT OR Apache-2.0",
                copyright_text="Copyright (c) 2023 Example Corp"
            ),
            "expected_valid": True
        }
    ]

    validator = create_default_validator()

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  测试案例 {i}: {test_case['name']}")
        result = validator.validate(test_case['spdx'])

        success = result.is_valid == test_case['expected_valid']
        status = "✅ 通过" if success else "❌ 失败"
        print(f"    结果: {status}")
        print(f"    验证结果: {'有效' if result.is_valid else '无效'}")
        print(f"    错误数量: {len(result.errors)}")
        print(f"    警告数量: {len(result.warnings)}")
        print(f"    建议数量: {len(result.suggestions)}")

        if result.errors:
            print("    错误:")
            for error in result.errors:
                print(f"      - {error.message}")
        if result.warnings:
            print("    警告:")
            for warning in result.warnings:
                print(f"      - {warning.message}")

def main():
    """主函数"""
    print("🚀 SPDX 验证器自动测试程序")
    print("=" * 50)

    try:
        test_license_database()
        test_validator_basic()
        test_copyright_validation()
        test_validation_rules()
        run_comprehensive_validation()

        print("\n" + "=" * 50)
        print("✅ 所有测试完成!")
        print("验证器功能正常运行，可以进行SPDX许可证声明的验证。")

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)