/**
 * Mobile JavaScript for CellStorage
 * Provides touch-optimized interactions and mobile-specific functionality
 */

// Mobile namespace
const MobileApp = {
    initialized: false,
    touchStart: { x: 0, y: 0 },
    touchEnd: { x: 0, y: 0 },
    swipeThreshold: 50,
    tapDelay: 300,
    lastTap: 0
};

/**
 * Initialize mobile app
 */
document.addEventListener('DOMContentLoaded', function() {
    if (MobileApp.initialized) return;
    
    MobileApp.init();
    MobileApp.initialized = true;
});

/**
 * Main initialization
 */
MobileApp.init = function() {
    this.setupTouchEvents();
    this.setupFormEnhancements();
    this.setupNavigationEnhancements();
    this.setupSearchEnhancements();
    this.setupModalEnhancements();
    this.setupLoadingStates();
    this.setupOfflineSupport();
    this.setupAccessibility();
    
    console.log('Mobile app initialized');
};

/**
 * Setup touch events and gestures
 */
MobileApp.setupTouchEvents = function() {
    // Prevent double-tap zoom on buttons
    document.querySelectorAll('button, .btn, .mobile-nav-item, .quick-action-btn').forEach(function(element) {
        element.addEventListener('touchend', function(e) {
            e.preventDefault();
            
            // Simulate click with delay to prevent double firing
            setTimeout(() => {
                if (!element.disabled) {
                    element.click();
                }
            }, 10);
        });
    });
    
    // Add touch feedback for interactive elements
    document.querySelectorAll('.card-mobile, .list-group-item, .quick-action-btn').forEach(function(element) {
        element.addEventListener('touchstart', function(e) {
            this.classList.add('touch-feedback');
            this.style.transform = 'scale(0.98)';
            this.style.opacity = '0.8';
        });
        
        element.addEventListener('touchend', function(e) {
            setTimeout(() => {
                this.classList.remove('touch-feedback');
                this.style.transform = '';
                this.style.opacity = '';
            }, 150);
        });
        
        element.addEventListener('touchcancel', function(e) {
            this.classList.remove('touch-feedback');
            this.style.transform = '';
            this.style.opacity = '';
        });
    });
    
    // Setup swipe gestures
    this.setupSwipeGestures();
};

/**
 * Setup swipe gestures
 */
MobileApp.setupSwipeGestures = function() {
    document.addEventListener('touchstart', function(e) {
        MobileApp.touchStart.x = e.touches[0].clientX;
        MobileApp.touchStart.y = e.touches[0].clientY;
    });
    
    document.addEventListener('touchend', function(e) {
        MobileApp.touchEnd.x = e.changedTouches[0].clientX;
        MobileApp.touchEnd.y = e.changedTouches[0].clientY;
        
        MobileApp.handleSwipe();
    });
};

/**
 * Handle swipe gestures
 */
MobileApp.handleSwipe = function() {
    const deltaX = this.touchEnd.x - this.touchStart.x;
    const deltaY = this.touchEnd.y - this.touchStart.y;
    
    // Check if it's a horizontal swipe
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > this.swipeThreshold) {
        if (deltaX > 0) {
            this.onSwipeRight();
        } else {
            this.onSwipeLeft();
        }
    }
    
    // Check if it's a vertical swipe
    if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > this.swipeThreshold) {
        if (deltaY > 0) {
            this.onSwipeDown();
        } else {
            this.onSwipeUp();
        }
    }
};

/**
 * Swipe event handlers
 */
MobileApp.onSwipeRight = function() {
    // Could be used for navigation back
    console.log('Swipe right detected');
};

MobileApp.onSwipeLeft = function() {
    // Could be used for navigation forward
    console.log('Swipe left detected');
};

MobileApp.onSwipeDown = function() {
    // Could be used for refresh
    console.log('Swipe down detected');
};

MobileApp.onSwipeUp = function() {
    // Could be used for additional actions
    console.log('Swipe up detected');
};

/**
 * Setup form enhancements
 */
MobileApp.setupFormEnhancements = function() {
    // Auto-submit forms on filter changes with debounce
    const filterInputs = document.querySelectorAll('select[name="creator"], select[name="fluorescence"], select[name="resistance"]');
    filterInputs.forEach(function(input) {
        let timeoutId;
        input.addEventListener('change', function() {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                if (this.form) {
                    MobileApp.showLoading();
                    this.form.submit();
                }
            }, 300);
        });
    });
    
    // Enhanced form validation
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>Processing...';
                
                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    if (submitBtn.disabled) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = submitBtn.dataset.originalText || 'Submit';
                    }
                }, 10000);
            }
        });
    });
    
    // Auto-resize textareas
    document.querySelectorAll('textarea').forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
    
    // Input focus enhancements
    document.querySelectorAll('input, select, textarea').forEach(function(input) {
        input.addEventListener('focus', function() {
            // Scroll into view with offset for mobile keyboard
            setTimeout(() => {
                this.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        });
    });
};

/**
 * Setup navigation enhancements
 */
MobileApp.setupNavigationEnhancements = function() {
    // Active navigation highlighting
    const currentPath = window.location.pathname;
    document.querySelectorAll('.mobile-nav-item').forEach(function(navItem) {
        const href = navItem.getAttribute('href');
        if (href && currentPath.includes(href.split('/').pop())) {
            navItem.classList.add('active');
        }
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    
    // Back button handling
    document.querySelectorAll('[data-action="back"]').forEach(function(backBtn) {
        backBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (window.history.length > 1) {
                window.history.back();
            } else {
                window.location.href = '/mobile/';
            }
        });
    });
};

/**
 * Setup search enhancements
 */
MobileApp.setupSearchEnhancements = function() {
    // Auto-focus search inputs
    const searchInput = document.querySelector('input[name="q"], .mobile-search input');
    if (searchInput && !searchInput.value) {
        setTimeout(() => {
            searchInput.focus();
        }, 500);
    }
    
    // Search input enhancements
    document.querySelectorAll('.mobile-search input').forEach(function(input) {
        // Clear button
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'mobile-search-clear';
        clearBtn.innerHTML = '<i class="fas fa-times"></i>';
        clearBtn.style.cssText = `
            position: absolute;
            right: 2.5rem;
            top: 50%;
            transform: translateY(-50%);
            border: none;
            background: none;
            color: #6c757d;
            padding: 0.25rem;
            display: none;
        `;
        
        input.parentNode.appendChild(clearBtn);
        
        // Show/hide clear button
        function toggleClearButton() {
            clearBtn.style.display = input.value ? 'block' : 'none';
        }
        
        input.addEventListener('input', toggleClearButton);
        toggleClearButton();
        
        // Clear functionality
        clearBtn.addEventListener('click', function() {
            input.value = '';
            input.focus();
            toggleClearButton();
            
            // Trigger change event
            input.dispatchEvent(new Event('input', { bubbles: true }));
        });
        
        // Search on Enter
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const searchBtn = this.parentNode.querySelector('.mobile-search-btn');
                if (searchBtn) {
                    searchBtn.click();
                } else if (this.form) {
                    this.form.submit();
                }
            }
        });
    });
};

/**
 * Setup modal enhancements
 */
MobileApp.setupModalEnhancements = function() {
    // Add mobile class to all modals
    document.querySelectorAll('.modal').forEach(function(modal) {
        modal.classList.add('modal-mobile');
    });
    
    // Auto-focus first input in modals
    document.querySelectorAll('.modal').forEach(function(modal) {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = this.querySelector('input:not([type="hidden"]), select, textarea');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        });
    });
    
    // Close modal on background tap
    document.querySelectorAll('.modal').forEach(function(modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                const bsModal = bootstrap.Modal.getInstance(this);
                if (bsModal) {
                    bsModal.hide();
                }
            }
        });
    });
};

/**
 * Setup loading states
 */
MobileApp.setupLoadingStates = function() {
    // Global loading overlay
    this.createLoadingOverlay();
    
    // Auto-show loading for form submissions
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function() {
            // Don't show loading for search forms (too quick)
            if (!this.classList.contains('search-form')) {
                setTimeout(() => MobileApp.showLoading(), 100);
            }
        });
    });
    
    // Auto-show loading for navigation
    document.querySelectorAll('a:not([href^="#"]):not([href^="javascript:"]):not([target="_blank"])').forEach(function(link) {
        link.addEventListener('click', function(e) {
            // Don't show loading for same-page navigation
            if (this.href && this.href !== window.location.href) {
                setTimeout(() => MobileApp.showLoading(), 100);
            }
        });
    });
};

/**
 * Create loading overlay
 */
MobileApp.createLoadingOverlay = function() {
    if (document.getElementById('mobile-loading-overlay')) return;
    
    const overlay = document.createElement('div');
    overlay.id = 'mobile-loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.style.display = 'none';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner mb-2" style="width: 2rem; height: 2rem; border-width: 3px;"></div>
            <div>Loading...</div>
        </div>
    `;
    
    document.body.appendChild(overlay);
};

/**
 * Show loading overlay
 */
MobileApp.showLoading = function(message = 'Loading...') {
    const overlay = document.getElementById('mobile-loading-overlay');
    if (overlay) {
        overlay.querySelector('.loading-content div:last-child').textContent = message;
        overlay.style.display = 'flex';
    }
};

/**
 * Hide loading overlay
 */
MobileApp.hideLoading = function() {
    const overlay = document.getElementById('mobile-loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
};

/**
 * Setup offline support
 */
MobileApp.setupOfflineSupport = function() {
    // Check online status
    function updateOnlineStatus() {
        const isOnline = navigator.onLine;
        const indicator = document.getElementById('online-indicator');
        
        if (!indicator) {
            const indicatorEl = document.createElement('div');
            indicatorEl.id = 'online-indicator';
            indicatorEl.style.cssText = `
                position: fixed;
                top: 1rem;
                right: 1rem;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-size: 0.875rem;
                font-weight: 500;
                z-index: 1050;
                transition: all 0.3s ease;
            `;
            document.body.appendChild(indicatorEl);
        }
        
        const indicator2 = document.getElementById('online-indicator');
        
        if (isOnline) {
            indicator2.textContent = 'Online';
            indicator2.className = 'bg-success text-white';
            indicator2.style.opacity = '0';
        } else {
            indicator2.textContent = 'Offline';
            indicator2.className = 'bg-warning text-dark';
            indicator2.style.opacity = '1';
        }
    }
    
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();
    
    // Cache important data in localStorage
    this.setupDataCaching();
};

/**
 * Setup data caching
 */
MobileApp.setupDataCaching = function() {
    // Cache search results
    const searchResults = document.querySelectorAll('.search-results [data-cache]');
    if (searchResults.length > 0) {
        const cacheData = Array.from(searchResults).map(el => ({
            id: el.dataset.cache,
            html: el.outerHTML,
            timestamp: Date.now()
        }));
        
        try {
            localStorage.setItem('mobile_search_cache', JSON.stringify(cacheData));
        } catch (e) {
            console.warn('Failed to cache search results:', e);
        }
    }
    
    // Clear old cache (older than 1 hour)
    try {
        const cached = localStorage.getItem('mobile_search_cache');
        if (cached) {
            const data = JSON.parse(cached);
            const oneHour = 60 * 60 * 1000;
            const filtered = data.filter(item => Date.now() - item.timestamp < oneHour);
            localStorage.setItem('mobile_search_cache', JSON.stringify(filtered));
        }
    } catch (e) {
        console.warn('Failed to clean cache:', e);
    }
};

/**
 * Setup accessibility enhancements
 */
MobileApp.setupAccessibility = function() {
    // Improve focus management
    document.addEventListener('keydown', function(e) {
        // Escape key to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const bsModal = bootstrap.Modal.getInstance(openModal);
                if (bsModal) {
                    bsModal.hide();
                }
            }
        }
    });
    
    // Add skip link
    this.addSkipLink();
    
    // Improve screen reader announcements
    this.setupScreenReaderAnnouncements();
};

/**
 * Add skip link for accessibility
 */
MobileApp.addSkipLink = function() {
    if (document.getElementById('skip-link')) return;
    
    const skipLink = document.createElement('a');
    skipLink.id = 'skip-link';
    skipLink.href = '#main-content';
    skipLink.textContent = 'Skip to main content';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        background: #007bff;
        color: white;
        padding: 8px;
        text-decoration: none;
        border-radius: 4px;
        z-index: 9999;
        transition: top 0.3s;
    `;
    
    skipLink.addEventListener('focus', function() {
        this.style.top = '6px';
    });
    
    skipLink.addEventListener('blur', function() {
        this.style.top = '-40px';
    });
    
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main content id if it doesn't exist
    const mainContent = document.querySelector('main, .mobile-content');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
    }
};

/**
 * Setup screen reader announcements
 */
MobileApp.setupScreenReaderAnnouncements = function() {
    // Create announcement region
    if (!document.getElementById('sr-announcements')) {
        const announceEl = document.createElement('div');
        announceEl.id = 'sr-announcements';
        announceEl.setAttribute('aria-live', 'polite');
        announceEl.setAttribute('aria-atomic', 'true');
        announceEl.style.cssText = `
            position: absolute;
            left: -10000px;
            top: auto;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        document.body.appendChild(announceEl);
    }
};

/**
 * Announce message to screen readers
 */
MobileApp.announce = function(message) {
    const announceEl = document.getElementById('sr-announcements');
    if (announceEl) {
        announceEl.textContent = message;
    }
};

/**
 * Show mobile alert
 */
MobileApp.showAlert = function(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-mobile alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('main, .mobile-content');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
        
        // Announce to screen readers
        this.announce(message);
    }
};

/**
 * Utility functions
 */
MobileApp.utils = {
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function
    throttle: function(func, limit) {
        let lastFunc;
        let lastRan;
        return function(...args) {
            if (!lastRan) {
                func.apply(this, args);
                lastRan = Date.now();
            } else {
                clearTimeout(lastFunc);
                lastFunc = setTimeout(() => {
                    if ((Date.now() - lastRan) >= limit) {
                        func.apply(this, args);
                        lastRan = Date.now();
                    }
                }, limit - (Date.now() - lastRan));
            }
        };
    },
    
    // Check if device is iOS
    isIOS: function() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent);
    },
    
    // Check if device is Android
    isAndroid: function() {
        return /Android/.test(navigator.userAgent);
    },
    
    // Get device pixel ratio
    getPixelRatio: function() {
        return window.devicePixelRatio || 1;
    },
    
    // Smooth scroll to element
    scrollToElement: function(element, offset = 0) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            const elementPosition = element.offsetTop - offset;
            window.scrollTo({
                top: elementPosition,
                behavior: 'smooth'
            });
        }
    }
};

// Global utility functions
window.showMobileAlert = MobileApp.showAlert.bind(MobileApp);
window.showMobileLoading = MobileApp.showLoading.bind(MobileApp);
window.hideMobileLoading = MobileApp.hideLoading.bind(MobileApp);
window.mobileAnnounce = MobileApp.announce.bind(MobileApp);

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileApp;
}

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause any ongoing operations
        MobileApp.hideLoading();
    } else {
        // Page is visible, resume operations
        console.log('Page became visible');
    }
});

// Handle orientation changes
window.addEventListener('orientationchange', function() {
    // Wait for orientation change to complete
    setTimeout(() => {
        // Trigger resize events for any components that need it
        window.dispatchEvent(new Event('resize'));
    }, 100);
});

console.log('Mobile JavaScript loaded and ready');