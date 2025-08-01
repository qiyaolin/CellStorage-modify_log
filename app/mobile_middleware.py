from flask import request, redirect, url_for
import re

def is_mobile_device():
    """Detect if it's a mobile device - Enhanced version"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Mobile device keywords
    mobile_keywords = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 
        'blackberry', 'windows phone', 'opera mini',
        'webos', 'palm', 'symbian', 'nokia', 'samsung',
        'htc', 'lg', 'motorola', 'sony', 'xiaomi'
    ]
    
    # Mobile browser regular expressions
    mobile_patterns = [
        r'android.*mobile',
        r'iphone',
        r'ipod',
        r'ipad',
        r'blackberry',
        r'windows phone',
        r'opera mini',
        r'mobile.*safari',
        r'mobile.*chrome'
    ]
    
    # Check keywords
    keyword_match = any(keyword in user_agent for keyword in mobile_keywords)
    
    # Check regular expressions
    pattern_match = any(re.search(pattern, user_agent) for pattern in mobile_patterns)
    
    # Check screen width (if available)
    accept = request.headers.get('Accept', '')
    is_wap = 'wap' in accept.lower()
    
    return keyword_match or pattern_match or is_wap

def mobile_redirect_middleware(app):
    """Mobile redirect middleware"""
    @app.before_request
    def check_mobile():
        # Debug information
        user_agent = request.headers.get('User-Agent', '')
        is_mobile = is_mobile_device()
        
        # Log for debugging
        app.logger.info(f"Access path: {request.path}")
        app.logger.info(f"User-Agent: {user_agent}")
        app.logger.info(f"Is mobile device: {is_mobile}")
        app.logger.info(f"Request endpoint: {request.endpoint}")
        
        # Check if accessing homepage and is mobile device
        if (request.path in ['/cell-storage/', '/cell-storage/index'] or 
            request.endpoint == 'cell_storage_main.index') and is_mobile:
            # Avoid duplicate redirects
            if not request.path.startswith('/cell-storage/mobile'):
                app.logger.info("Redirecting to mobile page")
                return redirect(url_for('mobile.mobile_index'))
        
        return None
