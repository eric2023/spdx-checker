# 源文件扩展名可配置功能说明

## 📋 功能概述

SPDX Scanner 现在支持可配置的源文件扩展名检测，默认专注于 C/C++ 和 Go 语言项目。

### 默认支持的文件类型

默认情况下，SPDX Scanner 会扫描以下类型的文件：

- `.h` - C/C++ 头文件
- `.cpp` - C++ 源文件
- `.c` - C 源文件
- `.go` - Go 源文件

---

## 🔧 配置方式

### 1. 命令行配置

#### 使用 `-e` 或 `--extensions` 选项

```bash
# 使用默认扩展名 (.h .cpp .c .go)
spdx-scanner scan /path/to/project

# 自定义扩展名
spdx-scanner scan -e .py -e .js /path/to/project

# 混合使用
spdx-scanner scan -e .c -e .cpp -e .rs /path/to/project

# 不带点也可以（会自动添加）
spdx-scanner scan -e c -e cpp -e h /path/to/project
```

#### 使用 `--include` 选项（仍然支持）

```bash
# 使用传统 include 模式
spdx-scanner scan --include "**/*.py" --include "**/*.js" /path/to/project
```

**注意**: `--include` 会覆盖 `--extensions` 设置

### 2. 配置文件配置

在 `spdx-scanner.config.json` 中配置：

```json
{
  "scanner_settings": {
    "source_file_extensions": [
      ".h",
      ".cpp",
      ".c",
      ".go"
    ]
  }
}
```

#### 示例配置文件

完整示例见: [examples/spdx-scanner.config.json](examples/spdx-scanner.config.json)

```json
{
  "project_name": "My C/C++ Project",
  "scanner_settings": {
    "source_file_extensions": [
      ".c",
      ".cpp",
      ".h",
      ".hpp",
      ".go"
    ],
    "exclude_patterns": [
      "**/build/**",
      "**/dist/**"
    ]
  }
}
```

### 3. Python API 配置

```python
from spdx_scanner.scanner import create_default_scanner

# 使用默认扩展名
scanner = create_default_scanner()

# 使用自定义扩展名
scanner = create_default_scanner(
    source_file_extensions=['.c', '.cpp', '.h', '.go']
)

# 使用扩展名列表（不带点）
scanner = create_default_scanner(
    source_file_extensions=['c', 'cpp', 'h', 'go']
)

# 使用自定义 include 模式（优先级最高）
scanner = create_default_scanner(
    include_patterns=['**/*.py', '**/*.js']
)
```

---

## 📚 使用场景

### 场景 1: C/C++ 项目

```bash
# 只扫描 C/C++ 文件
spdx-scanner scan -e .c -e .cpp -e .h /path/to/cpp/project

# 或者使用配置文件
# 在 spdx-scanner.config.json 中设置:
# "source_file_extensions": [".c", ".cpp", ".h", ".hpp"]
```

### 场景 2: Go 项目

```bash
# 扫描 Go 文件
spdx-scanner scan -e .go /path/to/go/project

# 扫描 Go + C 文件
spdx-scanner scan -e .go -e .c -e .h /path/to/go-project
```

### 场景 3: 多语言项目

```bash
# 扫描 C/C++/Go + Python
spdx-scanner scan -e .c -e .cpp -e .h -e .go -e .py /path/to/project
```

### 场景 4: 仅扫描特定文件类型

```bash
# 只扫描头文件
spdx-scanner scan -e .h /path/to/project

# 只扫描 C++ 源文件
spdx-scanner scan -e .cpp /path/to/project
```

---

## 🎯 优先级规则

配置优先级（从高到低）：

1. **命令行 `--include`** - 最高优先级，完全自定义
2. **命令行 `--extensions`** - 中等优先级，使用扩展名列表
3. **配置文件 `source_file_extensions`** - 较低优先级
4. **默认扩展名** - 最低优先级 (.h .cpp .c .go)

```bash
# 例子
spdx-scanner scan \
  --extensions .py .js \          # 会被忽略
  --include "**/*.c"              # 生效，只扫描 .c 文件
  /path/to/project
```

---

## 📝 扩展名格式说明

### 支持的格式

| 格式 | 示例 | 说明 |
|------|------|------|
| 带点 | `.c`, `.cpp` | 推荐格式 |
| 不带点 | `c`, `cpp` | 自动添加点 |

### 自动转换

系统会自动处理扩展名格式：

```python
# 输入
extensions = ['c', 'cpp', '.h', 'go']

# 自动转换为
['.c', '.cpp', '.h', '.go']

# 生成模式
['**/*.c', '**/*.cpp', '**/*.h', '**/*.go']
```

---

## 🔍 验证功能

### 运行验证测试

```bash
# 运行扩展名配置功能测试
python3 test_extensions_config.py
```

### 预期输出

```
========================================
SPDX Scanner - 源文件扩展名可配置功能测试
========================================

测试1: 默认扫描器扩展名
  ✅ 支持扩展名: .h
  ✅ 支持扩展名: .cpp
  ✅ 支持扩展名: .c
  ✅ 支持扩展名: .go

测试2: 自定义扩展名
  ✅ 包含扩展名: .py
  ...

✅ 所有测试通过！
```

---

## 💡 最佳实践

### 1. 明确指定扩展名

```bash
# 推荐：明确列出需要的扩展名
spdx-scanner scan -e .c -e .cpp -e .h /path/to/project
```

### 2. 使用配置文件

对于长期项目，使用配置文件更方便：

```bash
# 生成默认配置
spdx-scanner create-config

# 编辑配置文件
vim spdx-scanner.config.json

# 使用配置扫描
spdx-scanner scan /path/to/project
```

### 3. 结合排除模式

```bash
# 扫描 C 文件，排除构建目录
spdx-scanner scan -e .c --exclude "**/build/**" /path/to/project
```

### 4. 预览扫描文件

```bash
# 预览哪些文件会被扫描（干运行模式）
spdx-scanner scan --dry-run -e .c /path/to/project
```

---

## 📊 性能优化

### 减少扫描范围

指定精确的扩展名可以提高扫描速度：

```bash
# 只扫描 C 文件（最快）
spdx-scanner scan -e .c /path/to/project

# 扫描多种类型（较慢）
spdx-scanner scan -e .c -e .cpp -e .go -e .rs /path/to/project
```

### 排除无关文件

```bash
# 排除构建产物
spdx-scanner scan -e .c --exclude "**/build/**" /path/to/project
```

---

## 🔧 故障排除

### 问题 1: 扩展名不生效

**原因**: 可能使用了 `--include` 选项，覆盖了 `--extensions`

**解决**: 不使用 `--include`，或移除 `--include` 参数

```bash
# 错误示例
spdx-scanner scan -e .c --include "**/*.py" /path/to/project
# 结果：只扫描 .py 文件（被 --include 覆盖）

# 正确示例
spdx-scanner scan -e .c /path/to/project
```

### 问题 2: 扩展名格式错误

**原因**: 扩展名可能缺少点号

**解决**: 系统会自动处理，但建议始终使用带点的格式

```bash
# 推荐
spdx-scanner scan -e .c -e .cpp /path/to/project

# 也可以（自动转换）
spdx-scanner scan -e c -e cpp /path/to/project
```

### 问题 3: 配置文件不生效

**检查步骤**:
1. 确认配置文件在正确位置
2. 验证 JSON 格式正确
3. 检查 `source_file_extensions` 字段存在

```bash
# 验证配置
python3 -c "from spdx_scanner.config import ConfigManager; \
config = ConfigManager().load_config(); \
print(config.scanner_settings.source_file_extensions)"
```

---

## 📈 迁移指南

### 从旧版本迁移

旧版本使用 `include_patterns`，新版本推荐使用 `source_file_extensions`：

**旧配置**:
```json
{
  "scanner_settings": {
    "include_patterns": [
      "**/*.c",
      "**/*.cpp",
      "**/*.h"
    ]
  }
}
```

**新配置**:
```json
{
  "scanner_settings": {
    "source_file_extensions": [
      ".c",
      ".cpp",
      ".h"
    ]
  }
}
```

**兼容性**: 旧配置仍然有效，但建议迁移到新格式

---

## ✅ 功能特性总结

- ✅ 默认支持 .h .cpp .c .go 文件
- ✅ 可自定义源文件扩展名
- ✅ 支持命令行和配置文件配置
- ✅ 自动处理带点/不带点格式
- ✅ 完整配置序列化支持
- ✅ 与现有功能完全兼容
- ✅ 向后兼容旧配置格式

---

## 📞 支持与反馈

如有问题或建议，请：

1. 运行测试脚本验证功能: `python3 test_extensions_config.py`
2. 查看完整验证报告: `VERIFICATION_REPORT.md`
3. 创建 Issue 描述问题

---

**文档版本**: v1.0
**最后更新**: 2025年10月28日
**适用版本**: SPDX Scanner v0.1.0+
