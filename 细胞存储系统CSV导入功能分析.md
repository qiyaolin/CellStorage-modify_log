# 细胞存储系统CSV导入功能分析

## Core Features

- CSV文件上传与验证

- 数据解析与字段映射

- 批量数据处理

- 重复检测与校验

- 错误处理与日志

- 导入进度跟踪

## Tech Stack

{
  "backend": "Python Flask + SQLAlchemy ORM",
  "data_processing": "Python内置csv模块 + 自定义验证",
  "file_handling": "Flask-WTF MultipleFileField",
  "async_processing": "同步处理（无异步）"
}

## Design

基于现有代码的详细工作流程分析，包含6个主要阶段：文件上传、文件验证、CSV结构验证、数据行处理、字段验证和批量数据处理。系统支持两种CSV格式（管理员和用户格式），具备完整的错误处理和反馈机制。

## ⚠️ 严重问题发现：Batch处理逻辑缺陷

### 关键问题：相同Batch Name但不同Batch ID的记录会被合并吗？

**答案：会被错误合并！这是一个严重的数据完整性缺陷**

### 问题根源
现有系统的逻辑缺陷：

```python
# 1. 先通过Batch ID查找
if batch_id_from_csv:
    batch = VialBatch.query.get(int(batch_id_from_csv))
    if batch and batch.name != batch_name:
        # 只有ID存在但名称不匹配时才报错
        skipped_rows.append(...)

# 2. 关键缺陷：如果通过ID没找到，直接通过名称查找
if not batch:
    batch = VialBatch.query.filter_by(name=batch_name).first()
    # 这里完全忽略了CSV中指定的Batch ID！
```

### 错误场景示例
假设数据库中存在：Batch ID=100, Name="实验批次A"

导入CSV：
```csv
Vial ID,Batch ID,Batch Name,Vial Tag,Cell Line,...
,300,实验批次A,V001,HeLa,...
```

**错误处理流程：**
1. 通过ID=300查找 → 没找到
2. 通过name="实验批次A"查找 → 找到ID=100的记录
3. **错误**：将记录分配给Batch ID=100，而不是创建新的ID=300批次

### 数据完整性风险
- **批次混淆**：不同实验批次被错误合并
- **ID冲突隐患**：CSV指定的Batch ID被完全忽略
- **审计追踪问题**：无法准确追踪样本原始批次归属
- **实验可追溯性丢失**：影响质量控制和合规性

### 修复建议
Batch ID应该是唯一标识符，即使Batch Name相同，不同Batch ID也必须视为不同批次。需要修改逻辑：
- 当CSV指定的Batch ID不存在时，检查是否有同名的不同ID批次
- 如果存在同名不同ID的批次，应该报错而不是合并
- 只有在确认无冲突时才创建新批次

详细分析请参考：`Batch处理逻辑问题分析-修正版.md`

## Plan

Note: 

- [ ] is holding
- [/] is doing
- [X] is done

---

[X] 分析CSV导入的完整工作流程

[X] 分析文件上传和验证机制

[X] 分析数据解析和字段映射逻辑

[X] 分析数据验证和重复检测机制

[X] 分析批量数据处理和事务管理

[X] 分析错误处理和日志记录系统

[X] 分析辅助工具和验证器

[X] 总结系统限制和优化建议

[X] 深入分析Batch处理逻辑和冲突检测机制
