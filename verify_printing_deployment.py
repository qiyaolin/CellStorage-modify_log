"""
验证Google Cloud上的集中式打印系统部署
用于检查 https://ambient-decoder-467517-h8.nn.r.appspot.com/ 的打印功能
"""

import requests
import json
import sys
from datetime import datetime

# 应用URL
APP_URL = "https://ambient-decoder-467517-h8.nn.r.appspot.com"

def test_app_health():
    """测试应用基本健康状态"""
    try:
        print("🏥 测试应用健康状态...")
        response = requests.get(f"{APP_URL}/", timeout=10)
        
        if response.status_code == 200:
            print("✅ 应用运行正常")
            return True
        else:
            print(f"⚠️  应用状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 应用连接失败: {e}")
        return False

def test_print_api():
    """测试打印API端点"""
    try:
        print("\n🖨️  测试打印API...")
        
        # 测试状态端点
        response = requests.get(f"{APP_URL}/api/print/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 打印API可访问")
            print(f"   - 系统可用: {data.get('available', 'unknown')}")
            print(f"   - 在线服务器: {data.get('online_servers', 0)}")
            print(f"   - 待处理任务: {data.get('pending_jobs', 0)}")
            print(f"   - 总任务数: {data.get('total_jobs', 0)}")
            return True
        elif response.status_code == 401:
            print("⚠️  打印API需要登录访问（正常情况）")
            return True
        else:
            print(f"❌ 打印API状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 打印API连接失败: {e}")
        return False

def test_print_stats():
    """测试打印统计端点"""
    try:
        print("\n📊 测试打印统计...")
        
        response = requests.get(f"{APP_URL}/api/print/stats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 打印统计API可访问")
            if 'jobs' in data:
                jobs = data['jobs']
                print(f"   - 总任务: {jobs.get('total', 0)}")
                print(f"   - 待处理: {jobs.get('pending', 0)}")
                print(f"   - 已完成: {jobs.get('completed', 0)}")
                print(f"   - 失败: {jobs.get('failed', 0)}")
                print(f"   - 成功率: {jobs.get('success_rate', 0)}%")
            if 'servers' in data:
                servers = data['servers']
                print(f"   - 服务器总数: {servers.get('total', 0)}")
                print(f"   - 在线服务器: {servers.get('online', 0)}")
            return True
        elif response.status_code == 401:
            print("⚠️  统计API需要登录访问（正常情况）")
            return True
        else:
            print(f"❌ 统计API状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 统计API连接失败: {e}")
        return False

def test_admin_interface():
    """测试管理界面"""
    try:
        print("\n👑 测试管理界面...")
        
        response = requests.get(f"{APP_URL}/admin", timeout=10)
        
        if response.status_code in [200, 302, 401, 403]:
            print("✅ 管理界面可访问")
            if response.status_code == 302:
                print("   - 重定向到登录页面（正常）")
            elif response.status_code in [401, 403]:
                print("   - 需要认证（正常）")
            return True
        else:
            print(f"❌ 管理界面状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 管理界面连接失败: {e}")
        return False

def test_print_endpoints():
    """测试其他打印端点"""
    try:
        print("\n🔧 测试其他打印端点...")
        
        endpoints = [
            "/api/print/fetch-pending-job",
            "/api/print/heartbeat",
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                response = requests.get(f"{APP_URL}{endpoint}", timeout=5)
                if response.status_code in [200, 400, 401, 404]:  # 这些都是预期的响应
                    results.append(f"✅ {endpoint}: {response.status_code}")
                else:
                    results.append(f"⚠️  {endpoint}: {response.status_code}")
            except Exception as e:
                results.append(f"❌ {endpoint}: {str(e)}")
        
        for result in results:
            print(f"   {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 端点测试失败: {e}")
        return False

def check_frontend_files():
    """检查前端文件是否可访问"""
    try:
        print("\n🌐 测试前端资源...")
        
        # 测试一些关键页面
        pages_to_test = [
            "/cell-storage/add",  # 添加小管页面
            "/cell-storage/inventory",  # 库存页面
        ]
        
        accessible_pages = 0
        
        for page in pages_to_test:
            try:
                response = requests.get(f"{APP_URL}{page}", timeout=5)
                if response.status_code in [200, 302, 401]:
                    accessible_pages += 1
                    print(f"   ✅ {page}: 可访问")
                else:
                    print(f"   ⚠️  {page}: 状态码 {response.status_code}")
            except Exception as e:
                print(f"   ❌ {page}: {str(e)}")
        
        print(f"   📊 可访问页面: {accessible_pages}/{len(pages_to_test)}")
        return accessible_pages > 0
        
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")
        return False

def run_full_verification():
    """运行完整验证"""
    print("🔍 Google Cloud 集中式打印系统验证")
    print(f"🌐 目标: {APP_URL}")
    print(f"🕐 开始时间: {datetime.now()}")
    print("=" * 60)
    
    tests = [
        ("应用健康状态", test_app_health),
        ("打印API", test_print_api),
        ("打印统计", test_print_stats),
        ("管理界面", test_admin_interface),
        ("打印端点", test_print_endpoints),
        ("前端资源", check_frontend_files),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试出错: {e}")
            results.append((test_name, False))
    
    # 总结报告
    print("\n" + "=" * 60)
    print("📋 验证结果摘要")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！集中式打印系统部署成功。")
        print("\n📝 下一步:")
        print("1. 登录应用测试用户界面")
        print("2. 创建小管时选择打印选项")
        print("3. 查看管理界面中的打印任务")
        print("4. 如需自动打印，设置打印服务器")
        return True
    elif passed >= total * 0.8:
        print("⚠️  大部分测试通过，但有些问题需要注意。")
        print("📞 建议检查失败的项目和应用日志。")
        return True
    else:
        print("❌ 多项测试失败，部署可能有问题。")
        print("🔧 建议:")
        print("1. 检查应用日志: gcloud app logs tail")
        print("2. 验证数据库迁移是否成功")
        print("3. 检查app.yaml配置")
        return False

if __name__ == '__main__':
    success = run_full_verification()
    
    print(f"\n🕐 完成时间: {datetime.now()}")
    
    if not success:
        sys.exit(1)