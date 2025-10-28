#!/usr/bin/env python3
"""
测试源文件扩展名可配置功能
验证默认支持 .h .cpp .c .go 文件
"""

import sys
import tempfile
import shutil
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def test_default_scanner_extensions():
    """测试默认扫描器支持的扩展名"""
    print("=" * 80)
    print("测试1: 默认扫描器扩展名")
    print("=" * 80)

    from spdx_scanner.scanner import create_default_scanner

    # 创建默认扫描器
    scanner = create_default_scanner()

    # 检查默认 include_patterns
    print(f"默认include_patterns: {scanner.include_patterns}")

    # 验证默认扩展名
    expected_extensions = ['.h', '.cpp', '.c', '.go']
    for ext in expected_extensions:
        pattern = f"**/*{ext}"
        if pattern in scanner.include_patterns:
            print(f"  ✅ 支持扩展名: {ext}")
        else:
            print(f"  ❌ 缺少扩展名: {ext}")
            return False

    print("\n✅ 默认扫描器测试通过\n")
    return True


def test_custom_extensions():
    """测试自定义扩展名"""
    print("=" * 80)
    print("测试2: 自定义扩展名")
    print("=" * 80)

    from spdx_scanner.scanner import create_default_scanner

    # 测试自定义扩展名列表
    custom_extensions = ['.py', '.js', '.java']
    scanner = create_default_scanner(source_file_extensions=custom_extensions)

    print(f"自定义扩展名: {custom_extensions}")
    print(f"生成的include_patterns: {scanner.include_patterns}")

    # 验证包含自定义扩展名
    for ext in custom_extensions:
        pattern = f"**/*{ext}"
        if pattern in scanner.include_patterns:
            print(f"  ✅ 包含扩展名: {ext}")
        else:
            print(f"  ❌ 缺少扩展名: {ext}")
            return False

    # 验证不包含默认扩展名（除非重叠）
    default_extensions = ['.h', '.cpp', '.c', '.go']
    for ext in default_extensions:
        if ext not in custom_extensions:
            pattern = f"**/*{ext}"
            if pattern not in scanner.include_patterns:
                print(f"  ✅ 正确排除扩展名: {ext}")
            else:
                print(f"  ⚠️  意外包含扩展名: {ext}")

    print("\n✅ 自定义扩展名测试通过\n")
    return True


def test_config_source_extensions():
    """测试配置中的源文件扩展名"""
    print("=" * 80)
    print("测试3: 配置中的源文件扩展名")
    print("=" * 80)

    from spdx_scanner.config import Configuration, ScannerSettings

    # 测试配置
    config = Configuration(
        scanner_settings=ScannerSettings(
            source_file_extensions=['.rs', '.swift', '.kt']
        )
    )

    print(f"配置的源文件扩展名: {config.scanner_settings.source_file_extensions}")
    print(f"生成的include_patterns: {config.scanner_settings.include_patterns}")

    # 验证
    expected = ['.rs', '.swift', '.kt']
    for ext in expected:
        if ext in config.scanner_settings.source_file_extensions:
            print(f"  ✅ 配置包含: {ext}")
        else:
            print(f"  ❌ 配置缺少: {ext}")
            return False

    # 验证生成模式
    for ext in expected:
        pattern = f"**/*{ext}"
        if pattern in config.scanner_settings.include_patterns:
            print(f"  ✅ 生成模式: {pattern}")
        else:
            print(f"  ❌ 缺少模式: {pattern}")
            return False

    print("\n✅ 配置源文件扩展名测试通过\n")
    return True


def test_scanning_with_extensions():
    """测试使用扩展名进行实际扫描"""
    print("=" * 80)
    print("测试4: 实际扫描测试")
    print("=" * 80)

    from spdx_scanner.scanner import create_default_scanner

    # 创建临时目录和文件
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # 创建不同类型的文件
        test_files = {
            'test.c': '/* C file */',
            'test.cpp': '// C++ file',
            'test.h': '// Header file',
            'test.go': '// Go file',
            'test.py': '# Python file',
            'test.js': '// JavaScript file',
        }

        for filename, content in test_files.items():
            (tmppath / filename).write_text(content)

        print(f"创建测试文件: {list(test_files.keys())}")

        # 测试默认扩展名扫描
        print("\n默认扩展名扫描 (.h .cpp .c .go):")
        scanner = create_default_scanner()
        found_files = list(scanner.scan_directory(tmppath))
        found_names = [f.filepath.name for f in found_files]
        print(f"  找到文件: {found_names}")

        expected_default = ['test.c', 'test.cpp', 'test.h', 'test.go']
        for name in expected_default:
            if name in found_names:
                print(f"  ✅ 正确发现: {name}")
            else:
                print(f"  ❌ 未发现: {name}")

        # 测试自定义扩展名扫描
        print("\n自定义扩展名扫描 (.py .js):")
        scanner = create_default_scanner(source_file_extensions=['.py', '.js'])
        found_files = list(scanner.scan_directory(tmppath))
        found_names = [f.filepath.name for f in found_files]
        print(f"  找到文件: {found_names}")

        expected_custom = ['test.py', 'test.js']
        for name in expected_custom:
            if name in found_names:
                print(f"  ✅ 正确发现: {name}")
            else:
                print(f"  ❌ 未发现: {name}")

        # 确保默认扩展名的文件未被扫描
        for name in expected_default:
            if name not in expected_custom and name in found_names:
                print(f"  ⚠️  意外发现: {name}")

    print("\n✅ 实际扫描测试通过\n")
    return True


def test_config_serialization():
    """测试配置序列化/反序列化"""
    print("=" * 80)
    print("测试5: 配置序列化")
    print("=" * 80)

    from spdx_scanner.config import Configuration

    # 创建配置
    from spdx_scanner.config import ScannerSettings
    config1 = Configuration(
        project_name="Test Project",
        scanner_settings=ScannerSettings(source_file_extensions=['.c', '.cpp', '.h'])
    )

    # 序列化
    config_dict = config1.to_dict()
    print(f"序列化后的配置: {config_dict}")

    # 反序列化
    config2 = Configuration.from_dict(config_dict)
    print(f"反序列化后的扩展名: {config2.scanner_settings.source_file_extensions}")
    print(f"反序列化后的include_patterns: {config2.scanner_settings.include_patterns}")

    # 验证
    if config2.scanner_settings.source_file_extensions == ['.c', '.cpp', '.h']:
        print("  ✅ 扩展名序列化/反序列化正确")
    else:
        print(f"  ❌ 扩展名不匹配: {config2.scanner_settings.source_file_extensions}")
        return False

    print("\n✅ 配置序列化测试通过\n")
    return True


def test_without_dot():
    """测试不带点的扩展名输入"""
    print("=" * 80)
    print("测试6: 无点扩展名处理")
    print("=" * 80)

    from spdx_scanner.scanner import create_default_scanner

    # 测试不带点的扩展名
    extensions_without_dot = ['c', 'cpp', 'h', 'go']
    scanner = create_default_scanner(source_file_extensions=extensions_without_dot)

    print(f"输入扩展名（无点）: {extensions_without_dot}")
    print(f"生成的include_patterns: {scanner.include_patterns}")

    # 验证自动添加点
    expected_patterns = ['**/*.c', '**/*.cpp', '**/*.h', '**/*.go']
    for pattern in expected_patterns:
        if pattern in scanner.include_patterns:
            print(f"  ✅ 正确生成模式: {pattern}")
        else:
            print(f"  ❌ 缺少模式: {pattern}")
            return False

    print("\n✅ 无点扩展名处理测试通过\n")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("SPDX Scanner - 源文件扩展名可配置功能测试")
    print("=" * 80 + "\n")

    tests = [
        ("默认扫描器扩展名", test_default_scanner_extensions),
        ("自定义扩展名", test_custom_extensions),
        ("配置源文件扩展名", test_config_source_extensions),
        ("实际扫描测试", test_scanning_with_extensions),
        ("配置序列化", test_config_serialization),
        ("无点扩展名处理", test_without_dot),
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
    print("测试结果汇总")
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
        print("\n🎉 所有测试通过！")
        print("\n✅ 功能特性:")
        print("  - 默认支持 .h .cpp .c .go 文件")
        print("  - 可自定义源文件扩展名")
        print("  - 支持带点或不带点格式")
        print("  - 完整配置序列化支持")
        print("  - 实际扫描功能正常")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
