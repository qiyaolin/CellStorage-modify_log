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

## 重要发现：Batch处理逻辑

### 关键问题：相同Batch Name但不同Batch ID的记录会被合并吗？

**答案：不会被合并，会产生冲突错误**

系统的Batch处理遵循严格的一致性检查：

1. **优先级顺序**：
   - 如果CSV提供Batch ID → 先通过ID查找
   - 如果ID对应的记录名称与CSV中的Batch Name不匹配 → **报错跳过**
   - 如果没有ID或ID不存在 → 通过Name查找现有Batch
   - 如果Name也不存在 → 创建新Batch

2. **冲突检测机制**：
```python
if batch and batch.name != batch_name:
    skipped_rows.append((i, row, 
        f"Batch ID '{batch_id_from_csv}' exists but has different name '{batch.name}' (expected '{batch_name}')."))
```

3. **数据一致性保护**：
   - Batch ID是唯一标识符，必须与数据库中的名称匹配
   - 不允许ID与Name不一致，防止数据混乱
   - 冲突行会被跳过，不会强制合并

详细分析请参考：`Batch处理逻辑详细分析.md`

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
