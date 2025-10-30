#!/usr/bin/env python3
"""
SPDX Scanner 演示脚本

展示SPDX Scanner的核心功能和用法。
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """主演示函数"""
    print("🎯 SPDX Scanner 功能演示")
    print("=" * 50)

    print("✅ 1. 验证工具演示")
    print("   运行验证工具展示核心功能...")
    print("   命令: python tools/verification/automated_verifier.py --mode quick")

    print("\n✅ 2. 标准验证演示")
    print("   运行标准验证展示完整功能...")
    print("   命令: python tools/verification/automated_verifier.py --mode standard")

    print("\n✅ 3. 生成报告演示")
    print("   生成HTML验证报告...")
    print("   命令: python tools/verification/automated_verifier.py --mode standard --format html --output demo_report.html")

    print("\n📁 4. 示例文件演示")
    print("   展示项目中的示例文件:")

    examples_dir = Path("examples")
    if examples_dir.exists():
        for example_file in examples_dir.glob("example.*"):
            print(f"   - {example_file.name}")
    else:
        print("   - examples目录不存在")

    print("\n🔧 5. CLI功能演示")
    print("   （需要安装依赖）")
    print("   安装命令: pip install -e '.[dev]'")
    print("   使用命令: spdx-scanner scan examples/")

    print("\n🎉 演示完成！")
    print("=" * 50)
    print("💡 提示: 运行 'make demo' 获得更完整的演示")

if __name__ == "__main__":
    main()