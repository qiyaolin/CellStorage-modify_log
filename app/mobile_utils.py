from flask import request
import re

def is_mobile_device():
    """检测是否为移动设备"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    mobile_patterns = [
        r'mobile', r'android', r'iphone', r'ipad', r'ipod',
        r'blackberry', r'windows phone', r'opera mini',
        r'palm', r'webos', r'symbian', r'nokia'
    ]
    
    for pattern in mobile_patterns:
        if re.search(pattern, user_agent):
            return True
    
    return False

def get_mobile_redirect_url():
    """获取移动端重定向URL"""
    # 在生产环境中，您可以将移动端应用部署到子域名或子路径
    # 例如: https://ambient-decoder-467517-h8.nn.r.appspot.com/mobile/
    # 或者: https://mobile.ambient-decoder-467517-h8.nn.r.appspot.com/
    
    # 暂时返回开发环境的URL，您可以根据需要修改
    return '/cell-storage/mobile'