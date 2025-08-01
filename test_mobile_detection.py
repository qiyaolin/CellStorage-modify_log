#!/usr/bin/env python3
"""
移动端检测测试脚本
"""

from app import create_app
from flask import Flask
import requests
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

def test_mobile_detection():
    """测试移动端检测功能"""
    
    # 不同的User-Agent字符串
    test_cases = [
        {
            'name': 'iPhone Safari',
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'expected': True
        },
        {
            'name': 'Android Chrome',
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'expected': True
        },
        {
            'name': 'iPad Safari',
            'user_agent': 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'expected': True
        },
        {
            'name': 'Desktop Chrome',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'expected': False
        },
        {
            'name': 'Desktop Firefox',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'expected': False
        }
    ]
    
    app = create_app()
    
    print("🧪 开始测试移动端检测功能...\n")
    
    with app.app_context():
        from app.mobile_middleware import is_mobile_device
        
        for test_case in test_cases:
            with app.test_request_context('/', headers={'User-Agent': test_case['user_agent']}):
                result = is_mobile_device()
                status = "✅ 通过" if result == test_case['expected'] else "❌ 失败"
                print(f"{status} {test_case['name']}: 检测结果={result}, 预期={test_case['expected']}")
    
    print(f"\n🎉 测试完成！")

if __name__ == '__main__':
    test_mobile_detection()