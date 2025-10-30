#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DYMO打印系统快速测试脚本
用于验证生产环境部署是否正常
"""

import os
import sys
import json
import requests
from pathlib import Path

def test_system_requirements():
    """测试系统要求"""
    print("🔍 检查系统要求...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 7:
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
    else:
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor} (需要3.7+)")
        return False
    
    # 检查必要文件
    required_files = [
        'src/production_print_agent.py',
        'src/auto_print_template.html',
        'src/print_agent_config.json'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ 文件存在: {file_path}")
        else:
            print(f"❌ 文件缺失: {file_path}")
            return False
    
    return True

def test_configuration():
    """测试配置文件"""
    print("\n🔧 检查配置文件...")
    
    config_path = 'src/print_agent_config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_keys = ['backend_url', 'template_path', 'poll_interval']
        for key in required_keys:
            if key in config:
                print(f"✅ 配置项 {key}: {config[key]}")
            else:
                print(f"❌ 缺少配置项: {key}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return False

def test_backend_connection():
    """测试后端连接"""
    print("\n🌐 测试后端连接...")
    
    try:
        with open('src/print_agent_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        backend_url = config['backend_url']
        test_url = f"{backend_url}/health/"
        
        print(f"测试URL: {test_url}")
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ 后端服务器连接正常")
            return True
        else:
            print(f"⚠️ 后端响应状态码: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 后端连接测试失败: {e}")
        print("注意: 这可能是正常的，如果后端服务器未运行或网络问题")
        return False
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        return False

def test_import_agent():
    """测试导入打印代理"""
    print("\n📦 测试打印代理导入...")
    
    try:
        # 切换到src目录进行测试
        original_cwd = os.getcwd()
        src_dir = os.path.join(os.getcwd(), 'src')
        os.chdir(src_dir)
        
        sys.path.insert(0, src_dir)
        from production_print_agent import ProductionPrintAgent
        
        # 创建代理实例
        agent = ProductionPrintAgent()
        print("✅ 打印代理导入成功")
        print(f"✅ 模板路径: {agent.template_path}")
        print(f"✅ 后端URL: {agent.backend_url}")
        
        # 恢复原始工作目录
        os.chdir(original_cwd)
        
        return True
    except Exception as e:
        print(f"❌ 打印代理导入失败: {e}")
        # 确保恢复原始工作目录
        try:
            os.chdir(original_cwd)
        except:
            pass
        return False

def main():
    """主测试函数"""
    print("🚀 DYMO打印系统生产环境测试")
    print("=" * 50)
    
    tests = [
        ("系统要求", test_system_requirements),
        ("配置文件", test_configuration),
        ("后端连接", test_backend_connection),
        ("代理导入", test_import_agent)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！系统已准备就绪。")
        print("\n🚀 启动打印代理:")
        print("   方法1: 双击 start_print_agent.bat")
        print("   方法2: cd src && python production_print_agent.py")
    else:
        print("\n⚠️ 部分测试失败，请检查上述问题后重试。")

if __name__ == "__main__":
    main()