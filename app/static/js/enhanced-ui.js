// Enhanced UI JavaScript for CellStorage
// Provides advanced animations, interactions, and UX improvements

class EnhancedUI {
    constructor() {
        this.init();
    }

    init() {
        this.setupScrollAnimations();
        this.setupNavbarScrollEffect();
        this.setupFormEnhancements();
        this.setupButtonEffects();
        this.setupTableEnhancements();
        this.setupLoadingStates();
        this.setupAccessibilityFeatures();
    }

    // Scroll-triggered animations
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    
                    // Add stagger effect for children
                    if (entry.target.classList.contains('stagger-fade-in')) {
                        const children = entry.target.children;
                        Array.from(children).forEach((child, index) => {
                            setTimeout(() => {
                                child.style.opacity = '1';
                                child.style.transform = 'translateY(0)';
                            }, index * 100);
                        });
                    }
                }
            });
        }, observerOptions);

        // Observe all elements with scroll-reveal class
        document.querySelectorAll('.scroll-reveal').forEach((element) => {
            observer.observe(element);
        });
    }

    // Navbar scroll effect
    setupNavbarScrollEffect() {
        const navbar = document.querySelector('.navbar-enhanced');
        if (!navbar) return;

        let lastScrollTop = 0;
        
        window.addEventListener('scroll', () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > 100) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
            
            // Hide/show navbar on scroll
            if (scrollTop > lastScrollTop && scrollTop > 200) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }
            
            lastScrollTop = scrollTop;
        });
    }

    // Enhanced form interactions
    setupFormEnhancements() {
        // Auto-focus first input in modals
        document.addEventListener('shown.bs.modal', (event) => {
            const firstInput = event.target.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });

        // Enhanced form validation feedback
        document.querySelectorAll('.form-control').forEach((input) => {
            input.addEventListener('blur', () => {
                this.validateInput(input);
            });

            input.addEventListener('input', () => {
                if (input.classList.contains('is-invalid')) {
                    this.validateInput(input);
                }
            });
        });

        // Floating label enhancements
        document.querySelectorAll('.form-floating-modern input, .form-floating-modern select').forEach((input) => {
            // Set initial state
            this.updateFloatingLabel(input);
            
            input.addEventListener('focus', () => {
                input.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', () => {
                input.parentElement.classList.remove('focused');
                this.updateFloatingLabel(input);
            });
            
            input.addEventListener('input', () => {
                this.updateFloatingLabel(input);
            });
        });
    }

    validateInput(input) {
        const isValid = input.checkValidity();
        input.classList.toggle('is-valid', isValid && input.value !== '');
        input.classList.toggle('is-invalid', !isValid);
        
        // Update floating label state
        this.updateFloatingLabel(input);
    }

    updateFloatingLabel(input) {
        const hasValue = input.value !== '';
        const isFocused = document.activeElement === input;
        const label = input.parentElement.querySelector('label');
        
        if (label) {
            if (hasValue || isFocused) {
                label.classList.add('floating');
            } else {
                label.classList.remove('floating');
            }
        }
    }

    // Enhanced button effects
    setupButtonEffects() {
        document.querySelectorAll('.btn-gradient-primary, .btn-gradient-secondary, .btn-gradient-success, .btn-gradient-warning, .btn-gradient-danger').forEach((button) => {
            button.addEventListener('click', (e) => {
                // Ripple effect
                this.createRipple(e);
                
                // Success animation for form submissions
                if (button.type === 'submit') {
                    this.handleFormSubmission(button);
                }
            });
        });
    }

    createRipple(event) {
        const button = event.currentTarget;
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            animation: ripple 0.6s ease-out;
            pointer-events: none;
        `;
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    handleFormSubmission(button) {
        const originalText = button.innerHTML;
        const loadingText = '<i class="bi bi-clock me-2"></i>Processing...';
        
        button.innerHTML = loadingText;
        button.disabled = true;
        button.classList.add('loading');
        
        // Reset after 3 seconds (in real implementation, this would be after actual submission)
        setTimeout(() => {
            button.innerHTML = '<i class="bi bi-check me-2"></i>Success!';
            button.classList.remove('loading');
            button.classList.add('success');
            
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
                button.classList.remove('success');
            }, 1500);
        }, 2000);
    }

    // Table enhancements
    setupTableEnhancements() {
        document.querySelectorAll('.table-modern tbody tr').forEach((row) => {
            row.addEventListener('click', () => {
                // Remove previous selections
                document.querySelectorAll('.table-modern tbody tr.selected').forEach((selectedRow) => {
                    selectedRow.classList.remove('selected');
                });
                
                // Add selection to clicked row
                row.classList.add('selected');
                
                // Emit custom event for row selection
                const event = new CustomEvent('rowSelected', {
                    detail: { row: row }
                });
                document.dispatchEvent(event);
            });
        });

        // Sortable headers
        document.querySelectorAll('.table-modern thead th[data-sortable]').forEach((header) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sortTable(header);
            });
        });
    }

    sortTable(header) {
        const table = header.closest('table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const columnIndex = Array.from(header.parentElement.children).indexOf(header);
        const isAscending = !header.classList.contains('sort-asc');
        
        // Clear previous sort indicators
        header.parentElement.querySelectorAll('th').forEach((th) => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Add sort indicator
        header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        
        // Sort rows
        rows.sort((a, b) => {
            const aText = a.children[columnIndex].textContent.trim();
            const bText = b.children[columnIndex].textContent.trim();
            
            if (isAscending) {
                return aText.localeCompare(bText, undefined, { numeric: true });
            } else {
                return bText.localeCompare(aText, undefined, { numeric: true });
            }
        });
        
        // Reorder rows
        rows.forEach((row) => {
            tbody.appendChild(row);
        });
    }

    // Loading states
    setupLoadingStates() {
        // Add loading indicators to buttons with data-loading attribute
        document.querySelectorAll('[data-loading]').forEach((element) => {
            element.addEventListener('click', () => {
                this.showLoadingState(element);
            });
        });
    }

    showLoadingState(element) {
        const originalContent = element.innerHTML;
        element.innerHTML = '<span class="loading-shimmer" style="width: 60px; height: 1em; display: inline-block;"></span>';
        element.disabled = true;
        
        // Simulate loading (replace with actual loading logic)
        setTimeout(() => {
            element.innerHTML = originalContent;
            element.disabled = false;
        }, 2000);
    }

    // Accessibility features
    setupAccessibilityFeatures() {
        // Enhanced focus management
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });

        // Skip link functionality
        const skipLink = document.querySelector('.skip-link');
        if (skipLink) {
            skipLink.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(skipLink.getAttribute('href'));
                if (target) {
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        }

        // Enhanced tooltips
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((element) => {
            new bootstrap.Tooltip(element, {
                placement: 'top',
                trigger: 'hover focus'
            });
        });
    }

    // Utility methods
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-enhanced alert-${type} alert-dismissible fade show position-fixed slide-in-right`;
        notification.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 280px;';
        notification.innerHTML = `
            <i class="bi bi-info-circle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }
        }, duration);
    }

    // Page transition effects
    setupPageTransitions() {
        // Add fade-in effect to page content
        const mainContent = document.querySelector('main');
        if (mainContent) {
            mainContent.style.opacity = '0';
            mainContent.style.transition = 'opacity 0.3s ease';
            
            window.addEventListener('load', () => {
                mainContent.style.opacity = '1';
            });
        }
    }
}

// Animation keyframes
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .keyboard-navigation *:focus {
        outline: 2px solid var(--primary-500) !important;
        outline-offset: 2px !important;
    }
    
    .table-modern tbody tr.selected {
        background: rgba(59, 130, 246, 0.1) !important;
        border-left: 4px solid var(--primary-500);
    }
    
    .table-modern th.sort-asc::after {
        content: ' ↑';
        color: var(--primary-500);
    }
    
    .table-modern th.sort-desc::after {
        content: ' ↓';  
        color: var(--primary-500);
    }
    
    .btn.loading {
        opacity: 0.7;
        cursor: not-allowed;
    }
    
    .btn.success {
        background: var(--success-gradient) !important;
        transform: scale(1.05);
    }
    
    .floating-label.floating {
        transform: translateY(-1.5rem) scale(0.85);
        color: var(--primary-600);
        font-weight: 600;
    }
    
    .form-floating-modern.focused .form-control {
        border-color: var(--primary-500);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
`;

document.head.appendChild(animationStyles);

// Initialize enhanced UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedUI = new EnhancedUI();
});

// Export for external use
window.EnhancedUI = EnhancedUI;