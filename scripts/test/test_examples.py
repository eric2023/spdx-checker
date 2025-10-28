#!/usr/bin/env python3
"""
验证 examples 目录中的示例文件
测试SPDX声明的准确性和规范性
"""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def verify_examples():
    """验证examples目录中的示例文件"""
    print("=" * 80)
    print("验证 Examples 目录中的示例文件")
    print("=" * 80)

    from spdx_scanner.scanner import FileScanner
    from spdx_scanner.parser import SPDXParser
    from spdx_scanner.validator import SPDXValidator

    examples_dir = Path('examples')
    scanner = FileScanner()
    parser = SPDXParser()
    validator = SPDXValidator()

    print("\n示例文件位置:")
    print(f"  {examples_dir.absolute()}\n")

    # 统计信息
    total_files = 0
    valid_files = 0
    invalid_files = 0

    print("详细验证结果:")
    print("-" * 80)

    for file_info in scanner.scan_directory(examples_dir):
        # 只检查源代码文件
        if file_info.language in ['python', 'javascript', 'c', 'java', 'cpp']:
            total_files += 1
            print(f"\n📄 文件: {file_info.filepath.name}")
            print(f"   语言: {file_info.language}")
            print(f"   编码: {file_info.encoding}")

            # 解析SPDX信息
            spdx_info = parser.parse_file(file_info)

            if spdx_info.has_minimal_info():
                print(f"   ✅ 许可证标识符: {spdx_info.license_identifier}")
                print(f"   ✅ 版权信息: {spdx_info.copyright_text}")

                if spdx_info.project_attribution:
                    print(f"   ✅ 项目归属: {spdx_info.project_attribution}")
                else:
                    print(f"   ℹ️  项目归属: (可选)")

                # 验证
                result = validator.validate(spdx_info)

                if result.is_valid:
                    print(f"   ✅ 验证结果: 通过")
                    valid_files += 1
                else:
                    print(f"   ❌ 验证结果: 失败")
                    invalid_files += 1
                    if result.errors:
                        for error in result.errors:
                            print(f"      - {error.severity.value}: {error.message}")
                            if error.suggestion:
                                print(f"        建议: {error.suggestion}")

                # 检查规范性问题
                issues = []
                if '2023' in spdx_info.copyright_text or '2024' in spdx_info.copyright_text:
                    issues.append("⚠️  版权年份过时")

                if 'Example' in spdx_info.copyright_text:
                    issues.append("⚠️  使用了示例信息")

                if spdx_info.project_attribution and 'Example' in spdx_info.project_attribution:
                    issues.append("⚠️  使用了示例信息")

                if issues:
                    for issue in issues:
                        print(f"   {issue}")
                else:
                    print(f"   ✅ 规范检查: 无问题")

            else:
                print(f"   ❌ 未找到SPDX声明")
                invalid_files += 1

    print("\n" + "=" * 80)
    print("验证汇总")
    print("=" * 80)
    print(f"总文件数: {total_files}")
    print(f"有效文件: {valid_files}")
    print(f"无效文件: {invalid_files}")
    print(f"成功率: {(valid_files / total_files * 100) if total_files > 0 else 0:.1f}%")

    if invalid_files == 0:
        print("\n✅ 所有示例文件都符合SPDX规范！")
    else:
        print(f"\n⚠️  有 {invalid_files} 个文件需要修正")

    return invalid_files == 0


def show_file_contents():
    """显示示例文件内容"""
    print("\n" + "=" * 80)
    print("示例文件内容")
    print("=" * 80)

    examples = {
        'Python': Path('examples/example.py'),
        'JavaScript': Path('examples/example.js'),
        'C': Path('examples/example.c'),
    }

    for name, filepath in examples.items():
        if filepath.exists():
            print(f"\n{name} 示例文件 ({filepath}):")
            print("-" * 80)

            # 读取前10行（包含SPDX头部）
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
                for line in lines:
                    print(line.rstrip())

            if len(lines) >= 10:
                print("...")


def main():
    """主函数"""
    # 验证示例文件
    all_valid = verify_examples()

    # 显示文件内容
    show_file_contents()

    print("\n" + "=" * 80)
    print("说明")
    print("=" * 80)
    print("""
examples 目录包含以下示例文件：

1. example.py  - Python示例文件
   - 展示Python代码中SPDX许可证声明的正确格式
   - 使用 # 注释风格

2. example.js  - JavaScript示例文件
   - 展示JavaScript代码中SPDX许可证声明的正确格式
   - 使用 // 注释风格

3. example.c   - C语言示例文件
   - 展示C语言代码中SPDX许可证声明的正确格式
   - 使用 /* */ 注释风格

SPDX声明格式规范：
- 第一行: SPDX-License-Identifier: <许可证标识符>
- 第二行: Copyright (c) <年份> <版权持有者>
- 第三行: <项目名称> (可选)

许可证标识符应来自 SPDX 许可证列表：
https://spdx.org/licenses/

示例中使用的许可证：
- MIT: 麻省理工学院许可证（宽松许可证）
""")

    return 0 if all_valid else 1


if __name__ == '__main__':
    sys.exit(main())
