#!/usr/bin/env python3
"""
SPDX Scanner 质量管理工具

执行全面的代码质量检查，确保项目维护在高质量标准。
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """运行命令并返回结果"""
    print(f"🔄 执行: {description}")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        duration = time.time() - start_time
        success = result.returncode == 0

        if success:
            print(f"✅ {description} - 耗时: {duration:.2f}秒")
        else:
            error_output = result.stderr.strip()
            if "No module named" in error_output:
                print(f"⚠️  {description} - 依赖未安装，跳过")
                print(f"   提示: 安装开发依赖 `pip install -e \"[dev]\"`")
                return False, "依赖未安装"
            else:
                print(f"❌ {description} - 耗时: {duration:.2f}秒")
                print(f"错误输出: {error_output}")

        return success, result.stdout + result.stderr

    except Exception as e:
        print(f"💥 {description} - 异常: {str(e)}")
        return False, str(e)

def check_test_coverage() -> bool:
    """检查测试覆盖率"""
    success, output = run_command(
        ["python", "-m", "pytest", "tests/", "--cov=src/spdx_scanner", "--cov-report=term-missing"],
        "测试覆盖率检查"
    )

    if success:
        # 解析覆盖率百分比
        lines = output.split('\n')
        for line in lines:
            if 'TOTAL' in line and '%' in line:
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        coverage = float(part.replace('%', ''))
                        if coverage >= 80:
                            print(f"📊 测试覆盖率: {coverage}% ✅")
                            return True
                        else:
                            print(f"📊 测试覆盖率: {coverage}% ❌ (需要≥80%)")
                            return False

    return False

def run_quality_checks() -> Dict[str, bool]:
    """运行全面的质量检查"""
    results = {}

    print("🔍 开始代码质量检查...")
    print("=" * 50)

    # 1. 代码格式检查
    results['black_format'] = run_command(
        ["python", "-m", "black", "--check", "src/", "tests/", "tools/"],
        "代码格式检查 (Black)"
    )[0]

    # 2. 导入排序检查
    results['isort_imports'] = run_command(
        ["python", "-m", "isort", "--check-only", "src/", "tests/", "tools/"],
        "导入排序检查 (isort)"
    )[0]

    # 3. 代码风格检查
    results['flake8_style'] = run_command(
        ["python", "-m", "flake8", "src/", "tests/", "tools/"],
        "代码风格检查 (flake8)"
    )[0]

    # 4. 类型检查
    results['mypy_types'] = run_command(
        ["python", "-m", "mypy", "src/"],
        "类型检查 (mypy)"
    )[0]

    # 5. 自动化验证
    results['automated_verification'] = run_command(
        ["python", "tools/verification/automated_verifier.py", "--mode", "quick"],
        "自动化验证 (快速模式)"
    )[0]

    # 6. 测试覆盖率
    results['test_coverage'] = check_test_coverage()

    print("=" * 50)
    return results

def generate_quality_report(results: Dict[str, bool]) -> None:
    """生成质量报告"""
    print("\n📋 质量检查报告")
    print("=" * 50)

    total_checks = len(results)
    passed_checks = sum(results.values())

    for check_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        check_display = check_name.replace('_', ' ').title()
        print(f"{check_display}: {status}")

    print(f"\n📊 总计: {passed_checks}/{total_checks} 项检查通过")

    if passed_checks == total_checks:
        print("🎉 所有质量检查通过！代码质量优秀！")
    elif passed_checks >= total_checks * 0.8:
        print("⚠️  大部分检查通过，质量尚可，建议修复失败项目")
    else:
        print("💥 质量检查失败过多，需要立即修复")

def main():
    """主函数"""
    print("🔍 SPDX Scanner 质量管理工具")
    print("=" * 50)

    results = run_quality_checks()
    generate_quality_report(results)

    # 返回适当的退出码
    if all(results.values()):
        sys.exit(0)  # 全部通过
    elif sum(results.values()) >= len(results) * 0.8:
        sys.exit(1)  # 大部分通过
    else:
        sys.exit(2)  # 太多失败

if __name__ == "__main__":
    main()