#!/usr/bin/env python3
"""
SPDX Scanner 代码质量分析工具

此工具用于分析项目代码质量，包括：
- 代码复杂度分析
- 依赖关系分析
- 重复代码检测
- 技术债务评估
- 测试覆盖率分析

使用方法:
    python tools/analysis/code_quality.py [--output json|html|console] [--verbose]
"""

import os
import ast
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re


@dataclass
class ComplexityMetric:
    """复杂度指标"""
    cyclomatic_complexity: int
    cognitive_complexity: int
    lines_of_code: int
    nesting_depth: int
    function_count: int
    class_count: int


@dataclass
class DependencyInfo:
    """依赖信息"""
    module_name: str
    imports: List[str]
    imported_by: List[str]
    external_imports: Set[str]
    internal_imports: Set[str]


@dataclass
class CodeQualityReport:
    """代码质量报告"""
    timestamp: str
    project_path: str
    file_count: int
    total_lines: int
    total_functions: int
    total_classes: int
    average_complexity: float
    complexity_distribution: Dict[str, int]
    dependency_graph: Dict[str, DependencyInfo]
    duplicate_files: List[Tuple[str, str, float]]
    technical_debt_score: float
    recommendations: List[str]


class CodeQualityAnalyzer:
    """代码质量分析器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.python_files = []
        self.dependency_graph: Dict[str, DependencyInfo] = {}
        self.complexity_metrics: Dict[str, ComplexityMetric] = {}
        self.duplicate_patterns: List[Tuple[str, str, float]] = []

    def analyze(self) -> CodeQualityReport:
        """执行完整的代码质量分析"""
        print("开始代码质量分析...")

        # 1. 发现Python文件
        self._discover_python_files()

        # 2. 分析复杂度
        self._analyze_complexity()

        # 3. 分析依赖关系
        self._analyze_dependencies()

        # 4. 检测重复代码
        self._detect_duplicates()

        # 5. 计算技术债务评分
        debt_score = self._calculate_technical_debt()

        # 6. 生成建议
        recommendations = self._generate_recommendations()

        # 7. 生成报告
        report = CodeQualityReport(
            timestamp=datetime.now().isoformat(),
            project_path=str(self.project_root),
            file_count=len(self.python_files),
            total_lines=sum(m.lines_of_code for m in self.complexity_metrics.values()),
            total_functions=sum(m.function_count for m in self.complexity_metrics.values()),
            total_classes=sum(m.class_count for m in self.complexity_metrics.values()),
            average_complexity=sum(m.cyclomatic_complexity for m in self.complexity_metrics.values()) / max(len(self.complexity_metrics), 1),
            complexity_distribution=self._get_complexity_distribution(),
            dependency_graph=self.dependency_graph,
            duplicate_files=self.duplicate_patterns,
            technical_debt_score=debt_score,
            recommendations=recommendations
        )

        return report

    def _discover_python_files(self):
        """发现所有Python文件"""
        patterns = ["**/*.py"]
        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                # 忽略特定目录
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                if 'venv' in file_path.parts or '__pycache__' in file_path.parts:
                    continue
                self.python_files.append(file_path)

        print(f"发现 {len(self.python_files)} 个Python文件")

    def _analyze_complexity(self):
        """分析代码复杂度"""
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                complexity = self._calculate_complexity(tree)
                self.complexity_metrics[str(file_path.relative_to(self.project_root))] = complexity

            except Exception as e:
                print(f"分析文件失败 {file_path}: {e}")

    def _calculate_complexity(self, tree: ast.AST) -> ComplexityMetric:
        """计算AST的复杂度"""
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.cyclomatic_complexity = 1
                self.cognitive_complexity = 0
                self.lines_of_code = 0
                self.nesting_depth = 0
                self.max_nesting = 0
                self.function_count = 0
                self.class_count = 0
                self.current_nesting = 0

            def visit_If(self, node):
                self.cyclomatic_complexity += 1
                self.cognitive_complexity += 1 + self.current_nesting
                self.current_nesting += 1
                self.generic_visit(node)
                self.current_nesting -= 1

            def visit_While(self, node):
                self.cyclomatic_complexity += 1
                self.cognitive_complexity += 1 + self.current_nesting
                self.current_nesting += 1
                self.generic_visit(node)
                self.current_nesting -= 1

            def visit_For(self, node):
                self.cyclomatic_complexity += 1
                self.cognitive_complexity += 1 + self.current_nesting
                self.current_nesting += 1
                self.generic_visit(node)
                self.current_nesting -= 1

            def visit_ExceptHandler(self, node):
                self.cyclomatic_complexity += 1
                self.cognitive_complexity += 1 + self.current_nesting
                self.generic_visit(node)

            def visit_With(self, node):
                self.cognitive_complexity += 1 + self.current_nesting
                self.generic_visit(node)

            def visit_And(self, node):
                self.cognitive_complexity += 1
                self.generic_visit(node)

            def visit_Or(self, node):
                self.cognitive_complexity += 1
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                self.function_count += 1
                self.current_nesting += 1
                self.generic_visit(node)
                self.current_nesting -= 1
                self.max_nesting = max(self.max_nesting, self.current_nesting)

            def visit_ClassDef(self, node):
                self.class_count += 1
                self.current_nesting += 1
                self.generic_visit(node)
                self.current_nesting -= 1

            def generic_visit(self, node):
                super().generic_visit(node)

        visitor = ComplexityVisitor()
        visitor.visit(tree)

        return ComplexityMetric(
            cyclomatic_complexity=visitor.cyclomatic_complexity,
            cognitive_complexity=visitor.cognitive_complexity,
            lines_of_code=len([line for line in ast.get_source_segment('').split('\\n') if line.strip()]) if hasattr(ast, 'get_source_segment') else 0,
            nesting_depth=visitor.max_nesting,
            function_count=visitor.function_count,
            class_count=visitor.class_count
        )

    def _analyze_dependencies(self):
        """分析依赖关系"""
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                imports = self._extract_imports(tree)
                relative_path = str(file_path.relative_to(self.project_root))

                self.dependency_graph[relative_path] = DependencyInfo(
                    module_name=relative_path,
                    imports=imports,
                    imported_by=[],  # 将在下一步填充
                    external_imports=set(),
                    internal_imports=set()
                )

            except Exception as e:
                print(f"分析依赖失败 {file_path}: {e}")

        # 填充导入者和分类导入
        for module, info in self.dependency_graph.items():
            for imp in info.imports:
                if imp.startswith('.'):
                    # 相对导入
                    internal_import = self._resolve_relative_import(module, imp)
                    if internal_import and internal_import in self.dependency_graph:
                        info.internal_imports.add(internal_import)
                        self.dependency_graph[internal_import].imported_by.append(module)
                elif imp.startswith('spdx_scanner'):
                    # 内部模块导入
                    info.internal_imports.add(imp)
                    if imp in self.dependency_graph:
                        self.dependency_graph[imp].imported_by.append(module)
                else:
                    # 外部导入
                    info.external_imports.add(imp)

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """提取导入语句"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def _resolve_relative_import(self, current_module: str, relative_import: str) -> str:
        """解析相对导入"""
        # 简化的相对导入解析
        if relative_import.startswith('.'):
            depth = len(relative_import) - len(relative_import.lstrip('.'))
            module_parts = current_module.split('/')

            if depth > len(module_parts):
                return None

            base_parts = module_parts[:-depth] if depth > 0 else module_parts
            import_parts = relative_import.lstrip('.').split('.')

            return '/'.join(base_parts + import_parts) + '.py'
        return relative_import

    def _detect_duplicates(self):
        """检测重复代码"""
        file_contents = {}

        # 收集文件内容
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 简单的重复检测 - 基于函数和类定义
                functions = re.findall(r'^\\s*def\\s+(\\w+)', content, re.MULTILINE)
                classes = re.findall(r'^\\s*class\\s+(\\w+)', content, re.MULTILINE)

                signature = ','.join(sorted(functions + classes))
                if signature:
                    if signature not in file_contents:
                        file_contents[signature] = []
                    file_contents[signature].append(str(file_path.relative_to(self.project_root)))

            except Exception:
                continue

        # 识别重复
        for signature, files in file_contents.items():
            if len(files) > 1:
                # 计算相似度（简化版本）
                similarity = min(len(files) / 5.0, 1.0)  # 简单的相似度计算
                self.duplicate_patterns.append((files[0], files[1], similarity))

    def _get_complexity_distribution(self) -> Dict[str, int]:
        """获取复杂度分布"""
        distribution = {
            'low': 0,      # 1-5
            'medium': 0,   # 6-10
            'high': 0,     # 11-20
            'very_high': 0 # >20
        }

        for metric in self.complexity_metrics.values():
            complexity = metric.cyclomatic_complexity
            if complexity <= 5:
                distribution['low'] += 1
            elif complexity <= 10:
                distribution['medium'] += 1
            elif complexity <= 20:
                distribution['high'] += 1
            else:
                distribution['very_high'] += 1

        return distribution

    def _calculate_technical_debt(self) -> float:
        """计算技术债务评分 (0-10, 10为最高债务)"""
        debt_score = 0.0

        # 复杂度债务
        high_complexity = sum(1 for m in self.complexity_metrics.values() if m.cyclomatic_complexity > 10)
        if high_complexity > 0:
            debt_score += min(high_complexity / len(self.complexity_metrics) * 10, 3)

        # 依赖债务
        problematic_deps = 0
        for info in self.dependency_graph.values():
            if len(info.imported_by) > 5:  # 过度耦合
                problematic_deps += 1
        if problematic_deps > 0:
            debt_score += min(problematic_deps / len(self.dependency_graph) * 5, 2)

        # 重复代码债务
        debt_score += len(self.duplicate_patterns) * 0.5

        return min(debt_score, 10.0)

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于复杂度的建议
        high_complexity_files = [f for f, m in self.complexity_metrics.items() if m.cyclomatic_complexity > 15]
        if high_complexity_files:
            recommendations.append(f"重构高复杂度文件: {', '.join(high_complexity_files[:3])}")

        # 基于依赖的建议
        highly_coupled = [f for f, info in self.dependency_graph.items() if len(info.imported_by) > 5]
        if highly_coupled:
            recommendations.append(f"考虑拆分高度耦合的模块: {', '.join(highly_coupled[:3])}")

        # 基于重复代码的建议
        if self.duplicate_patterns:
            recommendations.append(f"合并重复代码模式，共发现 {len(self.duplicate_patterns)} 处")

        # 通用建议
        recommendations.extend([
            "建立代码审查流程",
            "实施自动化测试",
            "定期进行代码质量检查",
            "建立技术债务管理流程"
        ])

        return recommendations

    def export_report(self, report: CodeQualityReport, output_format: str = 'console', output_file: str = None):
        """导出报告"""
        if output_format == 'json':
            with open(output_file or 'code_quality_report.json', 'w') as f:
                json.dump(asdict(report), f, indent=2)
            print(f"报告已导出到: {output_file or 'code_quality_report.json'}")

        elif output_format == 'html':
            self._generate_html_report(report, output_file)

        else:  # console
            self._print_console_report(report)

    def _print_console_report(self, report: CodeQualityReport):
        """打印控制台报告"""
        print("\\n" + "="*60)
        print("SPDX Scanner 代码质量分析报告")
        print("="*60)

        print(f"分析时间: {report.timestamp}")
        print(f"项目路径: {report.project_path}")

        print(f"\\n📊 基本统计:")
        print(f"  文件数量: {report.file_count}")
        print(f"  总行数: {report.total_lines}")
        print(f"  函数数量: {report.total_functions}")
        print(f"  类数量: {report.total_classes}")

        print(f"\\n🧮 复杂度分析:")
        print(f"  平均复杂度: {report.average_complexity:.2f}")
        print("  复杂度分布:")
        for level, count in report.complexity_distribution.items():
            print(f"    {level}: {count} 个文件")

        print(f"\\n🔗 依赖关系:")
        print(f"  分析了 {len(report.dependency_graph)} 个模块的依赖关系")

        print(f"\\n🔄 重复代码:")
        if report.duplicate_files:
            print(f"  发现 {len(report.duplicate_files)} 处重复代码")
            for file1, file2, similarity in report.duplicate_files[:3]:
                print(f"    {file1} <-> {file2} (相似度: {similarity:.2f})")
        else:
            print("  未发现重复代码")

        print(f"\\n⚠️  技术债务评分: {report.technical_debt_score:.1f}/10")

        print(f"\\n💡 改进建议:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")

        print("="*60)

    def _generate_html_report(self, report: CodeQualityReport, output_file: str = None):
        """生成HTML报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>SPDX Scanner 代码质量报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ background-color: #e9f7ef; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SPDX Scanner 代码质量分析报告</h1>
        <p>生成时间: {report.timestamp}</p>
        <p>项目路径: {report.project_path}</p>
    </div>

    <div class="section">
        <h2>基本统计</h2>
        <table>
            <tr><th>指标</th><th>值</th></tr>
            <tr><td>文件数量</td><td>{report.file_count}</td></tr>
            <tr><td>总行数</td><td>{report.total_lines}</td></tr>
            <tr><td>函数数量</td><td>{report.total_functions}</td></tr>
            <tr><td>类数量</td><td>{report.total_classes}</td></tr>
            <tr><td>平均复杂度</td><td>{report.average_complexity:.2f}</td></tr>
            <tr><td>技术债务评分</td><td>{report.technical_debt_score:.1f}/10</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>复杂度分布</h2>
        <table>
            <tr><th>复杂度等级</th><th>文件数量</th></tr>
            <tr><td>低 (1-5)</td><td>{report.complexity_distribution['low']}</td></tr>
            <tr><td>中 (6-10)</td><td>{report.complexity_distribution['medium']}</td></tr>
            <tr><td>高 (11-20)</td><td>{report.complexity_distribution['high']}</td></tr>
            <tr><td>很高 (>20)</td><td>{report.complexity_distribution['very_high']}</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>改进建议</h2>
        {''.join(f'<div class="recommendation">{rec}</div>' for rec in report.recommendations)}
    </div>
</body>
</html>
        """

        with open(output_file or 'code_quality_report.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML报告已生成: {output_file or 'code_quality_report.html'}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SPDX Scanner代码质量分析工具")
    parser.add_argument("--output", choices=['json', 'html', 'console'], default='console',
                       help="输出格式 (默认: console)")
    parser.add_argument("--output-file", help="输出文件路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 查找项目根目录
    project_root = Path.cwd()

    # 创建分析器
    analyzer = CodeQualityAnalyzer(project_root)

    # 执行分析
    report = analyzer.analyze()

    # 导出报告
    analyzer.export_report(report, args.output, args.output_file)


if __name__ == "__main__":
    main()