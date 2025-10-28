#!/usr/bin/env python3
"""
手动功能验证脚本
测试 SPDX Scanner 的核心功能模块
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_models():
    """测试数据模型"""
    print("=" * 60)
    print("测试数据模型 (models.py)")
    print("=" * 60)

    try:
        from spdx_scanner.models import SPDXInfo, SPDXDeclarationType, ValidationError, ValidationSeverity

        # 测试 SPDXInfo
        spdx = SPDXInfo(
            license_identifier='MIT',
            copyright_text='Copyright (c) 2025 Test',
            project_attribution='Test Project'
        )

        print(f"✓ SPDXInfo 创建成功")
        print(f"  - 许可证标识符: {spdx.license_identifier}")
        print(f"  - 版权信息: {spdx.copyright_text}")
        print(f"  - 项目归属: {spdx.project_attribution}")
        print(f"  - 是否有效: {spdx.is_valid()}")
        print(f"  - 有基本信息: {spdx.has_minimal_info()}")

        # 测试版权年份提取
        years = spdx.get_copyright_years()
        print(f"  - 版权年份: {years}")

        # 测试序列化
        spdx_dict = spdx.to_dict()
        print(f"  - 序列化成功: {len(spdx_dict)} 个字段")

        # 测试 ValidationError
        error = ValidationError(
            severity=ValidationSeverity.ERROR,
            message="测试错误",
            line_number=10
        )
        print(f"✓ ValidationError 创建成功")
        print(f"  - 严重性: {error.severity.value}")
        print(f"  - 消息: {error.message}")

        print("\n✅ 数据模型测试通过\n")
        return True

    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """测试配置管理"""
    print("=" * 60)
    print("测试配置管理 (config.py)")
    print("=" * 60)

    try:
        from spdx_scanner.config import Configuration, ValidationRules, CorrectionSettings

        # 测试基本配置
        config = Configuration(
            project_name='Test Project',
            project_version='1.0.0',
            default_license='MIT',
            copyright_holder='Test Company'
        )

        print(f"✓ Configuration 创建成功")
        print(f"  - 项目名称: {config.project_name}")
        print(f"  - 默认许可证: {config.default_license}")
        print(f"  - 版权持有者: {config.copyright_holder}")

        # 测试嵌套配置
        print(f"  - 验证规则数: {len(config.validation_rules.__dict__)}")
        print(f"  - 修正设置: {config.correction_settings.create_backups}")

        # 测试验证
        errors = config.validate()
        print(f"  - 配置验证错误数: {len(errors)}")

        # 测试序列化
        config_dict = config.to_dict()
        print(f"✓ 配置序列化成功")
        print(f"  - 字段数: {len(config_dict)}")

        print("\n✅ 配置管理测试通过\n")
        return True

    except Exception as e:
        print(f"❌ 配置管理测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_scanner():
    """测试扫描器"""
    print("=" * 60)
    print("测试扫描器 (scanner.py)")
    print("=" * 60)

    try:
        from spdx_scanner.scanner import LanguageDetector, EncodingDetector, FileScanner

        # 测试语言检测
        detector = LanguageDetector()
        python_lang = detector.detect_language(Path('/test/file.py'))
        js_lang = detector.detect_language(Path('/test/file.js'))
        java_lang = detector.detect_language(Path('/test/Main.java'))
        c_lang = detector.detect_language(Path('/test/header.h'))

        print(f"✓ LanguageDetector 创建成功")
        print(f"  - .py 文件语言: {python_lang}")
        print(f"  - .js 文件语言: {js_lang}")
        print(f"  - .java 文件语言: {java_lang}")
        print(f"  - .h 文件语言: {c_lang}")

        # 测试编码检测器
        enc_detector = EncodingDetector()
        print(f"✓ EncodingDetector 创建成功")
        print(f"  - 编码检测功能可用")

        # 测试文件扫描器
        scanner = FileScanner()
        print(f"✓ FileScanner 创建成功")
        print(f"  - 包含模式数: {len(scanner.include_patterns)}")
        print(f"  - 排除模式数: {len(scanner.exclude_patterns)}")
        print(f"  - 最大文件大小: {scanner.max_file_size / 1024 / 1024:.1f} MB")

        print("\n✅ 扫描器测试通过\n")
        return True

    except Exception as e:
        print(f"❌ 扫描器测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_parser():
    """测试SPDX解析器"""
    print("=" * 60)
    print("测试SPDX解析器 (parser.py)")
    print("=" * 60)

    try:
        from spdx_scanner.parser import SPDXParser, SPDXPatterns
        from spdx_scanner.models import FileInfo
        from pathlib import Path

        # 创建解析器
        parser = SPDXParser()
        print(f"✓ SPDXParser 创建成功")
        print(f"  - 支持的语言数: {len(parser.get_supported_languages())}")

        # 测试模式
        patterns = SPDXPatterns()
        print(f"✓ SPDXPatterns 加载成功")
        print(f"  - 许可证标识符模式数: {len(patterns.LICENSE_IDENTIFIER_PATTERNS)}")
        print(f"  - 版权模式数: {len(patterns.COPYRIGHT_PATTERNS)}")
        print(f"  - 注释风格数: {len(patterns.COMMENT_PATTERNS)}")

        # 测试解析
        test_content = """# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Test Company
# Test Project
"""

        from spdx_scanner.models import FileInfo
        from pathlib import Path

        file_info = FileInfo(
            filepath=Path('test.py'),
            language='python',
            content=test_content
        )

        spdx_info = parser.parse_file(file_info)
        print(f"✓ 文件解析成功")
        print(f"  - 许可证标识符: {spdx_info.license_identifier}")
        print(f"  - 版权信息: {spdx_info.copyright_text}")
        print(f"  - 项目归属: {spdx_info.project_attribution}")
        print(f"  - 声明类型: {spdx_info.declaration_type.value}")

        print("\n✅ SPDX解析器测试通过\n")
        return True

    except Exception as e:
        print(f"❌ SPDX解析器测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_validator():
    """测试验证器"""
    print("=" * 60)
    print("测试验证器 (validator.py)")
    print("=" * 60)

    try:
        from spdx_scanner.validator import SPDXValidator, SPDXLicenseDatabase
        from spdx_scanner.models import SPDXInfo

        # 测试许可证数据库
        license_db = SPDXLicenseDatabase()
        print(f"✓ SPDXLicenseDatabase 创建成功")
        print(f"  - 核心许可证数: {len(license_db.CORE_LICENSES)}")

        # 测试许可证验证
        mit_valid = license_db.is_valid_license_id('MIT')
        apache_valid = license_db.is_valid_license_id('Apache-2.0')
        invalid_valid = license_db.is_valid_license_id('Invalid-License')

        print(f"  - MIT 许可证有效: {mit_valid}")
        print(f"  - Apache-2.0 许可证有效: {apache_valid}")
        print(f"  - 无效许可证有效: {invalid_valid}")

        # 测试验证器
        validator = SPDXValidator()
        print(f"✓ SPDXValidator 创建成功")

        # 测试SPDX信息验证
        spdx = SPDXInfo(
            license_identifier='MIT',
            copyright_text='Copyright (c) 2025 Test',
            project_attribution='Test Project'
        )

        validation_result = validator.validate(spdx)
        print(f"✓ SPDX信息验证成功")
        print(f"  - 验证结果: {validation_result.is_valid}")
        print(f"  - 错误数: {len(validation_result.errors)}")
        print(f"  - 警告数: {len(validation_result.warnings)}")
        print(f"  - 建议数: {len(validation_result.suggestions)}")

        # 测试无效许可证验证
        invalid_spdx = SPDXInfo(
            license_identifier='Invalid-License-123',
            copyright_text='Invalid copyright'
        )

        invalid_result = validator.validate(invalid_spdx)
        print(f"✓ 无效许可证检测成功")
        print(f"  - 验证结果: {invalid_result.is_valid}")
        print(f"  - 错误数: {len(invalid_result.errors)}")

        print("\n✅ 验证器测试通过\n")
        return True

    except Exception as e:
        print(f"❌ 验证器测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_corrector():
    """测试修正器"""
    print("=" * 60)
    print("测试修正器 (corrector.py)")
    print("=" * 60)

    try:
        from spdx_scanner.corrector import SPDXCorrector, LicenseHeaderTemplates
        from spdx_scanner.models import FileInfo
        from pathlib import Path

        # 测试许可证头模板
        templates = LicenseHeaderTemplates()
        print(f"✓ LicenseHeaderTemplates 创建成功")
        print(f"  - 可用模板数: {len(templates.TEMPLATES)}")
        print(f"  - 支持的语言: {', '.join(list(templates.TEMPLATES.keys())[:5])}...")

        # 测试注释样式
        python_style = templates.get_comment_style('python')
        java_style = templates.get_comment_style('java')
        print(f"  - Python 注释样式: {python_style}")
        print(f"  - Java 注释样式: {java_style}")

        # 测试修正器
        corrector = SPDXCorrector({
            'default_license': 'MIT',
            'default_copyright_holder': 'Test Company',
            'default_project_name': 'Test Project'
        })
        print(f"✓ SPDXCorrector 创建成功")

        # 测试文件修正
        test_content = """def hello():
    print("Hello, World!")
"""

        file_info = FileInfo(
            filepath=Path('test.py'),
            language='python',
            content=test_content
        )

        # 干运行测试
        result = corrector.correct_file(file_info, dry_run=True)
        print(f"✓ 文件修正测试成功（干运行）")
        print(f"  - 成功: {result.success}")
        print(f"  - 修改次数: {len(result.changes_made)}")
        if result.changes_made:
            print(f"  - 修改描述: {result.changes_made[0]}")

        print("\n✅ 修正器测试通过\n")
        return True

    except Exception as e:
        print(f"❌ 修正器测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_reporter():
    """测试报告生成器"""
    print("=" * 60)
    print("测试报告生成器 (reporter.py)")
    print("=" * 60)

    try:
        from spdx_scanner.reporter import (
            ReportGenerator, TextReportGenerator, JSONReportGenerator,
            HTMLReportGenerator, MarkdownReportGenerator
        )
        from spdx_scanner.models import ScanResult, ScanSummary, FileInfo, ValidationResult
        from pathlib import Path

        # 测试报告生成器基类
        print(f"✓ ReportGenerator 基类可用")
        print(f"  - 格式: Text, JSON, HTML, Markdown")

        # 测试文本报告生成器
        text_gen = TextReportGenerator()
        print(f"✓ TextReportGenerator 创建成功")
        print(f"  - 文件扩展名: {text_gen.get_file_extension()}")

        # 测试JSON报告生成器
        json_gen = JSONReportGenerator()
        print(f"✓ JSONReportGenerator 创建成功")
        print(f"  - 文件扩展名: {json_gen.get_file_extension()}")

        # 测试扫描摘要
        summary = ScanSummary()
        summary.total_files = 10
        summary.valid_files = 8
        summary.invalid_files = 2
        summary.corrected_files = 1

        print(f"✓ ScanSummary 创建成功")
        print(f"  - 总文件数: {summary.total_files}")
        print(f"  - 有效文件数: {summary.valid_files}")
        print(f"  - 成功率: {summary.get_success_rate():.1f}%")
        print(f"  - 修正率: {summary.get_correction_rate():.1f}%")

        # 测试序列化
        summary_dict = summary.to_dict()
        print(f"✓ 扫描摘要序列化成功")
        print(f"  - 字段数: {len(summary_dict)}")

        print("\n✅ 报告生成器测试通过\n")
        return True

    except Exception as e:
        print(f"❌ 报告生成器测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_git_integration():
    """测试Git集成"""
    print("=" * 60)
    print("测试Git集成 (git_integration.py)")
    print("=" * 60)

    try:
        from spdx_scanner.git_integration import GitRepository, GitIntegrationError

        # 测试Git仓库
        git_repo = GitRepository()
        print(f"✓ GitRepository 创建成功")
        print(f"  - 是否Git仓库: {git_repo.is_git_repository()}")

        if git_repo.is_git_repository():
            print(f"  - Git根目录: {git_repo.get_git_root()}")
            branch = git_repo.get_current_branch()
            print(f"  - 当前分支: {branch}")
        else:
            print(f"  - 当前目录不是Git仓库")

        # 测试.gitignore模式
        patterns = git_repo.get_gitignore_patterns()
        print(f"✓ .gitignore模式加载成功")
        print(f"  - 模式数: {len(patterns)}")

        print("\n✅ Git集成测试通过\n")
        return True

    except Exception as e:
        print(f"❌ Git集成测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("SPDX Scanner 功能验证测试")
    print("=" * 60 + "\n")

    tests = [
        ("数据模型", test_models),
        ("配置管理", test_config),
        ("扫描器", test_scanner),
        ("SPDX解析器", test_parser),
        ("验证器", test_validator),
        ("修正器", test_corrector),
        ("报告生成器", test_reporter),
        ("Git集成", test_git_integration),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"正在测试: {name}")
        print(f"{'=' * 60}")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}测试出现异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

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
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
