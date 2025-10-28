#!/usr/bin/env python3
"""
SPDX Scanner 自动化验证工具

统一的自动化验证框架，整合所有验证功能，确保SPDX Scanner各组件正常工作。

使用方法:
    python tools/verification/automated_verifier.py --mode [quick|standard|full|ci]
    python tools/verification/automated_verifier.py --verify-spdx --verify-quality --verify-integration
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

# 添加项目根目录和src到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from spdx_scanner.scanner import FileScanner, create_default_scanner
    from spdx_scanner.parser import SPDXParser
    from spdx_scanner.validator import SPDXValidator
    from spdx_scanner.corrector import SPDXCorrector
    from spdx_scanner.reporter import ReportGenerator
    from spdx_scanner.models import ScanResult, SPDXInfo, ValidationResult
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保您在项目根目录中运行此脚本")
    sys.exit(1)

# 添加工具目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from spdx_validator import SPDXComponentValidator
from quality_checker import CodeQualityChecker
from integration_tester import IntegrationTester
from auto_corrector import AutoCorrector


@dataclass
class VerificationResult:
    """验证结果"""
    timestamp: str
    mode: str
    duration: float
    overall_status: str  # 'PASS', 'FAIL', 'WARNING'
    components: Dict[str, Dict[str, Any]]
    issues_found: List[Dict[str, Any]]
    auto_fixes_applied: List[Dict[str, Any]]
    recommendations: List[str]


class AutomatedVerifier:
    """自动化验证器主类"""

    def __init__(self, project_root: Path, config: Optional[Dict] = None):
        self.project_root = project_root
        self.config = config or self._load_default_config()
        self.logger = self._setup_logging()

        # 验证结果存储
        self.verification_result = None

        # 初始化各验证模块
        self.spdx_validator = SPDXComponentValidator(project_root, self.config.get('spdx', {}))
        self.quality_checker = CodeQualityChecker(project_root, self.config.get('quality', {}))
        self.integration_tester = IntegrationTester(project_root, self.config.get('integration', {}))
        self.auto_corrector = AutoCorrector(project_root, self.config.get('auto_fix', {}))
        self.report_generator = SimpleReportGenerator(self.config.get('report', {}))

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        config_file = self.project_root / "tools" / "verification" / "config.yaml"
        if config_file.exists():
            # TODO: 加载YAML配置
            pass

        # 默认配置
        return {
            'spdx': {
                'verify_parser': True,
                'verify_validator': True,
                'verify_corrector': True,
                'verify_reporter': True,
                'accuracy_threshold': 0.95
            },
            'quality': {
                'max_complexity': 15,
                'min_coverage': 0.80,
                'check_duplicates': True,
                'check_dependencies': True
            },
            'integration': {
                'test_cli': True,
                'test_config': True,
                'test_git_integration': True,
                'test_report_formats': True
            },
            'auto_fix': {
                'enable_auto_fix': True,
                'backup_files': True,
                'fix_code_quality': True,
                'fix_test_issues': True
            },
            'report': {
                'format': 'console',
                'include_details': True,
                'include_recommendations': True
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def verify_all(self, mode: str = 'standard') -> VerificationResult:
        """执行完整验证"""
        start_time = time.time()
        self.logger.info(f"开始执行 {mode} 模式验证...")

        components_results = {}
        issues_found = []
        auto_fixes = []
        verification_result = 'PASS'  # 默认状态
        duration = 0.0  # 初始化duration

        try:
            # 1. SPDX组件验证
            if mode in ['standard', 'full', 'ci']:
                self.logger.info("执行SPDX组件验证...")
                spdx_result = self.spdx_validator.verify_all()
                components_results['spdx'] = asdict(spdx_result)
                issues_found.extend(spdx_result.issues)

            # 2. 代码质量验证
            if mode in ['standard', 'full']:
                self.logger.info("执行代码质量验证...")
                quality_result = self.quality_checker.analyze()
                components_results['quality'] = asdict(quality_result)
                issues_found.extend(quality_result.issues)

            # 3. 集成测试验证
            if mode in ['full', 'ci']:
                self.logger.info("执行集成测试验证...")
                integration_result = self.integration_tester.run_all_tests()
                components_results['integration'] = asdict(integration_result)
                issues_found.extend(integration_result.issues)

            # 4. 快速验证模式
            if mode == 'quick':
                self.logger.info("执行快速验证...")
                quick_result = self._quick_verify()
                components_results['quick'] = quick_result
                issues_found.extend(quick_result['issues'])

            # 5. 自动修正（如果启用）
            if self.config['auto_fix']['enable_auto_fix'] and issues_found:
                self.logger.info("应用自动修正...")
                fix_result = self.auto_corrector.auto_fix_issues(issues_found)
                auto_fixes = fix_result.fixes_applied

            # 6. 重新验证（如果应用了修正）
            if auto_fixes:
                self.logger.info("重新验证修正结果...")
                verification_result = self._determine_overall_status(components_results, auto_fixes)
            else:
                verification_result = self._determine_overall_status(components_results, [])

            # 构建最终结果
            result = VerificationResult(
                timestamp=datetime.now().isoformat(),
                mode=mode,
                duration=duration,
                overall_status=verification_result,
                components=components_results,
                issues_found=issues_found,
                auto_fixes_applied=auto_fixes,
                recommendations=self._generate_recommendations(issues_found)
            )

            self.verification_result = result
            return result

        except Exception as e:
            self.logger.error(f"验证过程中发生错误: {e}")
            components_results['error'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            verification_result = 'FAIL'
            duration = time.time() - start_time  # 在except块中也计算duration

        # 在所有情况下都要计算duration
        duration = time.time() - start_time

        # 构建最终结果
        result = VerificationResult(
            timestamp=datetime.now().isoformat(),
            mode=mode,
            duration=duration,
            overall_status=verification_result,
            components=components_results,
            issues_found=issues_found,
            auto_fixes_applied=auto_fixes,
            recommendations=self._generate_recommendations(issues_found)
        )

        self.verification_result = result
        return result

    def _quick_verify(self) -> Dict[str, Any]:
        """快速验证 - 基础功能检查"""
        quick_result = {
            'status': 'PASS',
            'issues': [],
            'checks': []
        }

        try:
            # 检查核心模块是否可以导入
            core_modules = ['scanner', 'parser', 'validator', 'corrector']
            for module in core_modules:
                try:
                    __import__(f'spdx_scanner.{module}')
                    quick_result['checks'].append(f'✓ {module} 导入成功')
                except ImportError as e:
                    quick_result['checks'].append(f'✗ {module} 导入失败: {e}')
                    quick_result['issues'].append({
                        'type': 'import_error',
                        'module': module,
                        'severity': 'HIGH'
                    })

            # 检查配置文件
            config_file = self.project_root / "spdx-scanner.config.json"
            if config_file.exists():
                quick_result['checks'].append('✓ 配置文件存在')
            else:
                quick_result['checks'].append('⚠ 配置文件不存在')

            # 检查CLI可执行性
            cli_file = self.project_root / "src" / "spdx_scanner" / "__main__.py"
            if cli_file.exists():
                quick_result['checks'].append('✓ CLI入口点存在')
            else:
                quick_result['issues'].append({
                    'type': 'missing_file',
                    'file': 'CLI入口点',
                    'severity': 'MEDIUM'
                })

            # 确定状态
            if quick_result['issues']:
                quick_result['status'] = 'FAIL'

        except Exception as e:
            quick_result['status'] = 'FAIL'
            quick_result['error'] = str(e)

        return quick_result

    def _determine_overall_status(self, components_results: Dict, auto_fixes: List) -> str:
        """确定整体验证状态"""
        if 'error' in components_results:
            return 'FAIL'

        # 检查是否有失败的关键组件
        critical_failures = 0
        warnings = 0

        for component, result in components_results.items():
            if isinstance(result, dict):
                status = result.get('status', 'UNKNOWN')
                if status == 'FAIL':
                    critical_failures += 1
                elif status == 'WARNING':
                    warnings += 1

        if critical_failures > 0:
            return 'FAIL'
        elif warnings > 2:
            return 'WARNING'
        else:
            return 'PASS'

    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于问题类型生成建议
        issue_types = {}
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        if 'import_error' in issue_types:
            recommendations.append("检查项目依赖，确保所有必需的模块都已正确安装")

        if 'code_quality' in issue_types:
            recommendations.append("运行代码质量分析，修复发现的问题以提高代码可维护性")

        if 'test_failure' in issue_types:
            recommendations.append("运行测试套件，修复失败的测试用例以确保功能正确性")

        if 'missing_file' in issue_types:
            recommendations.append("检查项目结构，确保所有必需的文件都存在")

        # 通用建议
        recommendations.extend([
            "定期运行自动化验证以确保代码质量",
            "建立持续集成流程，在代码提交前自动验证",
            "保持测试覆盖率在80%以上",
            "及时修复发现的问题，避免技术债务累积"
        ])

        return recommendations

    def generate_report(self, output_format: str = 'console', output_file: Optional[str] = None):
        """生成验证报告"""
        if not self.verification_result:
            raise ValueError("请先运行验证！")

        return self.report_generator.generate(
            self.verification_result,
            output_format,
            output_file
        )


class SimpleReportGenerator:
    """简化的报告生成器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def generate(self, result: VerificationResult, output_format: str = 'console', output_file: Optional[str] = None) -> str:
        """生成验证报告"""
        if output_format == 'console':
            return self._generate_console_report(result, output_file)
        elif output_format == 'json':
            return self._generate_json_report(result, output_file)
        elif output_format == 'html':
            return self._generate_html_report(result, output_file)
        elif output_format == 'markdown':
            return self._generate_markdown_report(result, output_file)
        else:
            raise ValueError(f"不支持的报告格式: {output_format}")

    def _generate_console_report(self, result: VerificationResult, output_file: Optional[str] = None) -> str:
        """生成控制台报告"""
        lines = []

        # 标题
        lines.append("=" * 80)
        lines.append("🔍 SPDX Scanner 自动化验证报告")
        lines.append("=" * 80)
        lines.append(f"生成时间: {result.timestamp}")
        lines.append(f"验证模式: {result.mode}")
        lines.append(f"验证耗时: {result.duration:.2f}秒")
        lines.append(f"整体状态: {self._format_status(result.overall_status)}")
        lines.append("")

        # 验证摘要
        lines.append("📊 验证摘要")
        lines.append("-" * 40)
        lines.append(f"发现问题数量: {len(result.issues_found)}")
        lines.append(f"自动修复数量: {len(result.auto_fixes_applied)}")
        lines.append(f"验证组件数量: {len(result.components)}")

        # 问题详情
        if result.issues_found:
            lines.append("")
            lines.append("⚠️  发现的问题")
            lines.append("-" * 40)
            for i, issue in enumerate(result.issues_found[:10], 1):  # 最多显示10个问题
                severity = issue.get('severity', 'UNKNOWN')
                issue_type = issue.get('type', 'unknown')
                message = issue.get('message', '无详细信息')
                lines.append(f"{i}. [{severity}] {issue_type}: {message}")

        # 自动修复详情
        if result.auto_fixes_applied:
            lines.append("")
            lines.append("🔧 自动修复")
            lines.append("-" * 40)
            for i, fix in enumerate(result.auto_fixes_applied[:5], 1):  # 最多显示5个修复
                fix_type = fix.get('type', 'unknown')
                description = fix.get('description', '无描述')
                lines.append(f"{i}. {fix_type}: {description}")

        # 改进建议
        if result.recommendations:
            lines.append("")
            lines.append("💡 改进建议")
            lines.append("-" * 40)
            for i, recommendation in enumerate(result.recommendations[:5], 1):
                lines.append(f"{i}. {recommendation}")

        lines.append("")
        lines.append("=" * 80)

        report_content = "\n".join(lines)

        # 输出到文件或控制台
        if output_file:
            Path(output_file).write_text(report_content, encoding='utf-8')
            print(f"报告已保存到: {output_file}")
        else:
            print(report_content)

        return report_content

    def _format_status(self, status: str) -> str:
        """格式化状态显示"""
        status_map = {
            'PASS': '✅ 通过',
            'FAIL': '❌ 失败',
            'WARNING': '⚠️  警告',
            'UNKNOWN': '❓ 未知'
        }
        return status_map.get(status, status)

    def _generate_json_report(self, result: VerificationResult, output_file: Optional[str] = None) -> str:
        """生成JSON报告"""
        report_data = asdict(result)
        report_json = json.dumps(report_data, indent=2, ensure_ascii=False)

        if output_file:
            Path(output_file).write_text(report_json, encoding='utf-8')
            print(f"JSON报告已保存到: {output_file}")
        else:
            print(report_json)

        return report_json

    def _generate_html_report(self, result: VerificationResult, output_file: Optional[str] = None) -> str:
        """生成HTML报告"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPDX Scanner 验证报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ text-align: center; border-bottom: 3px solid #007acc; padding-bottom: 20px; }}
        .status {{ display: inline-block; padding: 5px 15px; border-radius: 20px; color: white; font-weight: bold; }}
        .status-pass {{ background-color: #28a745; }}
        .status-fail {{ background-color: #dc3545; }}
        .status-warning {{ background-color: #ffc107; color: #333; }}
        .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007acc; }}
        .issue {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .fix {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 10px; margin: 5px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 SPDX Scanner 验证报告</h1>
        <p>生成时间: {result.timestamp}</p>
        <p>验证模式: {result.mode}</p>
        <p>整体状态: <span class="status status-{result.overall_status.lower()}">{self._format_status(result.overall_status)}</span></p>
    </div>

    <div class="section">
        <h2>📊 验证摘要</h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{len(result.issues_found)}</div>
                <div>发现问题</div>
            </div>
            <div class="metric">
                <div class="metric-value">{len(result.auto_fixes_applied)}</div>
                <div>自动修复</div>
            </div>
            <div class="metric">
                <div class="metric-value">{len(result.components)}</div>
                <div>验证组件</div>
            </div>
        </div>
    </div>
"""

        # 添加问题详情
        if result.issues_found:
            html_content += """
    <div class="section">
        <h2>⚠️ 发现的问题</h2>
"""
            for i, issue in enumerate(result.issues_found[:10], 1):
                severity = issue.get('severity', 'UNKNOWN').lower()
                issue_type = issue.get('type', 'unknown')
                message = issue.get('message', '无详细信息')
                html_content += f"""
        <div class="issue">
            <strong>{i}. [{issue.get('severity', 'UNKNOWN')}] {issue_type}</strong><br>
            {message}
        </div>
"""
            html_content += "    </div>\n"

        # 添加修复详情
        if result.auto_fixes_applied:
            html_content += """
    <div class="section">
        <h2>🔧 自动修复</h2>
"""
            for i, fix in enumerate(result.auto_fixes_applied[:5], 1):
                fix_type = fix.get('type', 'unknown')
                description = fix.get('description', '无描述')
                html_content += f"""
        <div class="fix">
            <strong>{i}. {fix_type}</strong><br>
            {description}
        </div>
"""
            html_content += "    </div>\n"

        html_content += """
</body>
</html>
"""

        if output_file:
            Path(output_file).write_text(html_content, encoding='utf-8')
            print(f"HTML报告已保存到: {output_file}")
        else:
            print(html_content)

        return html_content

    def _generate_markdown_report(self, result: VerificationResult, output_file: Optional[str] = None) -> str:
        """生成Markdown报告"""
        lines = []

        # 标题
        lines.append("# 🔍 SPDX Scanner 验证报告")
        lines.append("")
        lines.append(f"- **生成时间:** {result.timestamp}")
        lines.append(f"- **验证模式:** {result.mode}")
        lines.append(f"- **整体状态:** {self._format_status(result.overall_status)}")
        lines.append(f"- **发现问题:** {len(result.issues_found)} 个")
        lines.append(f"- **自动修复:** {len(result.auto_fixes_applied)} 个")
        lines.append("")

        # 问题详情
        if result.issues_found:
            lines.append("## ⚠️ 发现的问题")
            lines.append("")
            for i, issue in enumerate(result.issues_found[:10], 1):
                severity = issue.get('severity', 'UNKNOWN')
                issue_type = issue.get('type', 'unknown')
                message = issue.get('message', '无详细信息')
                lines.append(f"### {i}. [{severity}] {issue_type}")
                lines.append("")
                lines.append(f"{message}")
                lines.append("")

        # 修复详情
        if result.auto_fixes_applied:
            lines.append("## 🔧 自动修复")
            lines.append("")
            for i, fix in enumerate(result.auto_fixes_applied[:5], 1):
                fix_type = fix.get('type', 'unknown')
                description = fix.get('description', '无描述')
                lines.append(f"### {i}. {fix_type}")
                lines.append("")
                lines.append(f"{description}")
                lines.append("")

        report_content = "\n".join(lines)

        if output_file:
            Path(output_file).write_text(report_content, encoding='utf-8')
            print(f"Markdown报告已保存到: {output_file}")
        else:
            print(report_content)

        return report_content

    def generate_report(self, output_format: str = 'console', output_file: Optional[str] = None):
        """生成验证报告"""
        if not self.verification_result:
            raise ValueError("请先运行验证！")

        return self.report_generator.generate(
            self.verification_result,
            output_format,
            output_file
        )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SPDX Scanner 自动化验证工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tools/verification/automated_verifier.py --mode quick
  python tools/verification/automated_verifier.py --mode standard
  python tools/verification/automated_verifier.py --mode full --format html --output report.html
  python tools/verification/automated_verifier.py --verify-spdx --verify-quality
        """
    )

    parser.add_argument(
        '--mode',
        choices=['quick', 'standard', 'full', 'ci'],
        default='standard',
        help='验证模式 (默认: standard)'
    )

    parser.add_argument(
        '--verify-spdx',
        action='store_true',
        help='仅验证SPDX组件'
    )

    parser.add_argument(
        '--verify-quality',
        action='store_true',
        help='仅验证代码质量'
    )

    parser.add_argument(
        '--verify-integration',
        action='store_true',
        help='仅验证集成功能'
    )

    parser.add_argument(
        '--format',
        choices=['console', 'json', 'html', 'markdown'],
        default='console',
        help='报告格式 (默认: console)'
    )

    parser.add_argument(
        '--output',
        help='输出文件路径'
    )

    parser.add_argument(
        '--no-auto-fix',
        action='store_true',
        help='禁用自动修正'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 创建验证器实例
    project_root = Path.cwd()
    verifier = AutomatedVerifier(project_root)

    # 禁用自动修正（如果指定）
    if args.no_auto_fix:
        verifier.config['auto_fix']['enable_auto_fix'] = False

    try:
        # 根据参数选择验证模式
        if args.verify_spdx:
            result = verifier.spdx_validator.verify_all()
            status = result.status
        elif args.verify_quality:
            result = verifier.quality_checker.analyze()
            status = result.status
        elif args.verify_integration:
            result = verifier.integration_tester.run_all_tests()
            status = result.status
        else:
            result = verifier.verify_all(args.mode)
            status = result.overall_status

        # 生成报告
        verifier.generate_report(args.format, args.output)

        # 输出总结
        print(f"\n{'='*60}")
        print(f"验证完成！整体状态: {status}")
        print(f"总耗时: {result.duration:.2f}秒")
        print(f"{'='*60}")

        # 根据状态设置退出码
        if status == 'FAIL':
            sys.exit(1)
        elif status == 'WARNING':
            sys.exit(2)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n验证被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n验证过程中发生错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()