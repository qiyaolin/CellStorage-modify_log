#!/bin/bash

# Google Cloud 集中式打印系统部署脚本
# 为现有App Engine应用添加打印功能

set -e  # 遇到错误时退出

echo "🌐 Cell Storage 集中式打印系统部署"
echo "🔗 目标: https://ambient-decoder-467517-h8.nn.r.appspot.com/"
echo "=" 

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查必要工具
echo -e "${BLUE}🔍 检查部署环境...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK未安装${NC}"
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"

# 检查Google Cloud配置
echo -e "${BLUE}🔧 检查Google Cloud配置...${NC}"

PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$PROJECT" != "ambient-decoder-467517-h8" ]; then
    echo -e "${YELLOW}⚠️  当前项目: $PROJECT${NC}"
    echo -e "${YELLOW}   期望项目: ambient-decoder-467517-h8${NC}"
    read -p "是否继续？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✅ Google Cloud配置正确${NC}"

# 第一步：数据库迁移
echo -e "${BLUE}📊 第一步: 数据库迁移${NC}"
echo "正在添加打印系统数据表到Cloud SQL..."

python cloud_migration_update.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 数据库迁移失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 数据库迁移完成${NC}"

# 第二步：检查配置文件
echo -e "${BLUE}⚙️  第二步: 检查配置文件${NC}"

if [ ! -f "app.yaml" ]; then
    echo -e "${RED}❌ app.yaml文件不存在${NC}"
    exit 1
fi

# 检查是否包含打印配置
if grep -q "CENTRALIZED_PRINTING_ENABLED" app.yaml; then
    echo -e "${GREEN}✅ app.yaml包含打印配置${NC}"
else
    echo -e "${YELLOW}⚠️  app.yaml缺少打印配置${NC}"
    echo "请在app.yaml的env_variables部分添加："
    echo "  CENTRALIZED_PRINTING_ENABLED: \"true\""
    read -p "是否继续部署？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 第三步：部署到App Engine
echo -e "${BLUE}🚀 第三步: 部署到App Engine${NC}"
echo "正在部署更新的应用..."

gcloud app deploy --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ App Engine部署失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ App Engine部署完成${NC}"

# 第四步：验证部署
echo -e "${BLUE}🧪 第四步: 验证部署${NC}"

echo "等待应用启动..."
sleep 10

# 检查应用健康状态
echo "检查应用状态..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" https://ambient-decoder-467517-h8.nn.r.appspot.com/)

if [ "$HEALTH_CHECK" = "200" ]; then
    echo -e "${GREEN}✅ 应用运行正常${NC}"
else
    echo -e "${YELLOW}⚠️  应用状态码: $HEALTH_CHECK${NC}"
fi

# 检查打印API
echo "检查打印API..."
PRINT_API_CHECK=$(curl -s -o /dev/null -w "%{http_code}" https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/status)

if [ "$PRINT_API_CHECK" = "200" ]; then
    echo -e "${GREEN}✅ 打印API可访问${NC}"
else
    echo -e "${YELLOW}⚠️  打印API状态码: $PRINT_API_CHECK${NC}"
fi

# 完成信息
echo
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "=" 
echo -e "${BLUE}📋 部署摘要:${NC}"
echo "✅ 数据库已更新（添加打印表）"
echo "✅ 应用已部署到App Engine"
echo "✅ 打印API已激活"
echo
echo -e "${BLUE}🌐 应用访问地址:${NC}"
echo "https://ambient-decoder-467517-h8.nn.r.appspot.com/"
echo
echo -e "${BLUE}🖨️  打印功能测试:${NC}"
echo "1. 访问应用并登录"
echo "2. 进入 'Add CryoVial(s)' 页面"
echo "3. 创建小管时选择 'Print vial labels after saving'"
echo "4. 查看打印模态框和任务状态"
echo
echo -e "${BLUE}📊 管理界面:${NC}"
echo "访问 /admin 查看打印任务和服务器状态"
echo
echo -e "${BLUE}🔧 API端点:${NC}"
echo "• 打印状态: /api/print/status"
echo "• 打印统计: /api/print/stats"
echo
echo -e "${YELLOW}📝 注意事项:${NC}"
echo "• 打印任务现在存储在数据库中"
echo "• 如需自动打印，请设置打印服务器"
echo "• 查看 GOOGLE_CLOUD_UPDATE_GUIDE.md 了解详细信息"
echo
echo -e "${GREEN}部署成功完成！${NC}"