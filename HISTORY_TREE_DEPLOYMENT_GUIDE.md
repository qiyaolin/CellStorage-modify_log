# History Tree 功能修复 - 部署指南

## 📋 修改概览

本次修复解决了 History Tree 功能的核心问题：**自动将用户在创建 CryoVial 时输入的 `parental_cell_line` 字符串转换为正式的 `BatchLineage` 数据库关系**。

### 修改的文件

1. **`app/cell_storage/models.py`**
   - 添加了 `VialBatch.auto_create_lineage_from_parental_name()` 静态方法
   - 用于自动从字符串创建 BatchLineage 关系

2. **`app/cell_storage/main/routes.py`**
   - 在 3 个关键位置调用自动创建函数：
     - 批量创建 vial（`add_cryovial` 函数，约 1120 行）
     - 单个创建 vial（`add_vial_at_position` 函数，约 876 行）
     - 编辑 vial（`edit_cryovial` 函数，约 783 行）

3. **`app/admin/routes.py`**
   - 添加了 `/backfill-lineage` 页面路由
   - 添加了 `/api/backfill-lineage` API 端点

4. **`app/templates/admin/backfill_lineage.html`** (新文件)
   - 创建了数据回填的 Web 界面

### 数据库迁移

**无需手动执行** - `batch_lineage` 表已在 `app/__init__.py:64-90` 中自动创建，会在应用启动时自动运行。

## 🚀 部署流程

### 步骤 1：验证代码变更

```bash
# 查看修改的文件
git status

# 应该显示以下文件已修改/新增：
# modified:   app/cell_storage/models.py
# modified:   app/cell_storage/main/routes.py
# modified:   app/admin/routes.py
# new file:   app/templates/admin/backfill_lineage.html
# new file:   HISTORY_TREE_DEPLOYMENT_GUIDE.md
```

### 步骤 2：提交代码

```bash
# 添加所有修改
git add app/cell_storage/models.py
git add app/cell_storage/main/routes.py
git add app/admin/routes.py
git add app/templates/admin/backfill_lineage.html
git add HISTORY_TREE_DEPLOYMENT_GUIDE.md

# 创建提交
git commit -m "Fix History Tree: Auto-create BatchLineage from parental_cell_line

- Add auto_create_lineage_from_parental_name() to VialBatch model
- Call auto-create in 3 vial creation/edit locations
- Add admin backfill tool at /system-admin/backfill-lineage
- Enable automatic lineage tracking for new vials
- Support backfilling existing historical data

Resolves: History Tree visualization now displays batch relationships"
```

### 步骤 3：部署到 Google Cloud

```bash
# 确认项目配置
gcloud config get-value project
# 应该显示：ambient-decoder-467517-h8

# 部署应用
gcloud app deploy

# 等待部署完成（约 3-5 分钟）
# 输出示例：
# Updating service [default]...done.
# Setting traffic split for service [default]...done.
# Deployed service [default] to [https://ambient-decoder-467517-h8.nn.r.appspot.com]
```

### 步骤 4：验证部署

```bash
# 查看应用日志
gcloud app logs tail -s default

# 查找迁移成功的日志：
# 应该看到类似的信息：
# "batch_lineage table created successfully" 或 "table already exists"
```

## 🔧 回填现有数据

部署完成后，需要将现有的 `parental_cell_line` 字符串数据转换为 BatchLineage 关系。

### 方法 1：使用 Web 界面（推荐）

1. **访问回填页面**
   ```
   https://ambient-decoder-467517-h8.nn.r.appspot.com/system-admin/backfill-lineage
   ```

2. **查看统计信息**
   - 页面会显示：
     - 总批次数量
     - 有 parental_cell_line 数据的批次数量
     - 现有的 lineage 记录数量
     - 前 10 个待处理批次的示例

3. **预览更改（Dry Run）**
   - 点击 **"Preview Changes (Dry Run)"** 按钮
   - 查看会创建哪些关系，但不实际修改数据库
   - 检查 skipped 和 error 的原因

4. **执行回填**
   - 点击 **"Execute Backfill"** 按钮
   - 确认操作
   - 等待处理完成（通常几秒到几分钟）
   - 查看结果报告

5. **强制覆盖（可选）**
   - 如果需要更新已存在的关系，点击 **"Force Overwrite"**
   - ⚠️ 警告：这会覆盖现有的 lineage 记录

### 方法 2：使用 API（高级用户）

```bash
# 使用 curl 或 Postman 调用 API

# 预览模式（不修改数据）
curl -X POST \
  https://ambient-decoder-467517-h8.nn.r.appspot.com/system-admin/api/backfill-lineage \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{"dry_run": true}'

# 执行回填
curl -X POST \
  https://ambient-decoder-467517-h8.nn.r.appspot.com/system-admin/api/backfill-lineage \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{"dry_run": false}'

# 强制覆盖
curl -X POST \
  https://ambient-decoder-467517-h8.nn.r.appspot.com/system-admin/api/backfill-lineage \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{"dry_run": false, "force": true}'
```

## ✅ 功能验证

### 1. 测试自动创建功能

1. **访问添加 Vial 页面**
   ```
   https://ambient-decoder-467517-h8.nn.r.appspot.com/cell-storage/cryovial/add
   ```

2. **创建新 vial**
   - 填写表单，特别是 **"Parental Cell Line"** 字段
   - 输入一个已存在的批次名称（例如："Batch_001"）
   - 提交表单

3. **检查日志**
   ```bash
   gcloud app logs tail -s default | grep "Auto-lineage"
   ```
   - 应该看到：`Auto-lineage: Created relationship X -> Y`

### 2. 测试 History Tree 可视化

1. **访问 History Tree 页面**
   ```
   https://ambient-decoder-467517-h8.nn.r.appspot.com/cell-storage/history-tree
   ```

2. **搜索批次**
   - 在搜索框中输入批次名称
   - 或从"Quick Picks"列表中选择一个批次

3. **查看树形图**
   - 应该能看到父子关系的树形可视化
   - 统计信息应该显示正确的数量
   - 可以切换视图（Full / Ancestors / Descendants）

4. **测试交互**
   - 点击节点应该跳转到该批次的 History Tree
   - 导出 SVG 功能应该正常工作

### 3. 验证数据完整性

```sql
-- 连接到生产数据库并运行以下查询

-- 检查 BatchLineage 表
SELECT COUNT(*) FROM batch_lineage;
-- 应该返回一个正数（创建的关系数量）

-- 查看示例关系
SELECT
    p.name as parent_name,
    c.name as child_name,
    bl.relationship_type,
    bl.notes,
    bl.created_at
FROM batch_lineage bl
JOIN vial_batches p ON p.id = bl.parent_batch_id
JOIN vial_batches c ON c.id = bl.child_batch_id
LIMIT 10;

-- 检查是否有自引用（应该返回 0）
SELECT COUNT(*) FROM batch_lineage
WHERE parent_batch_id = child_batch_id;
```

## 📊 预期效果

### 修复前

- ❌ History Tree 显示空白或不完整
- ❌ 统计数字显示为 0
- ❌ 无法可视化批次谱系
- ❌ `parental_cell_line` 字段只是字符串，没有数据库关系

### 修复后

- ✅ 新创建的 vial 自动建立 BatchLineage 关系
- ✅ History Tree 正确显示父子关系
- ✅ 统计数字准确反映祖先/后代数量
- ✅ 可以导出和分享谱系树
- ✅ 历史数据可以通过回填工具转换

## 🆘 故障排除

### 问题 1：History Tree 仍然显示空

**可能原因**：
1. 回填操作尚未执行
2. 父批次名称不匹配

**解决方案**：
```bash
# 1. 检查 batch_lineage 表
gcloud app logs tail -s default | grep "batch_lineage"

# 2. 运行回填操作
# 访问 /system-admin/backfill-lineage

# 3. 检查日志中的 Auto-lineage 消息
gcloud app logs tail -s default | grep "Auto-lineage"
```

### 问题 2：回填操作失败

**可能原因**：
- 数据库连接问题
- 权限不足
- 父批次名称不存在

**解决方案**：
1. 查看详细错误信息（在回填页面的 "Results" 部分）
2. 检查应用日志：
   ```bash
   gcloud app logs tail -s default --level=warning
   ```
3. 验证数据完整性：
   ```sql
   -- 查找无法匹配的 parental_cell_line
   SELECT DISTINCT cv.parental_cell_line
   FROM cryovials cv
   WHERE cv.parental_cell_line IS NOT NULL
     AND cv.parental_cell_line != ''
     AND NOT EXISTS (
       SELECT 1 FROM vial_batches vb
       WHERE vb.name = cv.parental_cell_line
     );
   ```

### 问题 3：自动创建不工作

**诊断**：
```bash
# 检查是否调用了自动创建函数
gcloud app logs tail -s default | grep "Auto-lineage"

# 如果没有日志，检查代码是否正确部署
gcloud app versions list
```

**解决方案**：
1. 确认代码已正确部署到 Google Cloud
2. 检查 `VialBatch` 模型是否有 `auto_create_lineage_from_parental_name` 方法
3. 验证 routes.py 中的调用代码是否存在

### 问题 4：权限错误

**错误信息**：`403 Forbidden` 或 `Permission denied`

**解决方案**：
1. 确保使用 admin 账号登录
2. 检查用户权限：
   ```sql
   SELECT * FROM users WHERE username = 'YOUR_USERNAME';
   SELECT role FROM users WHERE username = 'YOUR_USERNAME';
   ```
3. 如果不是 admin，联系管理员授予权限

## 📝 技术细节

### 自动创建逻辑

```python
# 在创建/编辑 vial 时自动调用
VialBatch.auto_create_lineage_from_parental_name(
    child_batch_id=batch.id,
    parental_name=form.parental_cell_line.data,
    created_by_user_id=current_user.id
)
```

**工作流程**：
1. 检查 `parental_name` 是否非空
2. 在数据库中查找同名的父批次
3. 验证不是自引用
4. 检查关系是否已存在
5. 创建新的 BatchLineage 记录
6. 记录日志

**错误处理**：
- 如果父批次不存在：记录日志，但不报错（不影响 vial 创建）
- 如果关系已存在：返回现有记录
- 如果发生其他错误：记录警告，继续执行主流程

### 数据库架构

```sql
-- batch_lineage 表结构
CREATE TABLE batch_lineage (
    id SERIAL PRIMARY KEY,
    parent_batch_id INTEGER NOT NULL REFERENCES vial_batches(id) ON DELETE CASCADE,
    child_batch_id INTEGER NOT NULL REFERENCES vial_batches(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'passage',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id),
    CHECK (parent_batch_id != child_batch_id),
    UNIQUE (parent_batch_id, child_batch_id)
);

-- 索引
CREATE INDEX idx_batch_lineage_parent ON batch_lineage(parent_batch_id);
CREATE INDEX idx_batch_lineage_child ON batch_lineage(child_batch_id);
CREATE INDEX idx_batch_lineage_type ON batch_lineage(relationship_type);
```

## 🎯 后续优化建议

### 短期改进

1. **UI 增强**
   - 在批次详情页添加"管理关系"按钮
   - 提供可视化的关系编辑界面
   - 显示关系质量指标（匹配成功率）

2. **数据验证**
   - 定期检查数据完整性
   - 自动修复不一致的关系
   - 提供关系验证报告

### 长期改进

1. **智能匹配**
   - 模糊匹配父批次名称（处理拼写错误）
   - 支持多个可能的父批次
   - 自动建议父批次

2. **批量操作**
   - 批量编辑关系
   - 批量删除无效关系
   - 批量导入关系数据

3. **分析功能**
   - 谱系路径分析
   - 传代深度统计
   - 细胞系演化追踪

## 📞 支持

如果遇到问题：
1. 查看本文档的"故障排除"部分
2. 检查应用日志：`gcloud app logs tail -s default`
3. 查看 GitHub Issues（如果有）

---

**文档版本**: 1.0
**最后更新**: 2025-10-27
**作者**: Claude Code Assistant
**状态**: 已部署，待测试
