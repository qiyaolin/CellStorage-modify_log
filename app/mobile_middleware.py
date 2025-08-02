"""
Mobile Device Detection Middleware for CellStorage

This middleware detects mobile devices based on User-Agent strings and provides
mobile-optimized functionality throughout the application without affecting
existing desktop functionality.
"""

import re
from flask import request, g, session, redirect, url_for
from urllib.parse import urlparse


class MobileDetectionMiddleware:
    """Mobile device detection middleware"""
    
    # Mobile device User-Agent pattern matching
    MOBILE_USER_AGENTS = [
        # iOS devices
        r'iPhone', r'iPad', r'iPod',
        
        # Android devices
        r'Android.*Mobile', r'Android.*Tablet',
        
        # Windows Mobile
        r'Windows Phone', r'Windows Mobile', r'IEMobile',
        
        # BlackBerry
        r'BlackBerry', r'BB10',
        
        # Other mobile devices
        r'Mobile', r'Tablet', r'Phone',
        
        # Common mobile browsers
        r'Opera Mini', r'Opera Mobi',
        r'Chrome.*Mobile', r'Firefox.*Mobile',
        r'Safari.*Mobile',
        
        # Specific device identifiers
        r'webOS', r'Palm', r'Symbian', r'Nokia',
        r'Samsung.*Mobile', r'LG.*Mobile', r'HTC.*Mobile'
    ]
    
    # Compile regex patterns
    MOBILE_PATTERN = re.compile(
        '|'.join(MOBILE_USER_AGENTS), 
        re.IGNORECASE
    )
    
    # Tablet device specific patterns (may need special handling)
    TABLET_PATTERN = re.compile(
        r'iPad|Android.*Tablet|Windows.*Touch|Tablet|PlayBook',
        re.IGNORECASE
    )
    
    def __init__(self, app=None):
        """Initialize middleware"""
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Flask application"""
        app.before_request(self.detect_mobile_device)
        app.context_processor(self.inject_mobile_context)
        
        # Register template global functions
        app.jinja_env.globals.update(
            is_mobile_device=self.is_mobile_device,
            is_tablet_device=self.is_tablet_device,
            get_device_type=self.get_device_type,
            should_use_mobile_template=self.should_use_mobile_template
        )
    
    def detect_mobile_device(self):
        """Detect mobile device before each request"""
        user_agent = request.headers.get('User-Agent', '')
        
        # Detect if it's a mobile device
        is_mobile = bool(self.MOBILE_PATTERN.search(user_agent))
        is_tablet = bool(self.TABLET_PATTERN.search(user_agent))
        
        # Store detection results in Flask's g object
        g.is_mobile = is_mobile
        g.is_tablet = is_tablet
        g.user_agent = user_agent
        
        # Determine device type
        if is_tablet:
            g.device_type = 'tablet'
        elif is_mobile:
            g.device_type = 'mobile'
        else:
            g.device_type = 'desktop'
        
        # Check if user manually switched view mode
        view_mode = request.args.get('view_mode') or session.get('view_mode')
        if view_mode in ['mobile', 'desktop']:
            session['view_mode'] = view_mode
            g.force_view_mode = view_mode
        else:
            g.force_view_mode = None
    
    def inject_mobile_context(self):
        """Inject mobile device related context variables into templates"""
        return {
            'is_mobile': getattr(g, 'is_mobile', False),
            'is_tablet': getattr(g, 'is_tablet', False),
            'device_type': getattr(g, 'device_type', 'desktop'),
            'force_view_mode': getattr(g, 'force_view_mode', None),
            'current_view_mode': self.get_current_view_mode()
        }
    
    @staticmethod
    def is_mobile_device():
        """Check if current request is from mobile device"""
        return getattr(g, 'is_mobile', False)
    
    @staticmethod
    def is_tablet_device():
        """Check if current request is from tablet device"""
        return getattr(g, 'is_tablet', False)
    
    @staticmethod
    def get_device_type():
        """Get device type"""
        return getattr(g, 'device_type', 'desktop')
    
    @staticmethod
    def get_current_view_mode():
        """Get current view mode - but never auto-redirect to maintain desktop functionality"""
        force_mode = getattr(g, 'force_view_mode', None)
        if force_mode:
            return force_mode
        
        # Always default to desktop to preserve existing functionality
        return 'desktop'
    
    @staticmethod
    def should_use_mobile_template():
        """Determine if mobile template should be used - only when explicitly requested"""
        force_mode = getattr(g, 'force_view_mode', None)
        return force_mode == 'mobile'
    
    @staticmethod
    def get_mobile_route_name(route_name):
        """Convert desktop route name to mobile route name"""
        if route_name.startswith('mobile.'):
            return route_name
        return f'mobile.{route_name}'
    
    @staticmethod
    def get_desktop_route_name(route_name):
        """Convert mobile route name to desktop route name"""
        if route_name.startswith('mobile.'):
            return route_name[7:]  # Remove 'mobile.' prefix
        return route_name
    
    @staticmethod
    def get_template_name(base_template, mobile_template=None):
        """Select appropriate template based on device type - only when mobile explicitly requested"""
        if MobileDetectionMiddleware.should_use_mobile_template():
            if mobile_template:
                return mobile_template
            else:
                # Auto-generate mobile template name
                if '/' in base_template:
                    parts = base_template.split('/')
                    return f"mobile/{'/'.join(parts)}"
                else:
                    return f"mobile/{base_template}"
        return base_template


def init_mobile_middleware(app):
    """Convenience function to initialize mobile middleware"""
    middleware = MobileDetectionMiddleware(app)
    return middleware


# Mobile decorators - for explicit mobile routes only
def mobile_template(mobile_template_name=None):
    """Decorator: automatically select mobile or desktop template"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Execute original view function
            result = func(*args, **kwargs)
            
            # Template selection should be handled in the actual view function
            return result
        return wrapper
    return decorator