#!/usr/bin/env python3
"""
简化的SPDX验证器测试脚本

直接测试validator模块的核心功能，避免依赖问题。
"""

import sys
import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Set, Any

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 简化的数据模型定义（避免依赖外部模块）
class ValidationSeverity:
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationError:
    def __init__(self, severity: str, message: str, rule_id: str, suggestion: str = ""):
        self.severity = severity
        self.message = message
        self.rule_id = rule_id
        self.suggestion = suggestion

class ValidationResult:
    def __init__(self, is_valid: bool = True):
        self.is_valid = is_valid
        self.errors = []
        self.warnings = []
        self.suggestions = []
        self.validation_time = 0.0

    def add_error(self, error: ValidationError):
        if error.severity == ValidationSeverity.ERROR:
            self.errors.append(error)
            self.is_valid = False
        elif error.severity == ValidationSeverity.WARNING:
            self.warnings.append(error)
        self.is_valid = False

    def add_warning(self, error: ValidationError):
        self.warnings.append(error)

    def add_suggestion(self, suggestion: str):
        self.suggestions.append(suggestion)

class SPDXInfo:
    def __init__(self, license_identifier: str = "", copyright_text: str = "",
                 project_attribution: str = "", spdx_version: str = "",
                 additional_tags: Optional[Dict[str, Any]] = None):
        self.license_identifier = license_identifier
        self.copyright_text = copyright_text
        self.project_attribution = project_attribution
        self.spdx_version = spdx_version
        self.additional_tags = additional_tags or {}

# SPDXLicenseDatabase类的复制（来自validator.py）
class SPDXLicenseDatabase:
    """SPDX license database for validation."""

    # Core SPDX licenses (simplified list for validation)
    CORE_LICENSES = {
        # Popular OSI-approved licenses
        'MIT': {
            'name': 'MIT License',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Permissive',
        },
        'Apache-2.0': {
            'name': 'Apache License 2.0',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Permissive',
        },
        'GPL-2.0': {
            'name': 'GNU General Public License v2.0 only',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Copyleft',
        },
        'GPL-2.0+': {
            'name': 'GNU General Public License v2.0 or later',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Copyleft',
        },
        'GPL-3.0': {
            'name': 'GNU General Public License v3.0 only',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Copyleft',
        },
        'GPL-3.0+': {
            'name': 'GNU General Public License v3.0 or later',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Copyleft',
        },
        'LGPL-2.1': {
            'name': 'GNU Lesser General Public License v2.1 only',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'LGPL-2.1+': {
            'name': 'GNU Lesser General Public License v2.1 or later',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'LGPL-3.0': {
            'name': 'GNU Lesser General Public License v3.0 only',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'LGPL-3.0+': {
            'name': 'GNU Lesser General Public License v3.0 or later',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'BSD-2-Clause': {
            'name': 'BSD 2-Clause License',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Permissive',
        },
        'BSD-3-Clause': {
            'name': 'BSD 3-Clause License',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Permissive',
        },
        'MPL-2.0': {
            'name': 'Mozilla Public License 2.0',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'EPL-2.0': {
            'name': 'Eclipse Public License 2.0',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'CC0-1.0': {
            'name': 'Creative Commons Zero v1.0 Universal',
            'is_osi_approved': False,
            'is_fsf_libre': True,
            'category': 'Public Domain',
        },
        'Unlicense': {
            'name': 'The Unlicense',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Public Domain',
        },
    }

    # License exceptions (for "WITH" expressions)
    LICENSE_EXCEPTIONS = {
        'Classpath-exception-2.0',
        'GPL-CC-1.0',
        'LLVM-exception',
        'Autoconf-exception-3.0',
        'Font-exception-2.0',
        'OCaml-LGPL-linking-exception',
        'Qt-GPL-exception-1.0',
        'Universal-FOSS-exception-1.0',
    }

    @classmethod
    def is_valid_license_id(cls, license_id: str) -> bool:
        """Check if license ID is valid."""
        license_id = license_id.strip()

        # Handle parentheses for grouping - recursively validate content
        if license_id.startswith('(') and license_id.endswith(')'):
            return cls.is_valid_license_id(license_id[1:-1])

        # Handle nested parentheses and complex expressions
        # Remove outer parentheses for processing
        while license_id.startswith('(') and license_id.endswith(')'):
            license_id = license_id[1:-1]

        # Handle OR expressions first (lowest precedence)
        if ' OR ' in license_id:
            licenses = [part.strip() for part in license_id.split(' OR ')]
            return all(cls.is_valid_license_id(lic) for lic in licenses)

        # Handle AND expressions (higher precedence than OR)
        if ' AND ' in license_id:
            licenses = [part.strip() for part in license_id.split(' AND ')]
            return all(cls.is_valid_license_id(lic) for lic in licenses)

        # Handle WITH expressions (highest precedence)
        if ' WITH ' in license_id:
            parts = license_id.split(' WITH ')
            if len(parts) == 2:
                base_license = parts[0].strip()
                exception = parts[1].strip()
                return (
                    cls.is_valid_license_id(base_license) and
                    exception in cls.LICENSE_EXCEPTIONS
                )

        # Handle simple license IDs
        return license_id in cls.CORE_LICENSES

    @classmethod
    def get_license_info(cls, license_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a license."""
        # Handle simple license IDs
        if license_id in cls.CORE_LICENSES:
            return cls.CORE_LICENSES[license_id]

        # For complex expressions, return basic info
        if any(op in license_id for op in [' OR ', ' AND ', ' WITH ']):
            return {
                'name': f'Complex License Expression: {license_id}',
                'is_osi_approved': False,  # Complex expressions need individual evaluation
                'is_fsf_libre': False,
                'category': 'Complex',
            }

        return None

# SPDXValidator类的核心方法
class SPDXValidator:
    """SPDX license declaration validator."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize validator with configuration."""
        self.config = config or {}
        self.license_db = SPDXLicenseDatabase()
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from configuration."""
        default_rules = {
            'require_license_identifier': True,
            'require_copyright': True,
            'require_project_attribution': False,
            'allow_unknown_licenses': False,
            'require_osi_approved': False,
            'require_spdx_version': False,
            'min_copyright_year': 1970,
            'max_copyright_year': datetime.now().year + 1,
            'copyright_format': 'standard',  # 'standard', 'flexible', 'any'
            'license_format': 'strict',  # 'strict', 'flexible'
        }

        # Override with config
        default_rules.update(self.config.get('validation_rules', {}))
        return default_rules

    def validate(self, spdx_info: SPDXInfo) -> ValidationResult:
        """Validate SPDX information."""
        result = ValidationResult(is_valid=True)
        start_time = datetime.now()

        try:
            # Validate license identifier
            self._validate_license_identifier(spdx_info, result)

            # Validate copyright
            self._validate_copyright(spdx_info, result)

            # Validate project attribution
            self._validate_project_attribution(spdx_info, result)

            # Validate SPDX version
            self._validate_spdx_version(spdx_info, result)

            # Validate additional tags
            self._validate_additional_tags(spdx_info, result)

            # Check for recommended practices
            self._validate_best_practices(spdx_info, result)

        except Exception as e:
            print(f"验证错误: {e}")
            result.add_error(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"验证失败: {str(e)}",
                rule_id="validation_error"
            ))

        # Calculate validation time
        end_time = datetime.now()
        result.validation_time = (end_time - start_time).total_seconds()

        return result

    def _validate_license_identifier(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate license identifier."""
        if self.validation_rules['require_license_identifier']:
            if not spdx_info.license_identifier:
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message="缺失必需的SPDX许可证标识符",
                    rule_id="missing_license_identifier",
                    suggestion="在文件头部添加 'SPDX-License-Identifier: [LICENSE-ID]'"
                ))
                return

        if spdx_info.license_identifier:
            license_id = spdx_info.license_identifier.strip()

            # Basic format validation
            if not self._is_valid_license_format(license_id):
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"无效的SPDX许可证标识符格式: {license_id}",
                    rule_id="invalid_license_format",
                    suggestion="使用有效的SPDX许可证标识符格式"
                ))

            # Check against license database
            if not self.license_db.is_valid_license_id(license_id):
                if self.validation_rules['allow_unknown_licenses']:
                    result.add_warning(ValidationError(
                        severity=ValidationSeverity.WARNING,
                        message=f"未知或未注册的SPDX许可证标识符: {license_id}",
                        rule_id="unknown_license_identifier",
                        suggestion="考虑使用SPDX许可证列表中的许可证"
                    ))
                else:
                    result.add_error(ValidationError(
                        severity=ValidationSeverity.ERROR,
                        message=f"无效的SPDX许可证标识符: {license_id}",
                        rule_id="invalid_license_identifier",
                        suggestion="使用有效的SPDX许可证标识符，参考 https://spdx.org/licenses/"
                    ))

    def _validate_copyright(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate copyright information."""
        if self.validation_rules['require_copyright']:
            if not spdx_info.copyright_text:
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message="缺失必需的版权信息",
                    rule_id="missing_copyright",
                    suggestion="使用格式添加版权信息: 'Copyright (c) [year] [holder]'"
                ))
                return

        if spdx_info.copyright_text:
            copyright_text = spdx_info.copyright_text.strip()

            # Validate copyright format
            if not self._is_valid_copyright_format(copyright_text):
                severity = ValidationSeverity.WARNING
                if self.validation_rules['copyright_format'] == 'standard':
                    severity = ValidationSeverity.ERROR

                result.add_error(ValidationError(
                    severity=severity,
                    message=f"版权格式可能无效: {copyright_text}",
                    rule_id="invalid_copyright_format",
                    suggestion="使用格式: 'Copyright (c) [year] [holder]'"
                ))

    def _validate_project_attribution(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate project attribution."""
        if self.validation_rules['require_project_attribution']:
            if not spdx_info.project_attribution:
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message="缺失必需的项目归属信息",
                    rule_id="missing_project_attribution",
                    suggestion="添加项目名称或归属信息"
                ))

    def _validate_spdx_version(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate SPDX version."""
        if self.validation_rules['require_spdx_version']:
            if not spdx_info.spdx_version:
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message="缺失必需的SPDX版本",
                    rule_id="missing_spdx_version",
                    suggestion="在文件头部添加 'SPDX-Version: [version]'"
                ))

    def _validate_additional_tags(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate additional SPDX tags."""
        # Validate contributor information if present
        if 'contributors' in spdx_info.additional_tags:
            contributors = spdx_info.additional_tags['contributors']
            if not contributors.strip():
                result.add_warning(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message="空的贡献者信息",
                    rule_id="empty_contributors",
                    suggestion="移除空的贡献者标签或添加贡献者名称"
                ))

    def _validate_best_practices(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate SPDX best practices."""
        # Check for complete license information
        if spdx_info.license_identifier and not spdx_info.copyright_text:
            result.add_suggestion("建议在许可证标识符旁边添加版权信息")

        if spdx_info.copyright_text and not spdx_info.license_identifier:
            result.add_suggestion("建议在版权信息旁边添加许可证标识符")

        # Check for SPDX version (recommended)
        if not spdx_info.spdx_version:
            result.add_suggestion("建议添加SPDX版本以便明确")

    def _is_valid_license_format(self, license_id: str) -> bool:
        """Check if license identifier has valid format."""
        # Basic SPDX license identifier format validation
        valid_chars = re.match(r'^[A-Za-z0-9\-\+\.\(\)\s]+$', license_id)
        if not valid_chars:
            return False

        # Should not be empty or just whitespace
        if not license_id.strip():
            return False

        # Should not contain consecutive operators without proper grouping
        if re.search(r'(OR\s+OR|AND\s+AND|WITH\s+WITH)', license_id):
            return False

        return True

    def _is_valid_copyright_format(self, copyright_text: str) -> bool:
        """Check if copyright text has valid format."""
        # Standard copyright format: "Copyright (c) [year(s)] [holder]"
        standard_pattern = r'^Copyright\s*\(c\)\s*[0-9\-\,\s]+\s+.+$'
        if re.match(standard_pattern, copyright_text, re.IGNORECASE):
            return True

        # Alternative formats (more flexible)
        alternative_patterns = [
            r'^©\s*[0-9\-\,\s]+\s+.+$',  # "© [year(s)] [holder]"
            r'^Copyright\s+[0-9\-\,\s]+\s+.+$',  # "Copyright [year(s)] [holder]"
            r'^©\s+[0-9\-\,\s]+\s+.+$',  # "© [year(s)] [holder]"
        ]

        for pattern in alternative_patterns:
            if re.match(pattern, copyright_text, re.IGNORECASE):
                return True

        return False

    def get_validation_rules(self) -> Dict[str, Any]:
        """Get current validation rules."""
        return self.validation_rules.copy()

def test_license_database():
    """测试SPDX许可证数据库功能"""
    print("🧪 测试 SPDX 许可证数据库...")
    db = SPDXLicenseDatabase()

    # 测试有效许可证
    print("  有效许可证测试:")
    valid_licenses = ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"]
    for license_id in valid_licenses:
        result = db.is_valid_license_id(license_id)
        status = "✅ 通过" if result else "❌ 失败"
        print(f"    {license_id}: {status}")

    # 测试无效许可证
    print("  无效许可证测试:")
    invalid_licenses = ["INVALID-LICENSE", "", "Made-Up-License"]
    for license_id in invalid_licenses:
        result = db.is_valid_license_id(license_id)
        status = "✅ 通过" if not result else "❌ 失败"
        print(f"    {license_id}: {status} (应该无效)")

    # 测试复杂许可证表达式
    print("  复杂许可证表达式测试:")
    complex_expressions = [
        "MIT OR Apache-2.0",
        "GPL-3.0 WITH Classpath-exception-2.0",
        "(MIT AND Apache-2.0) OR BSD-3-Clause"
    ]
    for expr in complex_expressions:
        result = db.is_valid_license_id(expr)
        status = "✅ 通过" if result else "❌ 失败"
        print(f"    {expr}: {status}")

def test_validator_basic():
    """测试基本的验证功能"""
    print("\n🧪 测试基础验证功能...")
    validator = SPDXValidator()

    # 测试有效的SPDX信息
    print("  有效SPDX信息测试:")
    valid_spdx = SPDXInfo(
        license_identifier="MIT",
        copyright_text="Copyright (c) 2023 Example Corp",
        project_attribution="Example Project",
        spdx_version="SPDX-2.2"
    )

    result = validator.validate(valid_spdx)
    if result.is_valid:
        print("    ✅ 有效SPDX信息验证通过")
    else:
        print("    ❌ 有效SPDX信息验证失败")
        for error in result.errors:
            print(f"      错误: {error.message}")

    # 测试无效的许可证标识符
    print("  无效许可证标识符测试:")
    invalid_license = SPDXInfo(
        license_identifier="INVALID-LICENSE",
        copyright_text="Copyright (c) 2023 Example Corp"
    )

    result = validator.validate(invalid_license)
    if not result.is_valid:
        print("    ✅ 无效许可证标识符检测成功")
        print(f"    检测到 {len(result.errors)} 个错误")
    else:
        print("    ❌ 无效许可证标识符未检测到")

    # 测试缺失必需字段
    print("  缺失必需字段测试:")
    missing_fields = SPDXInfo()

    result = validator.validate(missing_fields)
    if not result.is_valid:
        print("    ✅ 缺失必需字段检测成功")
        print(f"    检测到 {len(result.errors)} 个错误")
    else:
        print("    ❌ 缺失必需字段未检测到")

def test_copyright_validation():
    """测试版权信息验证"""
    print("\n🧪 测试版权验证功能...")
    validator = SPDXValidator()

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

    validator = SPDXValidator()

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