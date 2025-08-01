class MobileCryoVialApp {
    constructor() {
        this.currentTab = 'search';
        this.selectedBatches = new Set();
        this.pickupList = [];
        this.currentLocation = null;
        this.locationHierarchy = [];
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        this.init();
    }

    getCSRFHeaders() {
        return this.csrfToken ? { 'X-CSRFToken': this.csrfToken } : {};
    }

    async init() {
        this.setupEventListeners();
        await this.loadFormOptions();
        this.switchTab('search');
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Search functionality
        const searchBtn = document.getElementById('search-btn');
        const viewAllBtn = document.getElementById('view-all-btn');
        const clearBtn = document.getElementById('clear-btn');
        
        if (searchBtn) searchBtn.addEventListener('click', () => this.performSearch());
        if (viewAllBtn) viewAllBtn.addEventListener('click', () => this.viewAll());
        if (clearBtn) clearBtn.addEventListener('click', () => this.clearSearch());

        // Add to pickup list button
        const addToPickupBtn = document.getElementById('add-to-pickup-btn');
        if (addToPickupBtn) {
            addToPickupBtn.addEventListener('click', () => this.addSelectedToPickup());
        }

        // Add new vial form
        const addVialForm = document.getElementById('add-vial-form');
        if (addVialForm) {
            addVialForm.addEventListener('submit', (e) => this.handleAddVial(e));
        }

        // Reset form button
        const resetFormBtn = document.getElementById('reset-form-btn');
        if (resetFormBtn) {
            resetFormBtn.addEventListener('click', () => this.resetForm());
        }

        // Search input enter key event
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }

        // Filter change events
        const creatorFilter = document.getElementById('creator-filter');
        const fluorescenceFilter = document.getElementById('fluorescence-filter');
        const resistanceFilter = document.getElementById('resistance-filter');
        
        if (creatorFilter) creatorFilter.addEventListener('change', () => this.applyFilters());
        if (fluorescenceFilter) fluorescenceFilter.addEventListener('change', () => this.applyFilters());
        if (resistanceFilter) resistanceFilter.addEventListener('change', () => this.applyFilters());

        // Location selection cascade
        const towerSelect = document.getElementById('tower-select');
        const drawerSelect = document.getElementById('drawer-select');
        const boxSelect = document.getElementById('box-select');
        
        if (towerSelect) towerSelect.addEventListener('change', () => this.loadDrawers());
        if (drawerSelect) drawerSelect.addEventListener('change', () => this.loadBoxes());
        if (boxSelect) boxSelect.addEventListener('change', () => this.loadPositions());

        // Modal close
        const closeBtn = document.querySelector('.close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }
    }

    switchTab(tabName) {
        // Update tab button state
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }

        // Show corresponding content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        const activeTab = document.getElementById(`${tabName}-tab`);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        this.currentTab = tabName;

        // Load data based on active tab
        if (tabName === 'browse') {
            this.loadInventoryData();
        } else if (tabName === 'pickup') {
            this.updatePickupList();
        } else if (tabName === 'add') {
            this.loadFormOptions();
            this.loadLocationHierarchy();
        }
    }

    async loadFormOptions() {
        try {
            const response = await fetch('/cell-storage/mobile/api/filter-options');
            const data = await response.json();
            
            // Fill creator filter options
            const creatorFilter = document.getElementById('creator-filter');
            if (creatorFilter && data.data.creators && Array.isArray(data.data.creators)) {
                creatorFilter.innerHTML = '<option value="">All Creators</option>';
                data.data.creators.forEach(creator => {
                    creatorFilter.innerHTML += `<option value="${creator}">${creator}</option>`;
                });
            }
            
            // Fill fluorescence tag filter options
            const fluorescenceFilter = document.getElementById('fluorescence-filter');
            if (fluorescenceFilter && data.data.fluorescence_tags && Array.isArray(data.data.fluorescence_tags)) {
                fluorescenceFilter.innerHTML = '<option value="">All Fluorescence</option>';
                data.data.fluorescence_tags.forEach(tag => {
                    fluorescenceFilter.innerHTML += `<option value="${tag}">${tag}</option>`;
                });
            }
            
            // Fill resistance filter options
            const resistanceFilter = document.getElementById('resistance-filter');
            if (resistanceFilter && data.data.resistances && Array.isArray(data.data.resistances)) {
                resistanceFilter.innerHTML = '<option value="">All Resistances</option>';
                data.data.resistances.forEach(resistance => {
                    resistanceFilter.innerHTML += `<option value="${resistance}">${resistance}</option>`;
                });
            }
            
            // Fill cell line options (this will be loaded separately from form-options endpoint)
            await this.loadFormOptionsForAdd();
            
        } catch (error) {
            console.error('Error loading form options:', error);
        }
    }

    async loadFormOptionsForAdd() {
        try {
            const response = await fetch('/cell-storage/mobile/api/form-options');
            const data = await response.json();
            
            if (data.success && data.data) {
                // Fill cell line options
                const cellLineSelect = document.getElementById('cell-line-select');
                if (cellLineSelect && data.data.cell_lines && Array.isArray(data.data.cell_lines)) {
                    cellLineSelect.innerHTML = '<option value="">Select Cell Line</option>';
                    data.data.cell_lines.forEach(cellLine => {
                        cellLineSelect.innerHTML += `<option value="${cellLine.id}">${cellLine.name}</option>`;
                    });
                }
                
                // Cache location hierarchy and fill tower select
                if (data.data.locations && Array.isArray(data.data.locations)) {
                    this.locationHierarchy = data.data.locations;
                    const towerSelect = document.getElementById('tower-select');
                    if (towerSelect) {
                        towerSelect.innerHTML = '<option value="">Select Tower</option>';
                        data.data.locations.forEach(tower => {
                            towerSelect.innerHTML += `<option value="${tower.id}">${tower.name}</option>`;
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Error loading form options for add:', error);
        }
    }

    async loadLocationHierarchy() {
        // This method is now integrated into loadFormOptionsForAdd
        await this.loadFormOptionsForAdd();
    }

    async loadDrawers() {
        const towerSelect = document.getElementById('tower-select');
        const drawerSelect = document.getElementById('drawer-select');
        const boxSelect = document.getElementById('box-select');
        
        if (!towerSelect || !drawerSelect || !boxSelect) return;
        
        const towerId = towerSelect.value;
        
        // Reset child selections
        drawerSelect.innerHTML = '<option value="">Select Drawer</option>';
        boxSelect.innerHTML = '<option value="">Select Box</option>';
        drawerSelect.disabled = !towerId;
        boxSelect.disabled = true;
        
        // Clear position grid
        const positionGrid = document.getElementById('position-grid');
        if (positionGrid) {
            positionGrid.style.display = 'none';
            positionGrid.innerHTML = '';
        }
        
        if (!towerId) return;
        
        // Find the selected tower from the cached location data
        if (this.locationHierarchy) {
            const selectedTower = this.locationHierarchy.find(tower => tower.id == towerId);
            if (selectedTower && selectedTower.drawers) {
                selectedTower.drawers.forEach(drawer => {
                    drawerSelect.innerHTML += `<option value="${drawer.id}">${drawer.name}</option>`;
                });
                drawerSelect.disabled = false;
            }
        }
    }

    async loadBoxes() {
        const towerSelect = document.getElementById('tower-select');
        const drawerSelect = document.getElementById('drawer-select');
        const boxSelect = document.getElementById('box-select');
        
        if (!towerSelect || !drawerSelect || !boxSelect) return;
        
        const towerId = towerSelect.value;
        const drawerId = drawerSelect.value;
        
        // Reset child selections
        boxSelect.innerHTML = '<option value="">Select Box</option>';
        boxSelect.disabled = !drawerId;
        
        // Clear position grid
        const positionGrid = document.getElementById('position-grid');
        if (positionGrid) {
            positionGrid.style.display = 'none';
            positionGrid.innerHTML = '';
        }
        
        if (!drawerId || !towerId) return;
        
        // Find the selected drawer from the cached location data
        if (this.locationHierarchy) {
            const selectedTower = this.locationHierarchy.find(tower => tower.id == towerId);
            if (selectedTower && selectedTower.drawers) {
                const selectedDrawer = selectedTower.drawers.find(drawer => drawer.id == drawerId);
                if (selectedDrawer && selectedDrawer.boxes) {
                    selectedDrawer.boxes.forEach(box => {
                        boxSelect.innerHTML += `<option value="${box.id}">${box.name}</option>`;
                    });
                    boxSelect.disabled = false;
                }
            }
        }
    }

    async loadPositions() {
        const towerSelect = document.getElementById('tower-select');
        const drawerSelect = document.getElementById('drawer-select');
        const boxSelect = document.getElementById('box-select');
        const positionGrid = document.getElementById('position-grid');
        const positionInfo = document.getElementById('position-info');
        
        if (!towerSelect || !drawerSelect || !boxSelect || !positionGrid || !positionInfo) return;
        
        const towerId = towerSelect.value;
        const drawerId = drawerSelect.value;
        const boxId = boxSelect.value;
        
        if (!boxId || !drawerId || !towerId) {
            positionGrid.style.display = 'none';
            positionInfo.textContent = 'Select a box to see available positions';
            return;
        }
        
        // Find the selected box from the cached location data
        if (this.locationHierarchy) {
            const selectedTower = this.locationHierarchy.find(tower => tower.id == towerId);
            if (selectedTower && selectedTower.drawers) {
                const selectedDrawer = selectedTower.drawers.find(drawer => drawer.id == drawerId);
                if (selectedDrawer && selectedDrawer.boxes) {
                    const selectedBox = selectedDrawer.boxes.find(box => box.id == boxId);
                    if (selectedBox) {
                        this.displayPositionGrid(selectedBox);
                        positionGrid.style.display = 'grid';
                        positionInfo.textContent = `Available positions in ${selectedBox.name}:`;
                    }
                }
            }
        }
    }

    displayPositionGrid(boxData) {
        const positionGrid = document.getElementById('position-grid');
        if (!positionGrid) return;
        
        const { rows, columns, available_positions } = boxData;
        
        positionGrid.innerHTML = '';
        positionGrid.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
        
        for (let row = 1; row <= rows; row++) {
            for (let col = 1; col <= columns; col++) {
                const isAvailable = available_positions.some(pos => pos.row === row && pos.col === col);
                const cell = document.createElement('div');
                cell.className = `position-cell ${isAvailable ? 'available' : 'occupied'}`;
                cell.textContent = `${row}-${col}`;
                
                if (isAvailable) {
                    cell.addEventListener('click', () => this.selectPosition(row, col, cell));
                    cell.title = 'Click to select this position';
                } else {
                    cell.title = 'Position occupied';
                }
                
                positionGrid.appendChild(cell);
            }
        }
    }

    selectPosition(row, col, cellElement) {
        // Remove previous selection
        document.querySelectorAll('.position-cell.selected').forEach(cell => {
            cell.classList.remove('selected');
        });
        
        // Select current position
        cellElement.classList.add('selected');
        
        // Set hidden field values
        const selectedRow = document.getElementById('selected-row');
        const selectedCol = document.getElementById('selected-col');
        
        if (selectedRow) selectedRow.value = row;
        if (selectedCol) selectedCol.value = col;
    }

    async performSearch() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;
        
        const searchTerm = searchInput.value.trim();
        
        const creatorFilter = document.getElementById('creator-filter');
        const fluorescenceFilter = document.getElementById('fluorescence-filter');
        const resistanceFilter = document.getElementById('resistance-filter');
        
        const params = new URLSearchParams();
        if (searchTerm) params.append('q', searchTerm);
        if (creatorFilter && creatorFilter.value) params.append('creator', creatorFilter.value);
        if (fluorescenceFilter && fluorescenceFilter.value) params.append('fluorescence', fluorescenceFilter.value);
        if (resistanceFilter && resistanceFilter.value) params.append('resistance', resistanceFilter.value);

        try {
            const response = await fetch(`/cell-storage/mobile/api/search-vials?${params.toString()}`);
            const data = await response.json();
            if (data.success) {
                this.displaySearchResults(data.data || []);
            } else {
                alert('Search failed: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Search error:', error);
            alert('Search failed, please try again');
        }
    }

    async viewAll() {
        try {
            const response = await fetch('/cell-storage/mobile/api/search-vials?view_all=true');
            const data = await response.json();
            if (data.success) {
                this.displaySearchResults(data.data || []);
            } else {
                alert('Load failed: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('View all error:', error);
            alert('Load failed, please try again');
        }
    }

    async applyFilters() {
        // This is now integrated into performSearch
        this.performSearch();
    }

    clearSearch() {
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        
        if (searchInput) searchInput.value = '';
        if (searchResults) {
            searchResults.innerHTML = '<div class="empty-state">Please enter search criteria or click "View All" to browse samples</div>';
        }
        
        this.selectedBatches.clear();
        this.updateSelectionButtons();
    }

    displaySearchResults(results) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;
        
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-state">No matching samples found</div>';
            return;
        }

        resultsContainer.innerHTML = results.map(batch => `
            <div class="vial-card" data-batch-id="${batch.batch_id}">
                <div class="vial-header">
                    <input type="checkbox" class="batch-checkbox" data-batch-id="${batch.batch_id}">
                    <h3>${batch.batch_name || 'N/A'}</h3>
                    <span class="quantity-badge">${batch.available_quantity || 0} available</span>
                </div>
                <div class="vial-info">
                    <div class="info-row">
                        <span class="label">Cell Line:</span>
                        <span class="value">${batch.cell_line || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Passage:</span>
                        <span class="value">${batch.passage_number || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Date Frozen:</span>
                        <span class="value">${batch.date_frozen || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Volume:</span>
                        <span class="value">${batch.volume_ml || 'N/A'} ml</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Concentration:</span>
                        <span class="value">${batch.concentration || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Fluorescence:</span>
                        <span class="value">${batch.fluorescence_tag || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Resistance:</span>
                        <span class="value">${batch.resistance || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `).join('');

        // Add checkbox event listeners
        document.querySelectorAll('.batch-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const batchId = parseInt(e.target.dataset.batchId);
                if (e.target.checked) {
                    this.selectedBatches.add(batchId);
                } else {
                    this.selectedBatches.delete(batchId);
                }
                this.updateSelectionButtons();
            });
        });
    }

    updateSelectionButtons() {
        const addToPickupBtn = document.getElementById('add-to-pickup-btn');
        if (addToPickupBtn) {
            const hasSelection = this.selectedBatches.size > 0;
            addToPickupBtn.style.display = hasSelection ? 'block' : 'none';
        }
    }

    async addSelectedToPickup() {
        if (this.selectedBatches.size === 0) {
            alert('Please select samples first');
            return;
        }

        const selectedBatchIds = Array.from(this.selectedBatches);
        
        try {
            const response = await fetch('/cell-storage/mobile/api/pickup-list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getCSRFHeaders()
                },
                body: JSON.stringify({ selected_batches: selectedBatchIds })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Update local pickup list
                selectedBatchIds.forEach(batchId => {
                    if (!this.pickupList.find(item => item.batch_id === batchId)) {
                        // Find corresponding batch info from current display
                        const vialCard = document.querySelector(`[data-batch-id="${batchId}"]`);
                        if (vialCard) {
                            const batchName = vialCard.querySelector('h3').textContent;
                            
                            this.pickupList.push({
                                batch_id: batchId,
                                batch_name: batchName,
                                addedAt: new Date().toLocaleString()
                            });
                        }
                    }
                });

                this.updatePickupList();
                this.selectedBatches.clear();
                this.updateSelectionButtons();
                
                // Clear checkbox selections
                document.querySelectorAll('.batch-checkbox').forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Switch to pickup list tab
                this.switchTab('pickup');
                
                alert(`Added ${selectedBatchIds.length} batches to pickup list`);
            } else {
                alert('Failed to add to pickup list: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error adding to pickup list:', error);
            alert('Failed to add to pickup list');
        }
    }

    async updatePickupList() {
        const pickupContainer = document.getElementById('pickup-content');
        if (!pickupContainer) return;
        
        try {
            const response = await fetch('/cell-storage/mobile/api/pickup-list');
            const data = await response.json();
            
            if (data.success) {
                this.pickupList = data.data;
            }
        } catch (error) {
            console.error('Error loading pickup list:', error);
        }
        
        if (this.pickupList.length === 0) {
            pickupContainer.innerHTML = '<div class="empty-state">Pickup list is empty</div>';
            return;
        }

        pickupContainer.innerHTML = `
            <div class="pickup-header">
                <h3>Pickup List (${this.pickupList.length})</h3>
                <button class="btn btn-outline" onclick="app.clearPickupList()">Clear All</button>
            </div>
            <div class="pickup-items">
                ${this.pickupList.map((item, index) => `
                    <div class="pickup-item">
                        <div class="pickup-info">
                            <h4>${item.vialName}</h4>
                            <p class="added-time">Added: ${item.addedAt}</p>
                        </div>
                        <button class="remove-btn" onclick="app.removeFromPickup(${index})">Remove</button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async removeFromPickup(index) {
        if (index < 0 || index >= this.pickupList.length) return;
        
        const batchToRemove = this.pickupList[index];
        
        try {
            const response = await fetch('/cell-storage/mobile/api/remove-from-pickup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getCSRFHeaders()
                },
                body: JSON.stringify({ remove_batches: [batchToRemove.batch_id] })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.pickupList.splice(index, 1);
                this.updatePickupList();
            } else {
                alert('Failed to remove from pickup list: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error removing from pickup list:', error);
            alert('Failed to remove from pickup list');
        }
    }

    async clearPickupList() {
        if (this.pickupList.length === 0) {
            alert('Pickup list is already empty');
            return;
        }

        if (confirm('Are you sure you want to clear the pickup list?')) {
            const allBatchIds = this.pickupList.map(item => item.batch_id);
            
            try {
                const response = await fetch('/cell-storage/mobile/api/remove-from-pickup', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...this.getCSRFHeaders()
                    },
                    body: JSON.stringify({ remove_batches: allBatchIds })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.pickupList = [];
                    this.updatePickupList();
                } else {
                    alert('Failed to clear pickup list: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error clearing pickup list:', error);
                alert('Failed to clear pickup list');
            }
        }
    }

    async loadInventoryData() {
        const inventoryContent = document.getElementById('inventory-content');
        if (!inventoryContent) return;
        
        try {
            const response = await fetch('/cell-storage/mobile/api/browse-inventory');
            const data = await response.json();
            
            if (data.success && data.data) {
                this.displayInventoryGrid(data.data);
            } else {
                inventoryContent.innerHTML = '<div class="empty-state">No inventory data available</div>';
            }
        } catch (error) {
            console.error('Error loading inventory:', error);
            inventoryContent.innerHTML = '<div class="empty-state">Error loading inventory data</div>';
        }
    }

    displayInventoryGrid(inventory) {
        const inventoryContent = document.getElementById('inventory-content');
        if (!inventoryContent) return;
        
        const towerNames = Object.keys(inventory);
        if (towerNames.length === 0) {
            inventoryContent.innerHTML = '<div class="empty-state">No inventory data available</div>';
            return;
        }
        
        inventoryContent.innerHTML = towerNames.map(towerName => {
            const towerData = inventory[towerName];
            const drawerNames = Object.keys(towerData);
            const totalBoxes = drawerNames.reduce((sum, drawerName) => sum + towerData[drawerName].length, 0);
            
            return `
                <div class="location-card">
                    <h3>${towerName}</h3>
                    <div class="location-stats">
                        <span class="stat">Drawers: ${drawerNames.length}</span>
                        <span class="stat">Boxes: ${totalBoxes}</span>
                    </div>
                    <button class="btn btn-primary" onclick="app.browseLocation('${towerName}')">Browse</button>
                </div>
            `;
        }).join('');
    }

    async browseLocation(locationId) {
        // Future enhancement: implement location browsing functionality
        console.log('Browse location:', locationId);
        alert('Location browsing feature coming soon!');
    }

    async handleAddVial(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        
        // Add position information
        const selectedRow = document.getElementById('selected-row');
        const selectedCol = document.getElementById('selected-col');
        
        if (!selectedRow?.value || !selectedCol?.value) {
            alert('Please select a position for the vial');
            return;
        }
        
        data.row = selectedRow.value;
        data.col = selectedCol.value;
        
        try {
            const response = await fetch('/cell-storage/mobile/api/add-cryovial', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getCSRFHeaders()
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            const addResult = document.getElementById('add-result');
            if (addResult) {
                if (result.success) {
                    addResult.innerHTML = '<div class="success-message">CryoVial added successfully!</div>';
                    this.resetForm();
                } else {
                    addResult.innerHTML = `<div class="error-message">Error: ${result.error || 'Unknown error'}</div>`;
                }
            }
        } catch (error) {
            console.error('Add vial error:', error);
            const addResult = document.getElementById('add-result');
            if (addResult) {
                addResult.innerHTML = '<div class="error-message">Failed to add vial. Please try again.</div>';
            }
        }
    }

    resetForm() {
        const form = document.getElementById('add-vial-form');
        if (form) {
            form.reset();
        }
        
        // Reset position selection
        const drawerSelect = document.getElementById('drawer-select');
        const boxSelect = document.getElementById('box-select');
        const positionGrid = document.getElementById('position-grid');
        const positionInfo = document.getElementById('position-info');
        
        if (drawerSelect) {
            drawerSelect.innerHTML = '<option value="">Select Drawer</option>';
            drawerSelect.disabled = true;
        }
        if (boxSelect) {
            boxSelect.innerHTML = '<option value="">Select Box</option>';
            boxSelect.disabled = true;
        }
        if (positionGrid) {
            positionGrid.style.display = 'none';
        }
        if (positionInfo) {
            positionInfo.textContent = 'Select a box to see available positions';
        }
        
        // Clear result messages
        const addResult = document.getElementById('add-result');
        if (addResult) {
            addResult.innerHTML = '';
        }
    }

    async showVialDetails(vialId) {
        try {
            const response = await fetch(`/cell-storage/mobile/api/vial-details/${vialId}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayVialModal(data.data);
            } else {
                alert('Failed to load vial details: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading vial details:', error);
            alert('Failed to load vial details');
        }
    }

    displayVialModal(vial) {
        const modal = document.getElementById('vial-modal');
        const vialDetails = document.getElementById('vial-details');
        
        if (!modal || !vialDetails) return;
        
        vialDetails.innerHTML = `
            <div class="detail-section">
                <h3>Basic Information</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="label">Batch Name:</span>
                        <span class="value">${vial.batch_name || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Cell Line:</span>
                        <span class="value">${vial.cell_line || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Frozen By:</span>
                        <span class="value">${vial.frozen_by || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Location:</span>
                        <span class="value">${vial.location || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Date Frozen:</span>
                        <span class="value">${vial.date_frozen || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Passage Number:</span>
                        <span class="value">${vial.passage_number || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Volume:</span>
                        <span class="value">${vial.volume_ml || 'N/A'} ml</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Concentration:</span>
                        <span class="value">${vial.concentration || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Fluorescence Tag:</span>
                        <span class="value">${vial.fluorescence_tag || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Resistance:</span>
                        <span class="value">${vial.resistance || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Parental Cell Line:</span>
                        <span class="value">${vial.parental_cell_line || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Status:</span>
                        <span class="value">${vial.status || 'N/A'}</span>
                    </div>
                    ${vial.notes ? `
                    <div class="detail-item full-width">
                        <span class="label">Notes:</span>
                        <span class="value">${vial.notes}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        modal.style.display = 'block';
    }

    closeModal() {
        const modal = document.getElementById('vial-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
}

// Initialize application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new MobileCryoVialApp();
});

// Close modal when clicking outside
window.addEventListener('click', (event) => {
    const modal = document.getElementById('vial-modal');
    if (event.target === modal && app) {
        app.closeModal();
    }
});