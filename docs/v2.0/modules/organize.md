# Organize Module 设计

## 📋 模块概述

Organize Module 提供智能音乐文件整理功能，包括自动归类、重命名、元数据处理和重复检测。

## 🎯 功能需求

1. **整理规则**: 用户自定义整理规则
2. **自动执行**: 定时或手动触发整理
3. **元数据处理**: 封面、歌词批量处理
4. **重复检测**: 识别并处理重复文件

## 🏗️ 核心组件

### Rule Engine
```python
class OrganizeRule:
    id: int
    name: str
    rule_type: str      # "move", "rename", "classify"
    condition: str      # 匹配条件 (JSON)
    action: str         # 执行动作 (JSON)
    enabled: bool
    priority: int       # 执行优先级
```

### Rule Types

#### Move Rule
```json
{
  "type": "move",
  "source": "/music/inbox",
  "destination": "/music/library/{artist}/{album}",
  "conflict": "rename"  // rename, skip, overwrite
}
```

#### Rename Rule
```json
{
  "type": "rename",
  "pattern": "{artist} - {title}",
  "case": "title"  // title, upper, lower
}
```

#### Classify Rule
```json
{
  "type": "classify",
  "conditions": {
    "genre": "Jazz"
  },
  "target": "/music/jazz"
}
```

### Processor

#### MetadataProcessor
- 读取/写入 ID3 标签
- 规范化元数据格式
- 自动补全缺失信息

#### CoverProcessor
- 提取/嵌入封面
- 缩放/裁剪封面尺寸
- 批量处理

#### LyricsProcessor
- 嵌入 LRC 歌词
- 下载自动歌词 (可选)

### DuplicateDetector
```python
class DuplicateDetector:
    # 检测策略
    - hash: 文件哈希比较
    - metadata: 元数据相似度
    - acoustic: 音频指纹 (高级)
    
    # 处理方式
    - keep_newest: 保留最新
    - keep_best: 保留质量最好
    - manual: 手动选择
```

## 📋 执行流程

1. 扫描源目录
2. 匹配规则条件
3. 执行规则动作
4. 记录执行日志
5. 生成执行报告

## ⚠️ 安全机制

- **Dry Run**: 预览模式，不实际修改
- **备份**: 执行前自动备份
- **回滚**: 支持撤销操作
- **权限检查**: 检查文件写入权限