// Storage Location Management - Simplified Version
class StorageLocationManager {
    constructor() {
        this.selectedLocationId = null;
        this.locationToDelete = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.initModals();
        this.initKeyboardShortcuts();
        this.initTreeState();
        this.updateStorageStats();
    }

    bindEvents() {
        // Add Tower button
        const addTowerBtn = document.getElementById('addTowerBtn');
        if (addTowerBtn) {
            addTowerBtn.addEventListener('click', () => {
                this.addLocation(null, 'tower');
            });
        }

        // Confirm delete button
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => {
                this.confirmDelete();
            });
        }

        // Bind event delegation for tree interactions
        this.bindTreeEvents();
        
        // Bind quick action buttons
        this.bindQuickActions();
        
        // Bind details panel events
        this.bindDetailsEvents();
    }

    // Event delegation for tree interactions
    bindTreeEvents() {
        const storageTree = document.getElementById('storageTree');
        if (!storageTree) {
            console.warn('Storage tree element not found');
            return;
        }

        // Event delegation for all tree interactions
        storageTree.addEventListener('click', (e) => {
            const target = e.target;
            const closest = target.closest('[data-action]');
            
            if (closest) {
                e.preventDefault();
                e.stopPropagation();
                
                const action = closest.dataset.action;
                const locationId = closest.dataset.locationId;
                const locationType = closest.dataset.locationType;
                const locationName = closest.dataset.locationName;
                
                switch (action) {
                    case 'toggle':
                        this.toggleNode(closest);
                        break;
                    case 'select':
                        this.selectLocation(locationId);
                        break;
                    case 'add-drawer':
                        this.addLocation(locationId, 'drawer');
                        break;
                    case 'add-box':
                        this.addLocation(locationId, 'box');
                        break;
                    case 'edit':
                        this.editLocation(locationId, locationType);
                        break;
                    case 'delete':
                        this.deleteLocation(locationId, locationName, locationType);
                        break;
                }
            }
        });
        
        console.log('Tree events bound successfully');
    }

    // Bind quick action buttons
    bindQuickActions() {
        // Quick Add Tower
        const quickAddTower = document.getElementById('quickAddTower');
        if (quickAddTower) {
            quickAddTower.addEventListener('click', () => {
                this.addLocation(null, 'tower');
            });
        }

        // Quick View Items
        const quickViewItems = document.getElementById('quickViewItems');
        if (quickViewItems) {
            quickViewItems.addEventListener('click', () => {
                window.location.href = '/inventory';
            });
        }

        // Quick Expand All
        const quickExpandAll = document.getElementById('quickExpandAll');
        if (quickExpandAll) {
            quickExpandAll.addEventListener('click', () => {
                this.expandAll();
            });
        }

        // Quick Collapse All
        const quickCollapseAll = document.getElementById('quickCollapseAll');
        if (quickCollapseAll) {
            quickCollapseAll.addEventListener('click', () => {
                this.collapseAll();
            });
        }

        console.log('Quick actions bound successfully');
    }

    // Bind details panel events
    bindDetailsEvents() {
        const detailsPanel = document.querySelector('.details-panel');
        if (!detailsPanel) {
            console.warn('Details panel not found');
            return;
        }

        // Event delegation for details panel actions
        detailsPanel.addEventListener('click', (e) => {
            const target = e.target;
            const closest = target.closest('[data-action]');
            
            if (closest) {
                e.preventDefault();
                e.stopPropagation();
                
                const action = closest.dataset.action;
                const locationId = closest.dataset.locationId;
                const locationType = closest.dataset.locationType;
                const locationName = closest.dataset.locationName;
                
                switch (action) {
                    case 'edit-detail':
                        this.editLocation(locationId, locationType);
                        break;
                    case 'add-drawer-detail':
                        this.addLocation(locationId, 'drawer');
                        break;
                    case 'add-box-detail':
                        this.addLocation(locationId, 'box');
                        break;
                    case 'delete-detail':
                        this.deleteLocation(locationId, locationName, locationType);
                        break;
                }
            }
            
            // Handle back to overview button
            if (target.id === 'backToOverview' || target.closest('#backToOverview')) {
                this.resetToOverview();
            }
        });
        
        console.log('Details panel events bound successfully');
    }

    initModals() {
        try {
            const locationModalEl = document.getElementById('locationModal');
            const deleteModalEl = document.getElementById('deleteModal');
            
            if (typeof bootstrap === 'undefined') {
                console.error('Bootstrap is not loaded. Modals will not work.');
                return;
            }
            
            if (locationModalEl) {
                this.locationModal = new bootstrap.Modal(locationModalEl);
                console.log('Location modal initialized');
            } else {
                console.warn('Location modal element not found');
            }
            
            if (deleteModalEl) {
                this.deleteModal = new bootstrap.Modal(deleteModalEl);
                console.log('Delete modal initialized');
            } else {
                console.warn('Delete modal element not found');
            }
        } catch (error) {
            console.error('Error initializing modals:', error);
        }
    }

    // Toggle tree node expansion with animation
    toggleNode(toggleElement) {
        const node = toggleElement.closest('.tree-node');
        const children = node.querySelector('.node-children');
        const icon = toggleElement.querySelector('i');

        if (children) {
            const isExpanded = !children.classList.contains('collapsed');
            
            if (isExpanded) {
                // Collapse
                children.style.maxHeight = children.scrollHeight + 'px';
                children.offsetHeight; // Force reflow
                children.style.maxHeight = '0';
                children.classList.add('collapsed');
                if (icon) {
                    icon.className = 'bi bi-chevron-right';
                }
            } else {
                // Expand
                children.classList.remove('collapsed');
                children.style.maxHeight = children.scrollHeight + 'px';
                if (icon) {
                    icon.className = 'bi bi-chevron-down';
                }
                
                // Reset max-height after animation
                setTimeout(() => {
                    children.style.maxHeight = 'none';
                }, 300);
            }
            
            // Save tree state
            this.saveTreeState();
        }
    }

    // Select location and show details
    selectLocation(locationId) {
        // Remove previous selection
        document.querySelectorAll('.node-content.selected').forEach(node => {
            node.classList.remove('selected');
        });

        // Add selection to current node
        const selectedNode = document.querySelector(`[data-location-id="${locationId}"] .node-content`);
        if (selectedNode) {
            selectedNode.classList.add('selected');
        }

        // Get location type from the node
        const nodeElement = document.querySelector(`[data-location-id="${locationId}"]`);
        const locationType = nodeElement ? nodeElement.dataset.locationType : 'unknown';

        this.selectedLocationId = locationId;
        this.selectedLocationType = locationType;
        this.loadLocationDetails(locationId, locationType);
    }

    // Load location details - simplified for cell-storage
    async loadLocationDetails(locationId, locationType) {
        // For now, create mock data based on the DOM since cell-storage doesn't have detail API endpoints
        const selectedNode = document.querySelector(`[data-location-id="${locationId}"]`);
        if (!selectedNode) return;
        
        const nameElement = selectedNode.querySelector('.node-name');
        const name = nameElement ? nameElement.textContent : 'Unknown';
        
        const mockLocation = {
            id: locationId,
            name: name,
            type: locationType,
            description: '',
            capacity: locationType === 'box' ? this.getBoxCapacity(selectedNode) : null,
            current_items: locationType === 'box' ? this.getBoxCurrentItems(selectedNode) : null
        };
        
        this.displayLocationDetails(mockLocation);
    }
    
    // Helper method to get box capacity from DOM
    getBoxCapacity(boxNode) {
        const capacityText = boxNode.querySelector('.capacity-text');
        if (capacityText) {
            const match = capacityText.textContent.match(/\/(\d+)/);
            return match ? parseInt(match[1]) : 0;
        }
        return 0;
    }
    
    // Helper method to get box current items from DOM
    getBoxCurrentItems(boxNode) {
        const capacityText = boxNode.querySelector('.capacity-text');
        if (capacityText) {
            const match = capacityText.textContent.match(/(\d+)\//);
            return match ? parseInt(match[1]) : 0;
        }
        return 0;
    }

    // Display location details in right panel
    displayLocationDetails(location) {
        const detailsTitle = document.getElementById('detailsTitle');
        const emptyState = document.getElementById('detailsEmptyState');
        const detailsForm = document.getElementById('detailsForm');

        if (!detailsTitle || !emptyState || !detailsForm) return;

        // Update title
        const typeIcon = this.getTypeIcon(location.type);
        detailsTitle.innerHTML = `${typeIcon} ${location.name}`;

        // Hide empty state and show form
        emptyState.style.display = 'none';
        detailsForm.style.display = 'block';

        // Populate form
        detailsForm.innerHTML = this.generateDetailsForm(location);
    }

    // Reset to overview when no location is selected
    resetToOverview() {
        const detailsTitle = document.getElementById('detailsTitle');
        const emptyState = document.getElementById('detailsEmptyState');
        const detailsForm = document.getElementById('detailsForm');

        if (!detailsTitle || !emptyState || !detailsForm) return;

        // Reset title
        detailsTitle.innerHTML = `
            <i class="bi bi-pie-chart"></i>
            Storage Overview
        `;

        // Show empty state and hide form
        emptyState.style.display = 'block';
        detailsForm.style.display = 'none';

        // Update statistics
        this.updateStorageStats();
    }

    // Generate details form HTML
    generateDetailsForm(location) {
        const capacitySection = location.type !== 'tower' ? `
            <div class="form-group">
                <label class="form-label">Capacity</label>
                <div class="capacity-display">
                    <span class="capacity-current">${location.current_items || 0}</span>
                    <span class="capacity-separator">/</span>
                    <span class="capacity-total">${location.capacity || 'Unlimited'}</span>
                </div>
                <div class="capacity-bar">
                    <div class="capacity-fill" style="width: ${this.calculateCapacityPercentage(location)}%"></div>
                </div>
            </div>
        ` : '';

        return `
            <div class="form-group">
                <label class="form-label">Name</label>
                <div class="form-display">${location.name}</div>
            </div>
            
            <div class="form-group">
                <label class="form-label">Type</label>
                <div class="form-display">
                    ${this.getTypeIcon(location.type)} ${this.capitalizeFirst(location.type)}
                </div>
            </div>
            
            ${location.description ? `
                <div class="form-group">
                    <label class="form-label">Description</label>
                    <div class="form-display">${location.description}</div>
                </div>
            ` : ''}
            
            ${capacitySection}
            
            <div class="form-group">
                <label class="form-label">Actions</label>
                <div class="action-buttons">
                    <button class="btn-secondary" id="backToOverview">
                        <i class="bi bi-arrow-left"></i> Back to Overview
                    </button>
                    <button class="btn-primary" data-action="edit-detail" data-location-id="${location.id}" data-location-type="${location.type}">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    ${location.type === 'tower' ? `
                        <button class="btn-primary" data-action="add-drawer-detail" data-location-id="${location.id}">
                            <i class="bi bi-plus"></i> Add Drawer
                        </button>
                    ` : ''}
                    ${location.type === 'drawer' ? `
                        <button class="btn-primary" data-action="add-box-detail" data-location-id="${location.id}">
                            <i class="bi bi-plus"></i> Add Box
                        </button>
                    ` : ''}
                    <button class="btn-danger" data-action="delete-detail" data-location-id="${location.id}" data-location-name="${location.name}" data-location-type="${location.type}">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </div>
        `;
    }

    // Add new location - redirect to existing cell-storage forms
    addLocation(parentId, type) {
        let url;
        switch(type) {
            case 'tower':
                url = '/cell-storage/tower/add';
                break;
            case 'drawer':
                url = `/cell-storage/drawer/add?tower_id=${parentId}`;
                break;
            case 'box':
                url = `/cell-storage/box/add?drawer_id=${parentId}`;
                break;
            default:
                this.showError('Unknown location type');
                return;
        }
        window.location.href = url;
    }

    // Edit existing location - redirect to existing cell-storage forms
    editLocation(locationId, locationType) {
        let url;
        switch(locationType) {
            case 'tower':
                url = `/cell-storage/tower/${locationId}/edit`;
                break;
            case 'drawer':
                url = `/cell-storage/drawer/${locationId}/edit`;
                break;
            case 'box':
                url = `/cell-storage/box/${locationId}/edit`;
                break;
            default:
                this.showError('Unknown location type');
                return;
        }
        window.location.href = url;
    }

    // Save location (add or edit) with validation
    async saveLocation() {
        const form = document.getElementById('locationForm');
        if (!form) return;

        const formData = new FormData(form);
        
        // Validate form data
        const validation = this.validateForm(formData);
        if (!validation.valid) {
            this.showError(validation.message);
            return;
        }

        const locationId = formData.get('id');
        const url = locationId ? 
            `/inventory/locations/${locationId}/edit` : 
            '/inventory/locations/add';

        // Show loading state
        const saveBtn = document.getElementById('saveLocationBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';
        saveBtn.disabled = true;

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                if (this.locationModal) {
                    this.locationModal.hide();
                }
                this.showSuccess(data.message || 'Location saved successfully');
                this.saveTreeState();
                // Reload the page to refresh the tree
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showError(data.message || 'Failed to save location');
            }
        } catch (error) {
            console.error('Error saving location:', error);
            this.showError('Error saving location');
        } finally {
            // Restore button state
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        }
    }

    // Delete location
    deleteLocation(locationId, locationName, locationType) {
        const deleteLocationName = document.getElementById('deleteLocationName');
        const deleteWarning = document.getElementById('deleteWarning');
        
        if (deleteLocationName) {
            deleteLocationName.textContent = locationName;
        }
        
        if (deleteWarning) {
            deleteWarning.textContent = 'This will also delete all child locations and their contents.';
        }
        
        // Store location ID and type for confirmation
        this.locationToDelete = locationId;
        this.locationTypeToDelete = locationType;
        
        if (this.deleteModal) {
            this.deleteModal.show();
        }
    }

    // Confirm delete - redirect to cell-storage delete endpoints
    async confirmDelete() {
        if (!this.locationToDelete || !this.locationTypeToDelete) return;

        let url;
        switch(this.locationTypeToDelete) {
            case 'tower':
                url = `/cell-storage/tower/${this.locationToDelete}/delete`;
                break;
            case 'drawer':
                url = `/cell-storage/drawer/${this.locationToDelete}/delete`;
                break;
            case 'box':
                url = `/cell-storage/box/${this.locationToDelete}/delete`;
                break;
            default:
                this.showError('Unknown location type');
                return;
        }

        // Hide modal and redirect
        if (this.deleteModal) {
            this.deleteModal.hide();
        }
        
        // Create a form and submit it for POST request
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = url;
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name=csrf-token]');
        if (csrfToken) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            csrfInput.value = csrfToken.getAttribute('content');
            form.appendChild(csrfInput);
        }
        
        document.body.appendChild(form);
        form.submit();

        this.locationToDelete = null;
        this.locationTypeToDelete = null;
    }

    // Helper methods
    getTypeIcon(type) {
        switch (type) {
            case 'tower':
                return '<i class="bi bi-building text-primary"></i>';
            case 'drawer':
                return '<i class="bi bi-inbox text-success"></i>';
            case 'box':
                return '<i class="bi bi-box text-warning"></i>';
            default:
                return '<i class="bi bi-question-circle"></i>';
        }
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    calculateCapacityPercentage(location) {
        if (!location.capacity || location.capacity === 0) return 0;
        return Math.min(100, ((location.current_items || 0) / location.capacity) * 100);
    }

    showSuccess(message) {
        // Simple alert for now - can be replaced with toast notifications
        alert('Success: ' + message);
    }

    showError(message) {
        // Simple alert for now - can be replaced with toast notifications
        alert('Error: ' + message);
    }

    // Initialize keyboard shortcuts
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + N: Add new tower
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                this.addLocation(null, 'tower');
            }
            
            // Delete key: Delete selected location
            if (e.key === 'Delete' && this.selectedLocationId) {
                const selectedNode = document.querySelector(`[data-location-id="${this.selectedLocationId}"]`);
                if (selectedNode) {
                    const locationName = selectedNode.querySelector('.node-name').textContent;
                    const locationType = selectedNode.dataset.locationType;
                    this.deleteLocation(this.selectedLocationId, locationName, locationType);
                }
            }
            
            // Escape key: Close modals
            if (e.key === 'Escape') {
                if (this.locationModal && this.locationModal._isShown) {
                    this.locationModal.hide();
                }
                if (this.deleteModal && this.deleteModal._isShown) {
                    this.deleteModal.hide();
                }
            }
        });
    }

    // Initialize tree state (expand/collapse memory)
    initTreeState() {
        try {
            // First, set all nodes to collapsed by default
            document.querySelectorAll('.node-children').forEach(children => {
                children.classList.add('collapsed');
                children.style.maxHeight = '0';
            });
            document.querySelectorAll('.node-toggle i').forEach(icon => {
                if (icon.classList.contains('bi-chevron-down')) {
                    icon.className = 'bi bi-chevron-right';
                }
            });
            
            // Then restore expanded state from localStorage (if user had previously expanded some nodes)
            const expandedNodes = JSON.parse(localStorage.getItem('expandedNodes') || '[]');
            console.log('Restoring expanded nodes:', expandedNodes);
            
            expandedNodes.forEach(nodeId => {
                const node = document.querySelector(`[data-location-id="${nodeId}"]`);
                if (node) {
                    const children = node.querySelector('.node-children');
                    const toggle = node.querySelector('.node-toggle');
                    if (children && toggle) {
                        children.classList.remove('collapsed');
                        children.style.maxHeight = 'none';
                        const icon = toggle.querySelector('i');
                        if (icon) {
                            icon.className = 'bi bi-chevron-down';
                        }
                    }
                }
            });
            
            console.log('Tree state initialized - default collapsed with restored expansions');
        } catch (error) {
            console.error('Error initializing tree state:', error);
        }
    }

    // Save tree state
    saveTreeState() {
        const expandedNodes = [];
        document.querySelectorAll('.tree-node').forEach(node => {
            const children = node.querySelector('.node-children');
            if (children && !children.classList.contains('collapsed')) {
                expandedNodes.push(node.dataset.locationId);
            }
        });
        localStorage.setItem('expandedNodes', JSON.stringify(expandedNodes));
    }

    // Expand all nodes
    expandAll() {
        document.querySelectorAll('.node-children').forEach(children => {
            children.classList.remove('collapsed');
            children.style.maxHeight = 'none';
        });
        document.querySelectorAll('.node-toggle i').forEach(icon => {
            icon.className = 'bi bi-chevron-down';
        });
        this.saveTreeState();
    }

    // Collapse all nodes
    collapseAll() {
        document.querySelectorAll('.node-children').forEach(children => {
            children.classList.add('collapsed');
            children.style.maxHeight = '0';
        });
        document.querySelectorAll('.node-toggle i').forEach(icon => {
            icon.className = 'bi bi-chevron-right';
        });
        this.saveTreeState();
    }

    // Enhanced form validation
    validateForm(formData) {
        const name = formData.get('name');
        const type = formData.get('type');
        const capacity = formData.get('capacity');

        if (!name || name.trim().length === 0) {
            return { valid: false, message: 'Name is required' };
        }

        if (name.trim().length > 50) {
            return { valid: false, message: 'Name must be less than 50 characters' };
        }

        if (type !== 'tower' && capacity && parseInt(capacity) <= 0) {
            return { valid: false, message: 'Capacity must be a positive number' };
        }

        return { valid: true };
    }

    // Update storage statistics in the right panel
    updateStorageStats() {
        try {
            const stats = this.calculateStorageStats();
            console.log('Storage stats calculated:', stats);
            
            // Update counts
            const towerCountEl = document.getElementById('towerCount');
            const drawerCountEl = document.getElementById('drawerCount');
            const boxCountEl = document.getElementById('boxCount');
            const totalUsedEl = document.getElementById('totalUsed');
            const totalCapacityEl = document.getElementById('totalCapacity');
            const capacityBarEl = document.getElementById('overallCapacityBar');
            const capacityPercentageEl = document.getElementById('capacityPercentage');
            
            if (towerCountEl) towerCountEl.textContent = stats.towers;
            if (drawerCountEl) drawerCountEl.textContent = stats.drawers;
            if (boxCountEl) boxCountEl.textContent = stats.boxes;
            if (totalUsedEl) totalUsedEl.textContent = stats.totalUsed;
            if (totalCapacityEl) totalCapacityEl.textContent = stats.totalCapacity;
            
            const percentage = stats.totalCapacity > 0 ? 
                Math.round((stats.totalUsed / stats.totalCapacity) * 100) : 0;
            
            if (capacityBarEl) {
                capacityBarEl.style.width = percentage + '%';
                
                // Update capacity bar color based on usage
                if (percentage >= 90) {
                    capacityBarEl.style.backgroundColor = '#dc3545';
                } else if (percentage >= 80) {
                    capacityBarEl.style.backgroundColor = '#ffc107';
                } else {
                    capacityBarEl.style.backgroundColor = '#28a745';
                }
            }
            
            if (capacityPercentageEl) {
                capacityPercentageEl.textContent = percentage + '% full';
            }
            
            console.log('Storage stats updated successfully');
        } catch (error) {
            console.error('Error updating storage stats:', error);
        }
    }

    // Calculate storage statistics from the DOM
    calculateStorageStats() {
        const towers = document.querySelectorAll('[data-location-type="tower"]').length;
        const drawers = document.querySelectorAll('[data-location-type="drawer"]').length;
        const boxes = document.querySelectorAll('[data-location-type="box"]').length;
        
        let totalUsed = 0;
        let totalCapacity = 0;
        
        // Calculate total capacity and usage from boxes
        document.querySelectorAll('[data-location-type="box"]').forEach(box => {
            const capacityText = box.querySelector('.capacity-text');
            if (capacityText) {
                const match = capacityText.textContent.match(/(\d+)\/(\d+)/);
                if (match) {
                    totalUsed += parseInt(match[1]);
                    totalCapacity += parseInt(match[2]);
                }
            }
        });
        
        return {
            towers,
            drawers,
            boxes,
            totalUsed,
            totalCapacity
        };
    }
}

// Global functions for template usage
function toggleNode(element) {
    try {
        if (window.storageManager) {
            window.storageManager.toggleNode(element);
        } else {
            console.error('StorageManager not initialized');
        }
    } catch (error) {
        console.error('Error in toggleNode:', error);
    }
}

function selectLocation(locationId) {
    try {
        if (window.storageManager) {
            window.storageManager.selectLocation(locationId);
        } else {
            console.error('StorageManager not initialized');
        }
    } catch (error) {
        console.error('Error in selectLocation:', error);
    }
}

function addLocation(parentId, type) {
    try {
        if (window.storageManager) {
            window.storageManager.addLocation(parentId, type);
        } else {
            console.error('StorageManager not initialized');
        }
    } catch (error) {
        console.error('Error in addLocation:', error);
    }
}

function editLocation(locationId, locationType) {
    try {
        if (window.storageManager) {
            window.storageManager.editLocation(locationId, locationType);
        } else {
            console.error('StorageManager not initialized');
        }
    } catch (error) {
        console.error('Error in editLocation:', error);
    }
}

function deleteLocation(locationId, locationName, locationType) {
    try {
        if (window.storageManager) {
            window.storageManager.deleteLocation(locationId, locationName, locationType);
        } else {
            console.error('StorageManager not initialized');
        }
    } catch (error) {
        console.error('Error in deleteLocation:', error);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    try {
        console.log('Initializing Storage Location Manager...');
        window.storageManager = new StorageLocationManager();
        console.log('Storage Location Manager initialized successfully');
    } catch (error) {
        console.error('Failed to initialize Storage Location Manager:', error);
    }
});