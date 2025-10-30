# 数据库迁移指南

从Google Cloud SQL迁移到Bluehost数据库的完整指南。

## 目录
1. [迁移前准备](#迁移前准备)
2. [从Google Cloud SQL导出](#从google-cloud-sql导出)
3. [导入到Bluehost](#导入到bluehost)
4. [数据验证](#数据验证)
5. [常见问题](#常见问题)

## 迁移前准备

### 评估数据规模
```bash
# 连接到Google Cloud SQL
gcloud sql connect [INSTANCE_NAME] --user=postgres

# 检查数据库大小
psql -d cell_storage -c "SELECT pg_size_pretty(pg_database_size('cell_storage'));"

# 检查表数量和行数
psql -d cell_storage -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
       n_live_tup AS rows
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### 停止写入操作
在迁移前：
1. 通知所有用户系统将维护
2. 禁用打印服务
3. 停止GAE应用实例

```bash
# 停止GAE应用
gcloud app versions stop [VERSION_ID]
```

### 备份现有数据
```bash
# 创建快照备份（Google Cloud SQL）
gcloud sql backups create --instance=[INSTANCE_NAME]

# 验证备份
gcloud sql backups list --instance=[INSTANCE_NAME]
```

## 从Google Cloud SQL导出

### 方法1：使用gcloud命令（推荐）

```bash
# 1. 创建Google Cloud Storage bucket（如果没有）
gsutil mb gs://cellstorage-backup

# 2. 导出数据到Cloud Storage
gcloud sql export sql [INSTANCE_NAME] gs://cellstorage-backup/cell_storage_export.sql \
  --database=cell_storage

# 3. 下载到本地
gsutil cp gs://cellstorage-backup/cell_storage_export.sql ./backup/

# 4. 清理Cloud Storage（可选）
gsutil rm gs://cellstorage-backup/cell_storage_export.sql
```

### 方法2：使用pg_dump（直接导出）

```bash
# 1. 获取Cloud SQL实例的公网IP
gcloud sql instances describe [INSTANCE_NAME] --format="value(ipAddresses[0].ipAddress)"

# 2. 添加你的IP到白名单
gcloud sql instances patch [INSTANCE_NAME] \
  --authorized-networks=[YOUR_IP_ADDRESS]

# 3. 使用pg_dump导出
pg_dump -h [CLOUD_SQL_IP] -U postgres -d cell_storage -F c -b -v -f cell_storage.backup

# 或导出为SQL文本格式
pg_dump -h [CLOUD_SQL_IP] -U postgres -d cell_storage > cell_storage.sql
```

### 方法3：使用Google Cloud Console

1. 登录Google Cloud Console
2. 导航到 SQL → 实例 → [你的实例]
3. 点击 "导出"
4. 选择导出格式：SQL
5. 选择目标：Cloud Storage bucket
6. 点击 "导出"
7. 导出完成后下载文件

## 导入到Bluehost

### PostgreSQL环境（VPS）

#### 1. 创建数据库

```bash
# SSH连接到Bluehost VPS
ssh username@hayerlab.org

# 切换到postgres用户
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE cell_storage;
CREATE USER cellstorage_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE cell_storage TO cellstorage_user;
\q
```

#### 2. 导入数据

```bash
# 方法A：从备份文件恢复（.backup格式）
pg_restore -U cellstorage_user -d cell_storage -v cell_storage.backup

# 方法B：从SQL文件导入
psql -U cellstorage_user -d cell_storage < cell_storage.sql

# 检查导入结果
psql -U cellstorage_user -d cell_storage -c "SELECT tablename FROM pg_tables WHERE schemaname='public';"
```

### MySQL环境（共享主机）

#### 1. 转换PostgreSQL到MySQL

由于PostgreSQL和MySQL语法差异，需要转换SQL脚本：

```bash
# 使用pgloader工具（推荐）
apt-get install pgloader

# 创建配置文件 pgloader.conf
cat > pgloader.conf << EOF
LOAD DATABASE
  FROM postgresql://postgres@localhost/cell_storage_temp
  INTO mysql://user:password@localhost/cell_storage

WITH include drop, create tables, create indexes, reset sequences

SET MySQL PARAMETERS
  net_read_timeout = 120,
  net_write_timeout = 120

CAST type datetime to timestamp drop not null drop default using zero-dates-to-null;
EOF

# 执行迁移
pgloader pgloader.conf
```

#### 2. 手动转换（如果pgloader不可用）

```python
# 使用Python脚本转换
import re

def convert_pg_to_mysql(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    # PostgreSQL到MySQL的转换规则
    conversions = [
        # 数据类型转换
        (r'\bSERIAL\b', 'INT AUTO_INCREMENT'),
        (r'\bBIGSERIAL\b', 'BIGINT AUTO_INCREMENT'),
        (r'\bTEXT\b', 'TEXT'),
        (r'\bBOOLEAN\b', 'TINYINT(1)'),
        (r'\bTIMESTAMP\b', 'DATETIME'),

        # 语法转换
        (r'\bNOW\(\)', 'CURRENT_TIMESTAMP'),
        (r"DEFAULT nextval\('[^']+'\)", ''),
        (r'\bCREATE SEQUENCE[^;]+;', ''),

        # 引号转换
        (r'"(\w+)"', r'`\1`'),
    ]

    for pattern, replacement in conversions:
        sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(sql)

    print(f"转换完成: {output_file}")

# 使用
convert_pg_to_mysql('cell_storage.sql', 'cell_storage_mysql.sql')
```

#### 3. 导入到MySQL（cPanel）

**通过cPanel界面**：
1. 登录cPanel
2. 进入 "MySQL数据库"
3. 创建新数据库 `cell_storage`
4. 创建用户并授权
5. 进入 phpMyAdmin
6. 选择数据库
7. 点击 "导入"
8. 上传转换后的SQL文件
9. 点击 "执行"

**通过SSH（如果可用）**：
```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE cell_storage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 创建用户
mysql -u root -p -e "CREATE USER 'cellstorage_user'@'localhost' IDENTIFIED BY 'your_password';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON cell_storage.* TO 'cellstorage_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"

# 导入数据
mysql -u cellstorage_user -p cell_storage < cell_storage_mysql.sql
```

#### 4. 修改应用配置

更新 `config_bluehost.py`:
```python
# 使用MySQL
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
```

安装MySQL依赖:
```bash
pip install pymysql
```

## 数据验证

### 验证表结构

```bash
# PostgreSQL
psql -U cellstorage_user -d cell_storage -c "\dt"
psql -U cellstorage_user -d cell_storage -c "\d+ users"

# MySQL
mysql -u cellstorage_user -p cell_storage -e "SHOW TABLES;"
mysql -u cellstorage_user -p cell_storage -e "DESCRIBE users;"
```

### 验证数据完整性

```python
# validate_migration.py
from app import create_app, db
from app.cell_storage.models import User, CellLine, VialBatch, CryoVial
from app.inventory.models import InventoryItem, Location

def validate_migration():
    app = create_app()
    with app.app_context():
        # 检查关键表的记录数
        tables = [
            ('Users', User),
            ('CellLines', CellLine),
            ('VialBatches', VialBatch),
            ('CryoVials', CryoVial),
            ('InventoryItems', InventoryItem),
            ('Locations', Location),
        ]

        print("=" * 50)
        print("数据迁移验证报告")
        print("=" * 50)

        for table_name, model in tables:
            count = model.query.count()
            print(f"{table_name}: {count} 条记录")

        # 检查外键关系
        print("\n验证外键关系...")
        orphaned_vials = db.session.query(CryoVial).filter(
            ~CryoVial.batch_id.in_(db.session.query(VialBatch.id))
        ).count()

        if orphaned_vials > 0:
            print(f"⚠️  警告: 发现 {orphaned_vials} 个孤立的CryoVial记录")
        else:
            print("✓ 外键关系完整")

        # 检查数据一致性
        print("\n验证数据一致性...")
        batches_with_vials = db.session.query(VialBatch).filter(
            VialBatch.vials.any()
        ).count()
        total_batches = VialBatch.query.count()

        print(f"有vials的批次: {batches_with_vials}/{total_batches}")

        print("\n" + "=" * 50)
        print("验证完成")
        print("=" * 50)

if __name__ == '__main__':
    validate_migration()
```

运行验证:
```bash
python validate_migration.py
```

### 验证应用功能

```bash
# 测试应用启动
cd /var/www/cellstorage
source venv/bin/activate
python run.py

# 在浏览器访问
# http://hayerlab.org

# 测试关键功能
# - 用户登录
# - 查看cryovial列表
# - 创建新批次
# - 搜索功能
# - 打印功能（如果启用）
```

## 数据一致性检查

### 创建一致性检查脚本

```python
# consistency_check.py
import sys
from app import create_app, db
from sqlalchemy import text

def run_consistency_checks():
    app = create_app()
    with app.app_context():
        checks = []

        # 检查1: 验证所有CryoVial都有有效的batch_id
        orphan_vials = db.session.execute(text("""
            SELECT COUNT(*) FROM cryo_vials cv
            WHERE NOT EXISTS (
                SELECT 1 FROM vial_batches vb WHERE vb.id = cv.batch_id
            )
        """)).scalar()

        checks.append(('孤立的CryoVials', orphan_vials, 0))

        # 检查2: 验证所有VialBatch都有有效的cell_line_id
        orphan_batches = db.session.execute(text("""
            SELECT COUNT(*) FROM vial_batches vb
            WHERE vb.cell_line_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM cell_lines cl WHERE cl.id = vb.cell_line_id
            )
        """)).scalar()

        checks.append(('孤立的VialBatches', orphan_batches, 0))

        # 检查3: 验证位置层级关系
        invalid_locations = db.session.execute(text("""
            SELECT COUNT(*) FROM cryo_vials cv
            WHERE NOT EXISTS (
                SELECT 1 FROM boxes b WHERE b.id = cv.box_id
            )
        """)).scalar()

        checks.append(('无效的存储位置', invalid_locations, 0))

        # 输出结果
        print("\n" + "=" * 60)
        print("数据一致性检查报告")
        print("=" * 60)

        all_passed = True
        for check_name, actual, expected in checks:
            status = "✓ 通过" if actual == expected else "✗ 失败"
            print(f"{check_name}: {actual} (期望: {expected}) - {status}")
            if actual != expected:
                all_passed = False

        print("=" * 60)

        if all_passed:
            print("✓ 所有一致性检查通过")
            return 0
        else:
            print("✗ 发现数据一致性问题")
            return 1

if __name__ == '__main__':
    sys.exit(run_consistency_checks())
```

## 迁移后清理

### 1. 更新应用配置

```bash
# 更新.env文件
nano /var/www/cellstorage/.env

# 确保数据库连接指向Bluehost
DB_HOST=localhost
DB_NAME=cell_storage
DB_USER=cellstorage_user
DB_PASS=your_password
```

### 2. 清理临时文件

```bash
# 删除导出的SQL文件
rm -f cell_storage.sql cell_storage.backup cell_storage_mysql.sql

# 清理Cloud Storage
gsutil -m rm -r gs://cellstorage-backup/*
```

### 3. 停止Google Cloud服务

```bash
# 停止GAE应用
gcloud app versions stop [VERSION_ID]

# 删除Cloud SQL实例（确认数据已迁移后）
# gcloud sql instances delete [INSTANCE_NAME]
```

## 常见问题

### 1. 字符编码问题

**问题**: 中文或特殊字符显示乱码

**解决方案**:
```bash
# PostgreSQL
ALTER DATABASE cell_storage SET client_encoding TO 'UTF8';

# MySQL
ALTER DATABASE cell_storage CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
ALTER TABLE table_name CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 自增ID不同步

**问题**: 导入后新记录ID冲突

**解决方案**:
```sql
-- PostgreSQL
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('vial_batches_id_seq', (SELECT MAX(id) FROM vial_batches));

-- MySQL
ALTER TABLE users AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM users);
ALTER TABLE vial_batches AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM vial_batches);
```

### 3. 外键约束失败

**问题**: 导入时外键约束错误

**解决方案**:
```sql
-- 临时禁用外键检查
SET FOREIGN_KEY_CHECKS = 0;

-- 导入数据
SOURCE cell_storage_mysql.sql;

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 验证外键完整性
SELECT * FROM information_schema.TABLE_CONSTRAINTS
WHERE CONSTRAINT_TYPE = 'FOREIGN KEY';
```

### 4. 大文件导入超时

**问题**: MySQL导入大文件时超时

**解决方案**:
```bash
# 修改MySQL配置
sudo nano /etc/mysql/my.cnf

# 添加以下配置
[mysqld]
max_allowed_packet=256M
net_read_timeout=120
net_write_timeout=120

# 重启MySQL
sudo systemctl restart mysql

# 分批导入
split -l 10000 cell_storage_mysql.sql cell_storage_part_

for file in cell_storage_part_*; do
    mysql -u cellstorage_user -p cell_storage < $file
done
```

### 5. 时区问题

**问题**: 时间戳显示不正确

**解决方案**:
```python
# config_bluehost.py
import pytz

class BluehostConfig:
    TIMEZONE = 'America/New_York'

    @staticmethod
    def init_app(app):
        # 设置应用时区
        app.config['BABEL_DEFAULT_TIMEZONE'] = BluehostConfig.TIMEZONE
```

```sql
-- MySQL设置时区
SET GLOBAL time_zone = '-05:00';  -- 东部时区
```

## 回滚计划

如果迁移失败，可以回滚到Google Cloud SQL：

```bash
# 1. 从备份恢复Google Cloud SQL
gcloud sql backups restore [BACKUP_ID] --instance=[INSTANCE_NAME]

# 2. 重新启动GAE应用
gcloud app deploy

# 3. 验证功能
curl https://your-app.appspot.com/health
```

## 监控和维护

### 设置定期备份

```bash
# 创建备份cron任务
crontab -e

# 添加每日备份（凌晨2点）
0 2 * * * /usr/bin/pg_dump -U cellstorage_user cell_storage > /var/backups/cellstorage_$(date +\%Y\%m\%d).sql

# 清理7天前的备份
0 3 * * * find /var/backups -name "cellstorage_*.sql" -mtime +7 -delete
```

### 性能监控

```sql
-- PostgreSQL慢查询
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- MySQL慢查询
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
```

## 下一步

1. ✅ 验证所有数据已成功迁移
2. ✅ 测试所有关键功能
3. ✅ 设置自动备份
4. ✅ 配置监控告警
5. ✅ 更新DNS记录（如需要）
6. ✅ 通知用户系统已恢复

## 支持

如果遇到迁移问题，请：
1. 检查日志文件
2. 运行一致性检查脚本
3. 查看常见问题部分
4. 联系技术支持并提供详细错误信息
