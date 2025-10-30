/**
 * Enhanced Storage Locations Management
 * Modern JavaScript for improved user experience
 */

class LocationManager {
    constructor() {
        this.expandedNodes = new Set();
        this.selectedLocation = null;
        this.currentView = 'split';
        this.capacityChart = null;
        
        this.init();
    }
    
    init() {
        this.initializeEventListeners();
        this.initializeLocationTree();
        this.initializeSearch();
        this.initializeFilters();
        this.initializeViewToggle();
        this.loadInitialAnimations();
    }
    
    initializeEventListeners() {
        // Tree node interactions
        $(document).on('click', '.location-toggle', this.handleToggleClick.bind(this));
        $(document).on('click', '.location-info', this.handleLocationSelect.bind(this));
        
        // Action button interactions
        $(document).on('click', '.btn-view', this.handleViewDetails.bind(this));
        $(document).on('click', '.btn-add', this.handleAddChild.bind(this));
        $(document).on('click', '.btn-edit', this.handleEditLocation.bind(this));
        $(document).on('click', '.btn-delete', this.handleDeleteLocation.bind(this));
        
        // Toolbar interactions
        $('#expandAllBtn').on('click', this.expandAll.bind(this));
        $('#collapseAllBtn').on('click', this.collapseAll.bind(this));
        $('#addLocationBtn').on('click', this.handleAddLocation.bind(this));
        
        // Details panel interactions
        $('#editLocationBtn').on('click', this.handleEditFromDetails.bind(this));
        $('#addChildBtn').on('click', this.handleAddChildFromDetails.bind(this));
        $('#deleteLocationBtn').on('click', this.handleDeleteFromDetails.bind(this));
    }
    
    initializeLocationTree() {
        $('.location-node').each((index, element) => {
            const $node = $(element);
            const hasChildren = $node.find('.location-children').length > 0;
            
            if (hasChildren) {
                $node.find('.location-children').hide();
            }
        });
    }
    
    initializeSearch() {
        let searchTimeout;
        $('#locationSearch').on('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });
    }
    
    initializeFilters() {
        $('#locationTypeFilter, #capacityFilter').on('change', () => {
            this.applyFilters();
        });
    }
    
    initializeViewToggle() {
        $('.view-toggle-btn').on('click', (e) => {
            const view = $(e.currentTarget).data('view');
            this.switchView(view);
        });
    }
    
    loadInitialAnimations() {
        // Add staggered animation delays
        $('.stat-card').each((index, element) => {
            $(element).css('animation-delay', `${index * 0.1}s`);
        });
        
        $('.location-node').each((index, element) => {
            $(element).css('animation-delay', `${index * 0.05}s`);
        });
    }
    
    handleToggleClick(e) {
        e.stopPropagation();
        const $toggle = $(e.currentTarget);
        const $node = $toggle.closest('.location-node');
        const $children = $node.find('> .location-children');
        const locationId = $node.data('location-id');
        
        if ($children.length > 0) {
            if ($children.is(':visible')) {
                this.collapseNode($node);
            } else {
                this.expandNode($node);
            }
        }
    }
    
    expandNode($node) {
        const $children = $node.find('> .location-children');
        const $toggle = $node.find('> .location-info .location-toggle i');
        const locationId = $node.data('location-id');
        
        $children.slideDown(300);
        $toggle.css('transform', 'rotate(90deg)');
        $node.addClass('expanded');
        this.expandedNodes.add(locationId);
    }
    
    collapseNode($node) {
        const $children = $node.find('> .location-children');
        const $toggle = $node.find('> .location-info .location-toggle i');
        const locationId = $node.data('location-id');
        
        $children.slideUp(300);
        $toggle.css('transform', 'rotate(0deg)');
        $node.removeClass('expanded');
        this.expandedNodes.delete(locationId);
    }
    
    handleLocationSelect(e) {
        e.stopPropagation();
        const $node = $(e.currentTarget).closest('.location-node');
        const locationId = $node.data('location-id');
        
        // Remove previous selection
        $('.location-node').removeClass('selected');
        
        // Add selection to current node
        $node.addClass('selected');
        
        // Load location details
        this.loadLocationDetails(locationId);
        this.selectedLocation = locationId;
    }
    
    loadLocationDetails(locationId) {
        // Show loading state
        this.showDetailsLoading();
        
        // Simulate API call (replace with actual endpoint)
        $.get(`/inventory/api/locations/${locationId}`)
            .done((data) => {
                this.renderLocationDetails(data);
            })
            .fail(() => {
                this.showDetailsError();
            });
    }
    
    showDetailsLoading() {
        $('#emptyState').hide();
        $('#detailsContent').show();
        $('#detailsActions').show();
        
        $('#detailsTitle').html('<i class="bi bi-hourglass-split me-2"></i>Loading...');
        $('#detailsSubtitle').text('Fetching location details...');
        
        $('#detailsContent').html(`
            <div class="details-section loading-skeleton" style="height: 200px;">
                <div class="loading-skeleton" style="height: 20px; margin-bottom: 10px;"></div>
                <div class="loading-skeleton" style="height: 20px; width: 80%; margin-bottom: 10px;"></div>
                <div class="loading-skeleton" style="height: 20px; width: 60%;"></div>
            </div>
        `);
    }
    
    showDetailsError() {
        $('#detailsContent').html(`
            <div class="details-empty-state">
                <div class="empty-state-icon" style="background: rgba(239, 68, 68, 0.1); color: #dc2626;">
                    <i class="bi bi-exclamation-triangle"></i>
                </div>
                <div class="empty-state-title">Error Loading Details</div>
                <div class="empty-state-description">
                    Unable to load location details. Please try again.
                </div>
            </div>
        `);
    }
    
    renderLocationDetails(location) {
        const capacityPercent = location.max_capacity ? 
            (location.current_usage / location.max_capacity * 100).toFixed(1) : 0;
        
        $('#detailsTitle').html(`
            <i class="bi bi-geo-alt me-2"></i>
            ${location.name}
        `);
        $('#detailsSubtitle').text(location.full_path);
        
        const detailsHtml = `
            <div class="details-section">
                <div class="details-section-title">
                    <i class="bi bi-info-circle me-2"></i>
                    Basic Information
                </div>
                <div class="details-grid">
                    <div class="detail-item">
                        <div class="detail-label">Name</div>
                        <div class="detail-value">${location.name}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Type</div>
                        <div class="detail-value">${location.location_type || 'N/A'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Temperature</div>
                        <div class="detail-value">${location.temperature || 'N/A'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Full Path</div>
                        <div class="detail-value">${location.full_path}</div>
                    </div>
                </div>
                ${location.description ? `
                    <div class="detail-item" style="margin-top: 16px;">
                        <div class="detail-label">Description</div>
                        <div class="detail-value">${location.description}</div>
                    </div>
                ` : ''}
            </div>
            
            <div class="details-section">
                <div class="details-section-title">
                    <i class="bi bi-pie-chart me-2"></i>
                    Capacity Information
                </div>
                <div class="details-grid">
                    <div class="detail-item">
                        <div class="detail-label">Max Capacity</div>
                        <div class="detail-value">${location.max_capacity || 'Unlimited'} ${location.capacity_unit || ''}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Current Usage</div>
                        <div class="detail-value">${location.current_usage}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Available Space</div>
                        <div class="detail-value">${location.max_capacity ? location.max_capacity - location.current_usage : 'Unlimited'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Utilization</div>
                        <div class="detail-value">${capacityPercent}%</div>
                    </div>
                </div>
                
                ${location.max_capacity ? `
                    <div class="capacity-chart-container">
                        <canvas id="capacityChart"></canvas>
                    </div>
                ` : ''}
            </div>
            
            <div class="details-section">
                <div class="details-section-title">
                    <i class="bi bi-box-seam me-2"></i>
                    Stored Items (${location.items ? location.items.length : 0})
                </div>
                <div class="details-items-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Item Name</th>
                                <th>Quantity</th>
                                <th>Status</th>
                                <th>Last Updated</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${location.items && location.items.length > 0 ? 
                                location.items.map(item => `
                                    <tr>
                                        <td>${item.name}</td>
                                        <td>${item.current_quantity} ${item.unit || ''}</td>
                                        <td><span class="status-badge ${this.getStatusClass(item.status)}">${item.status}</span></td>
                                        <td>${this.formatDate(item.updated_at)}</td>
                                    </tr>
                                `).join('') : 
                                '<tr><td colspan="4" style="text-align: center; color: #64748b;">No items stored in this location</td></tr>'
                            }
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        $('#detailsContent').html(detailsHtml);
        
        // Initialize capacity chart if needed
        if (location.max_capacity) {
            this.initializeCapacityChart(location);
        }
    }
    
    initializeCapacityChart(location) {
        const ctx = document.getElementById('capacityChart');
        if (!ctx) return;
        
        const capacityPercent = (location.current_usage / location.max_capacity * 100);
        const availablePercent = 100 - capacityPercent;
        
        if (this.capacityChart) {
            this.capacityChart.destroy();
        }
        
        this.capacityChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Available'],
                datasets: [{
                    data: [capacityPercent, availablePercent],
                    backgroundColor: [
                        this.getCapacityColor(capacityPercent),
                        '#e2e8f0'
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    }
                }
            }
        });
    }
    
    getCapacityColor(percent) {
        if (percent >= 100) return '#8b5cf6';
        if (percent >= 80) return '#ef4444';
        if (percent >= 60) return '#f59e0b';
        return '#10b981';
    }
    
    getStatusClass(status) {
        switch (status?.toLowerCase()) {
            case 'available': return 'available';
            case 'low stock': return 'low-stock';
            case 'expired': return 'expired';
            default: return 'available';
        }
    }
    
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }
    
    performSearch(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        
        $('.location-node').each((index, element) => {
            const $node = $(element);
            const locationName = $node.data('location-name')?.toLowerCase() || '';
            const locationType = $node.data('location-type')?.toLowerCase() || '';
            const fullPath = $node.data('full-path')?.toLowerCase() || '';
            
            const matches = !term || 
                locationName.includes(term) || 
                locationType.includes(term) || 
                fullPath.includes(term);
            
            $node.toggle(matches);
            
            // If a node matches, ensure its parents are visible
            if (matches) {
                $node.parents('.location-node').show();
            }
        });
        
        // Highlight search terms
        this.highlightSearchTerms(term);
    }
    
    highlightSearchTerms(term) {
        $('.location-name').each((index, element) => {
            const $element = $(element);
            const text = $element.text();
            
            if (term && text.toLowerCase().includes(term)) {
                const highlightedText = text.replace(
                    new RegExp(`(${term})`, 'gi'),
                    '<mark style="background: #fef08a; padding: 2px 4px; border-radius: 3px;">$1</mark>'
                );
                $element.html(highlightedText);
            } else {
                $element.text(text);
            }
        });
    }
    
    applyFilters() {
        const typeFilter = $('#locationTypeFilter').val();
        const capacityFilter = $('#capacityFilter').val();
        
        $('.location-node').each((index, element) => {
            const $node = $(element);
            const locationType = $node.data('location-type') || '';
            const capacityUsage = parseFloat($node.data('capacity-usage')) || 0;
            
            let showNode = true;
            
            // Type filter
            if (typeFilter && locationType !== typeFilter) {
                showNode = false;
            }
            
            // Capacity filter
            if (capacityFilter) {
                switch (capacityFilter) {
                    case 'available':
                        if (capacityUsage >= 80) showNode = false;
                        break;
                    case 'warning':
                        if (capacityUsage < 80 || capacityUsage >= 100) showNode = false;
                        break;
                    case 'full':
                        if (capacityUsage < 100) showNode = false;
                        break;
                }
            }
            
            $node.toggle(showNode);
        });
    }
    
    switchView(view) {
        $('.view-toggle-btn').removeClass('active');
        $(`.view-toggle-btn[data-view="${view}"]`).addClass('active');
        
        const $mainContent = $('#mainContent');
        
        switch (view) {
            case 'split':
                $mainContent.css('grid-template-columns', '400px 1fr');
                $('.location-tree-panel, .location-details-panel').show();
                break;
            case 'tree':
                $mainContent.css('grid-template-columns', '1fr');
                $('.location-tree-panel').show();
                $('.location-details-panel').hide();
                break;
            case 'list':
                // Implement list view
                this.switchToListView();
                break;
        }
        
        this.currentView = view;
    }
    
    switchToListView() {
        // Implementation for list view
        console.log('List view not yet implemented');
    }
    
    expandAll() {
        $('.location-node').each((index, element) => {
            const $node = $(element);
            if ($node.find('> .location-children').length > 0) {
                this.expandNode($node);
            }
        });
    }
    
    collapseAll() {
        $('.location-node').each((index, element) => {
            const $node = $(element);
            if ($node.find('> .location-children').length > 0) {
                this.collapseNode($node);
            }
        });
    }
    
    // Action handlers
    handleViewDetails(e) {
        e.stopPropagation();
        const locationId = $(e.currentTarget).data('location-id');
        this.loadLocationDetails(locationId);
    }
    
    handleAddChild(e) {
        e.stopPropagation();
        const locationId = $(e.currentTarget).data('location-id');
        window.location.href = `/inventory/locations/create?parent_id=${locationId}`;
    }
    
    handleEditLocation(e) {
        e.stopPropagation();
        const locationId = $(e.currentTarget).data('location-id');
        window.location.href = `/inventory/locations/${locationId}/edit`;
    }
    
    handleDeleteLocation(e) {
        e.stopPropagation();
        const locationId = $(e.currentTarget).data('location-id');
        
        if (confirm('Are you sure you want to delete this location? This action cannot be undone.')) {
            // Create form and submit via POST
            const form = $('<form>', {
                method: 'POST',
                action: `/inventory/locations/${locationId}/delete`
            });
            
            // Add CSRF token if available
            const csrfToken = $('meta[name="csrf-token"]').attr('content');
            if (csrfToken) {
                form.append($('<input>', {
                    type: 'hidden',
                    name: 'csrf_token',
                    value: csrfToken
                }));
            }
            
            // Submit form
            $('body').append(form);
            form.submit();
        }
    }
    
    handleAddLocation() {
        window.location.href = '/inventory/locations/create';
    }
    
    handleEditFromDetails() {
        if (this.selectedLocation) {
            window.location.href = `/inventory/locations/${this.selectedLocation}/edit`;
        }
    }
    
    handleAddChildFromDetails() {
        if (this.selectedLocation) {
            window.location.href = `/inventory/locations/create?parent_id=${this.selectedLocation}`;
        }
    }
    
    handleDeleteFromDetails() {
        if (this.selectedLocation) {
            if (confirm('Are you sure you want to delete this location? This action cannot be undone.')) {
                // Create form and submit via POST
                const form = $('<form>', {
                    method: 'POST',
                    action: `/inventory/locations/${this.selectedLocation}/delete`
                });
                
                // Add CSRF token if available
                const csrfToken = $('meta[name="csrf-token"]').attr('content');
                if (csrfToken) {
                    form.append($('<input>', {
                        type: 'hidden',
                        name: 'csrf_token',
                        value: csrfToken
                    }));
                }
                
                // Submit form
                $('body').append(form);
                form.submit();
            }
        }
    }
}

// Initialize when document is ready
$(document).ready(() => {
    window.locationManager = new LocationManager();
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LocationManager;
}