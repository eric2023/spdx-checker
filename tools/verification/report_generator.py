#!/usr/bin/env python3
"""
验证报告生成器

生成多格式的验证报告，包括控制台、JSON、HTML、Markdown等格式。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64
from dataclasses import asdict

# 添加项目根目录和src到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加工具目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from automated_verifier import VerificationResult
from spdx_validator import SPDXValidationResult
from quality_checker import CodeQualityResult
from integration_tester import IntegrationTestResult
from auto_corrector import AutoFixResult


class VerificationReportGenerator:
    """验证报告生成器"""

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

        # 按组件显示详细结果
        for component_name, component_result in result.components.items():
            lines.append("")
            lines.append(f"📋 {component_name.upper()} 组件验证")
            lines.append("-" * 40)

            if isinstance(component_result, dict):
                status = component_result.get('status', 'UNKNOWN')
                lines.append(f"状态: {self._format_status(status)}")

                # 显示组件特定信息
                if component_name == 'spdx':
                    self._format_spdx_component(component_result, lines)
                elif component_name == 'quality':
                    self._format_quality_component(component_result, lines)
                elif component_name == 'integration':
                    self._format_integration_component(component_result, lines)
                elif component_name == 'quick':
                    self._format_quick_component(component_result, lines)
            else:
                lines.append(f"状态: {self._format_status(str(component_result))}")

        # 问题详情
        if result.issues_found:
            lines.append("")
            lines.append("⚠️  发现的问题")
            lines.append("-" * 40)
            for i, issue in enumerate(result.issues_found, 1):
                severity = issue.get('severity', 'UNKNOWN')
                issue_type = issue.get('type', 'unknown')
                message = issue.get('message', '无详细信息')
                lines.append(f"{i}. [{severity}] {issue_type}: {message}")

        # 自动修复详情
        if result.auto_fixes_applied:
            lines.append("")
            lines.append("🔧 自动修复")
            lines.append("-" * 40)
            for i, fix in enumerate(result.auto_fixes_applied, 1):
                fix_type = fix.get('type', 'unknown')
                description = fix.get('description', '无描述')
                lines.append(f"{i}. {fix_type}: {description}")

        # 改进建议
        if result.recommendations:
            lines.append("")
            lines.append("💡 改进建议")
            lines.append("-" * 40)
            for i, recommendation in enumerate(result.recommendations, 1):
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

    def _format_spdx_component(self, component_result: Dict, lines: List[str]):
        """格式化SPDX组件结果"""
        accuracy = component_result.get('accuracy', 0.0)
        test_coverage = component_result.get('test_coverage', 0.0)

        lines.append(f"准确率: {accuracy:.2%}")
        lines.append(f"测试覆盖率: {test_coverage:.2%}")

        component_results = component_result.get('component_results', {})
        if component_results:
            lines.append("组件详情:")
            for comp_name, comp_data in component_results.items():
                comp_status = comp_data.get('status', 'UNKNOWN')
                tests_passed = comp_data.get('passed_tests', 0)
                tests_total = comp_data.get('total_tests', 0)
                lines.append(f"  - {comp_name}: {self._format_status(comp_status)} ({tests_passed}/{tests_total})")

    def _format_quality_component(self, component_result: Dict, lines: List[str]):
        """格式化代码质量组件结果"""
        score = component_result.get('score', 0.0)
        files_analyzed = component_result.get('files_analyzed', 0)
        total_lines = component_result.get('total_lines', 0)
        avg_complexity = component_result.get('average_complexity', 0.0)

        lines.append(f"质量评分: {score:.1f}/10.0")
        lines.append(f"分析文件: {files_analyzed} 个")
        lines.append(f"总代码行: {total_lines:,}")
        lines.append(f"平均复杂度: {avg_complexity:.2f}")

        metrics = component_result.get('metrics', {})
        if metrics:
            complexity_dist = metrics.get('complexity_distribution', {})
            if complexity_dist:
                lines.append("复杂度分布:")
                for level, count in complexity_dist.items():
                    lines.append(f"  - {level}: {count} 个文件")

    def _format_integration_component(self, component_result: Dict, lines: List[str]):
        """格式化集成测试组件结果"""
        test_suites = component_result.get('test_suites', {})
        performance = component_result.get('performance_metrics', {})

        if test_suites:
            lines.append("测试套件:")
            for suite_name, suite_result in test_suites.items():
                suite_status = suite_result.get('status', 'UNKNOWN')
                tests = suite_result.get('tests', [])
                passed_tests = len([t for t in tests if t.get('status') == 'PASS'])
                total_tests = len(tests)
                lines.append(f"  - {suite_name}: {self._format_status(suite_status)} ({passed_tests}/{total_tests})")

        if performance:
            lines.append("性能指标:")
            for metric, value in performance.items():
                lines.append(f"  - {metric}: {value}")

    def _format_quick_component(self, component_result: Dict, lines: List[str]):
        """格式化快速验证组件结果"""
        checks = component_result.get('checks', [])
        if checks:
            lines.append("快速检查:")
            for check in checks:
                lines.append(f"  {check}")

    def _generate_json_report(self, result: VerificationResult, output_file: Optional[str] = None) -> str:
        """生成JSON报告"""
        # 转换为可序列化的格式
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
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007acc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007acc;
            margin: 0;
            font-size: 2.5em;
        }}
        .meta-info {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            margin: 5px;
        }}
        .status-pass {{ background-color: #28a745; }}
        .status-fail {{ background-color: #dc3545; }}
        .status-warning {{ background-color: #ffc107; color: #333; }}
        .status-unknown {{ background-color: #6c757d; }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
        }}
        .component {{
            background: #f8f9fa;
            margin: 15px 0;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #007acc;
        }}
        .issue {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            margin: 5px 0;
            border-radius: 3px;
        }}
        .issue-high {{ border-left-color: #dc3545; background-color: #f8d7da; }}
        .issue-medium {{ border-left-color: #ffc107; background-color: #fff3cd; }}
        .issue-low {{ border-left-color: #17a2b8; background-color: #d1ecf1; }}
        .fix {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 10px;
            margin: 5px 0;
            border-radius: 3px;
        }}
        .recommendation {{
            background: #e2e3e5;
            padding: 10px;
            margin: 5px 0;
            border-radius: 3px;
            border-left: 4px solid #6f42c1;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border: 1px solid #dee2e6;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007acc;
        }}
        .metric-label {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 SPDX Scanner 验证报告</h1>
            <p>自动化验证工具生成的详细报告</p>
        </div>

        <div class="meta-info">
            <p><strong>生成时间:</strong> {result.timestamp}</p>
            <p><strong>验证模式:</strong> {result.mode}</p>
            <p><strong>验证耗时:</strong> {result.duration:.2f}秒</p>
            <p><strong>整体状态:</strong> <span class="status status-{result.overall_status.lower()}">{self._format_status(result.overall_status)}</span></p>
        </div>

        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{len(result.issues_found)}</div>
                <div class="metric-label">发现问题</div>
            </div>
            <div class="metric">
                <div class="metric-value">{len(result.auto_fixes_applied)}</div>
                <div class="metric-label">自动修复</div>
            </div>
            <div class="metric">
                <div class="metric-value">{len(result.components)}</div>
                <div class="metric-label">验证组件</div>
            </div>
        </div>
"""

        # 添加组件详细结果
        for component_name, component_result in result.components.items():
            html_content += f"""
        <div class="section">
            <h2>📋 {component_name.upper()} 组件验证</h2>
            <div class="component">
"""

            if isinstance(component_result, dict):
                status = component_result.get('status', 'UNKNOWN')
                html_content += f"""
                <p><strong>状态:</strong> <span class="status status-{status.lower()}">{self._format_status(status)}</span></p>
"""
                # 组件特定信息
                if component_name == 'spdx':
                    accuracy = component_result.get('accuracy', 0.0)
                    test_coverage = component_result.get('test_coverage', 0.0)
                    html_content += f"""
                <p><strong>准确率:</strong> {accuracy:.2%}</p>
                <p><strong>测试覆盖率:</strong> {test_coverage:.2%}</p>
"""
                elif component_name == 'quality':
                    score = component_result.get('score', 0.0)
                    files_analyzed = component_result.get('files_analyzed', 0)
                    html_content += f"""
                <p><strong>质量评分:</strong> {score:.1f}/10.0</p>
                <p><strong>分析文件:</strong> {files_analyzed} 个</p>
"""
            html_content += "            </div>\n        </div>\n"

        # 添加问题详情
        if result.issues_found:
            html_content += """
        <div class="section">
            <h2>⚠️ 发现的问题</h2>
"""
            for i, issue in enumerate(result.issues_found, 1):
                severity = issue.get('severity', 'UNKNOWN').lower()
                issue_type = issue.get('type', 'unknown')
                message = issue.get('message', '无详细信息')
                html_content += f"""
            <div class="issue issue-{severity}">
                <strong>{i}. [{issue.get('severity', 'UNKNOWN')}] {issue_type}</strong><br>
                {message}
            </div>
"""
            html_content += "        </div>\n"

        # 添加自动修复详情
        if result.auto_fixes_applied:
            html_content += """
        <div class="section">
            <h2>🔧 自动修复</h2>
"""
            for i, fix in enumerate(result.auto_fixes_applied, 1):
                fix_type = fix.get('type', 'unknown')
                description = fix.get('description', '无描述')
                html_content += f"""
            <div class="fix">
                <strong>{i}. {fix_type}</strong><br>
                {description}
            </div>
"""
            html_content += "        </div>\n"

        # 添加改进建议
        if result.recommendations:
            html_content += """
        <div class="section">
            <h2>💡 改进建议</h2>
"""
            for i, recommendation in enumerate(result.recommendations, 1):
                html_content += f"""
            <div class="recommendation">
                <strong>{i}. {recommendation}</strong>
            </div>
"""
            html_content += "        </div>\n"

        html_content += """
        <div class="footer">
            <p>报告由 SPDX Scanner 自动化验证工具生成</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
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
        lines.append("自动化验证工具生成的详细报告")
        lines.append("")

        # 基本信息
        lines.append("## 📊 验证摘要")
        lines.append("")
        lines.append(f"- **生成时间:** {result.timestamp}")
        lines.append(f"- **验证模式:** {result.mode}")
        lines.append(f"- **验证耗时:** {result.duration:.2f}秒")
        lines.append(f"- **整体状态:** {self._format_status(result.overall_status)}")
        lines.append(f"- **发现问题:** {len(result.issues_found)} 个")
        lines.append(f"- **自动修复:** {len(result.auto_fixes_applied)} 个")
        lines.append(f"- **验证组件:** {len(result.components)} 个")
        lines.append("")

        # 组件详细结果
        for component_name, component_result in result.components.items():
            lines.append(f"## 📋 {component_name.upper()} 组件验证")
            lines.append("")

            if isinstance(component_result, dict):
                status = component_result.get('status', 'UNKNOWN')
                lines.append(f"**状态:** {self._format_status(status)}")
                lines.append("")

                # 组件特定信息
                if component_name == 'spdx':
                    accuracy = component_result.get('accuracy', 0.0)
                    test_coverage = component_result.get('test_coverage', 0.0)
                    lines.append(f"- **准确率:** {accuracy:.2%}")
                    lines.append(f"- **测试覆盖率:** {test_coverage:.2%}")
                elif component_name == 'quality':
                    score = component_result.get('score', 0.0)
                    files_analyzed = component_result.get('files_analyzed', 0)
                    lines.append(f"- **质量评分:** {score:.1f}/10.0")
                    lines.append(f"- **分析文件:** {files_analyzed} 个")

            lines.append("")

        # 问题详情
        if result.issues_found:
            lines.append("## ⚠️ 发现的问题")
            lines.append("")
            for i, issue in enumerate(result.issues_found, 1):
                severity = issue.get('severity', 'UNKNOWN')
                issue_type = issue.get('type', 'unknown')
                message = issue.get('message', '无详细信息')
                lines.append(f"### {i}. [{severity}] {issue_type}")
                lines.append("")
                lines.append(f"{message}")
                lines.append("")

        # 自动修复详情
        if result.auto_fixes_applied:
            lines.append("## 🔧 自动修复")
            lines.append("")
            for i, fix in enumerate(result.auto_fixes_applied, 1):
                fix_type = fix.get('type', 'unknown')
                description = fix.get('description', '无描述')
                lines.append(f"### {i}. {fix_type}")
                lines.append("")
                lines.append(f"{description}")
                lines.append("")

        # 改进建议
        if result.recommendations:
            lines.append("## 💡 改进建议")
            lines.append("")
            for i, recommendation in enumerate(result.recommendations, 1):
                lines.append(f"{i}. {recommendation}")
            lines.append("")

        # 页脚
        lines.append("---")
        lines.append("")
        lines.append("*报告由 SPDX Scanner 自动化验证工具生成*")
        lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        report_content = "\n".join(lines)

        if output_file:
            Path(output_file).write_text(report_content, encoding='utf-8')
            print(f"Markdown报告已保存到: {output_file}")
        else:
            print(report_content)

        return report_content
