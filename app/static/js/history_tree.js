const HistoryTreeApp = (() => {
    const state = {
        selectedBatch: null,
        summary: null,
        lineage: null,
        lineageSource: null,
        mode: 'full',
        viewportDepth: 4,
        maxDepth: 5,
        requestId: 0
    };

    const elements = {};
    let searchTimer = null;
    let tooltipEl = null;

    const NODE_VERTICAL_GAP = 80;
    const NODE_HORIZONTAL_GAP = 160;
    const VIEWBOX_MARGIN = 80;

    const API_PREFIX = (() => {
        const path = window.location.pathname || '';
        if (path.endsWith('/history-tree')) {
            const base = path.slice(0, -'/history-tree'.length);
            return base || '/cell-storage';
        }
        const marker = '/history-tree/';
        if (path.includes(marker)) {
            const base = path.split(marker)[0];
            return base || '/cell-storage';
        }
        return '/cell-storage';
    })();

    function init() {
        cacheElements();
        if (!window.d3) {
            showVisualStatus('D3 failed to load. Refresh the page or check your network.');
            return;
        }

        setupTooltip();
        bindEvents();
        loadQuickLists();
        hydrateFromQuery();
    }

    function cacheElements() {
        elements.searchInput = document.getElementById('history-tree-search');
        elements.searchResults = document.getElementById('history-tree-search-results');
        elements.searchHint = document.getElementById('history-tree-search-hint');
        elements.quickRecent = document.getElementById('history-tree-recent-list');
        elements.quickLineage = document.getElementById('history-tree-lineage-list');
        elements.selectionCard = document.getElementById('history-tree-selection-card');
        elements.selectedName = document.getElementById('history-tree-selected-name');
        elements.selectedMeta = document.getElementById('history-tree-selected-meta');
        elements.selectedDetails = document.getElementById('history-tree-selected-details');
        elements.manageLink = document.getElementById('history-tree-manage-link');
        elements.copyLink = document.getElementById('history-tree-copy-link');
        elements.statsContainer = document.getElementById('history-tree-stats');
        elements.statsEmpty = document.getElementById('history-tree-stats-empty');
        elements.statDirectParents = document.getElementById('history-tree-stat-direct-parents');
        elements.statDirectChildren = document.getElementById('history-tree-stat-direct-children');
        elements.statAncestors = document.getElementById('history-tree-stat-ancestors');
        elements.statDescendants = document.getElementById('history-tree-stat-descendants');
        elements.statTotal = document.getElementById('history-tree-stat-total');
        elements.visualStatus = document.getElementById('history-tree-visual-status');
        elements.feedback = document.getElementById('history-tree-feedback');
        elements.meta = document.getElementById('history-tree-meta');
        elements.svg = document.getElementById('history-tree-svg');
        elements.placeholder = document.getElementById('history-tree-placeholder');
        elements.refreshButton = document.getElementById('refresh-history-tree');
        elements.modeGroup = document.getElementById('history-tree-mode-group');
        elements.fitButton = document.getElementById('history-tree-fit');
        elements.exportButton = document.getElementById('history-tree-export');
        if (elements.searchResults) {
            elements.searchResults.classList.add('list-group');
        }
        if (elements.svg) {
            elements.svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        }
    }

    function setupTooltip() {
        tooltipEl = document.createElement('div');
        tooltipEl.className = 'history-tree-tooltip';
        tooltipEl.style.display = 'none';
        document.body.appendChild(tooltipEl);
    }

    function bindEvents() {
        elements.searchInput?.addEventListener('input', handleSearchInput);
        document.addEventListener('click', handleDocumentClick);
        elements.refreshButton?.addEventListener('click', () => {
            if (state.selectedBatch) {
                selectBatch({ id: state.selectedBatch.id });
            }
        });
        elements.modeGroup?.addEventListener('change', event => {
            if (event.target && event.target.name === 'history-tree-mode') {
                state.mode = event.target.value;
                renderHistoryTree();
                updateMeta();
            }
        });
        window.addEventListener('resize', debounce(() => {
            if (state.lineage) {
                renderHistoryTree();
            }
        }, 250));
        elements.fitButton?.addEventListener('click', () => {
            if (state.lineage) {
                renderHistoryTree();
            }
        });
        elements.exportButton?.addEventListener('click', exportSvg);
        elements.copyLink?.addEventListener('click', copyDirectLink);
    }

    function hydrateFromQuery() {
        const params = new URLSearchParams(window.location.search);
        const batchId = params.get('batch_id');
        if (batchId) {
            selectBatch({ id: parseInt(batchId, 10) });
        }
    }

    function handleSearchInput(event) {
        const query = event.target.value.trim();
        if (searchTimer) {
            clearTimeout(searchTimer);
        }

        if (!query) {
            if (elements.searchResults) {
                elements.searchResults.classList.add('d-none');
                elements.searchResults.innerHTML = '';
            }
            if (elements.searchHint) {
                elements.searchHint.textContent = 'Start typing to search across batches.';
            }
            return;
        }

        if (query.length < 2) {
            if (elements.searchHint) {
                elements.searchHint.textContent = 'Enter at least two characters to search.';
            }
            elements.searchResults?.classList.add('d-none');
            return;
        }

        if (elements.searchHint) {
            elements.searchHint.textContent = 'Searching...';
        }
        searchTimer = setTimeout(() => performSearch(query), 300);
    }

    async function performSearch(query) {
        try {
            const response = await fetchJson(buildApiUrl(`/api/batch/search?q=${encodeURIComponent(query)}&limit=15`));
            if (!response.success) {
                throw new Error(response.message || 'Search failed');
            }
            renderSearchResults(response.batches || []);
        } catch (error) {
            console.error(error);
            if (elements.searchHint) {
                elements.searchHint.textContent = 'Search failed. Retry in a moment.';
            }
            if (elements.searchResults) {
                elements.searchResults.innerHTML = '';
                elements.searchResults.classList.add('d-none');
            }
        }
    }

    function renderSearchResults(batches) {
        if (!elements.searchResults) {
            return;
        }
        elements.searchResults.innerHTML = '';

        if (!batches.length) {
            const emptyItem = document.createElement('div');
            emptyItem.className = 'list-group-item text-muted small';
            emptyItem.textContent = 'No batches match that search.';
            elements.searchResults.appendChild(emptyItem);
            elements.searchResults.classList.remove('d-none');
            if (elements.searchHint) {
                elements.searchHint.textContent = 'Try another search term.';
            }
            return;
        }

        batches.forEach(batch => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action';
            item.innerHTML = `
                <div class="fw-semibold">${escapeHtml(batch.name)}</div>
                <div class="small text-muted">${formatBatchMeta(batch)}</div>
            `;
            item.addEventListener('click', () => {
                selectBatch(batch);
                elements.searchResults.classList.add('d-none');
            });
            elements.searchResults.appendChild(item);
        });

        elements.searchResults.classList.remove('d-none');
        if (elements.searchHint) {
            const label = batches.length === 1 ? 'result' : 'results';
            elements.searchHint.textContent = `${batches.length} ${label} found.`;
        }
    }

    function handleDocumentClick(event) {
        if (!elements.searchResults || !elements.searchInput) {
            return;
        }
        if (!elements.searchResults.contains(event.target) && event.target !== elements.searchInput) {
            elements.searchResults.classList.add('d-none');
        }
    }

    async function loadQuickLists() {
        try {
            const [recent, lineage] = await Promise.all([
                fetchJson(buildApiUrl('/api/batch/recent?limit=10')),
                fetchJson(buildApiUrl('/api/batch/with-lineage?limit=10'))
            ]);

            renderQuickList(elements.quickRecent, recent && recent.success ? recent.batches : [], 'No recent batches found.');
            renderQuickList(elements.quickLineage, lineage && lineage.success ? lineage.batches : [], 'No lineage batches available yet.');
        } catch (error) {
            console.error(error);
            renderQuickList(elements.quickRecent, [], 'Unable to load recent batches.');
            renderQuickList(elements.quickLineage, [], 'Unable to load lineage batches.');
        }
    }

    function renderQuickList(container, batches, fallbackText) {
        if (!container) {
            return;
        }
        container.innerHTML = '';

        if (!batches.length) {
            const empty = document.createElement('p');
            empty.className = 'text-muted small mb-0';
            empty.textContent = fallbackText;
            container.appendChild(empty);
            return;
        }

        batches.forEach(batch => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'history-tree-quick-item';
            button.innerHTML = `
                <span class="history-tree-quick-name">${escapeHtml(batch.name)}</span>
                <span class="history-tree-quick-meta">${formatBatchMeta(batch)}</span>
            `;
            button.addEventListener('click', () => selectBatch(batch));
            container.appendChild(button);
        });
    }

    async function selectBatch(batchLike) {
        if (!batchLike || !batchLike.id) {
            return;
        }
        const batchId = Number(batchLike.id);
        const requestMarker = ++state.requestId;
        setLoadingState(batchId);

        try {
            const lineagePayload = await loadLineage(batchId);
            if (requestMarker !== state.requestId) {
                return;
            }

            const normalizedLineage = normalizeLineage(lineagePayload.lineage);
            state.lineage = normalizedLineage;
            state.lineageSource = lineagePayload.source;
            state.selectedBatch = normalizedLineage.current;
            state.summary = await loadSummary(batchId, normalizedLineage);

            updateUrl(batchId);
            updateSelectionCard();
            updateStats();
            renderHistoryTree();
            updateMeta();
            showSourceFeedback(lineagePayload);
        } catch (error) {
            console.error(error);
            showVisualStatus(error.message || 'Failed to load lineage data.');
            elements.feedback?.classList.add('d-none');
        }
    }

    function setLoadingState(batchId) {
        showVisualStatus(`Loading lineage for batch ${batchId}...`);
        elements.feedback?.classList.add('d-none');
        if (elements.meta) {
            elements.meta.textContent = '';
        }
        elements.selectionCard?.classList.add('d-none');
    }

    async function loadLineage(batchId) {
        const params = new URLSearchParams({
            viewport_depth: String(state.viewportDepth),
            include_details: 'true',
            use_cache: 'true'
        });

        try {
            const response = await fetchJson(buildApiUrl(`/api/v2/batch/${batchId}/lineage/optimized?${params.toString()}`));
            if (!response.success || !response.lineage) {
                throw new Error(response.message || 'Optimized lineage unavailable');
            }
            return { lineage: response.lineage, source: 'v2', cached: !!response.cached };
        } catch (error) {
            console.warn('Falling back to v1 lineage endpoint', error);
            const response = await fetchJson(buildApiUrl(`/api/batch/${batchId}/lineage?max_depth=${state.maxDepth}`));
            if (!response.success || !response.lineage) {
                throw new Error(response.message || 'Lineage data unavailable');
            }
            return { lineage: response.lineage, source: 'v1', cached: false };
        }
    }

    async function loadSummary(batchId, lineage) {
        try {
            const response = await fetchJson(buildApiUrl(`/api/v2/batch/${batchId}/lineage/summary`));
            if (response.success && response.summary) {
                return response.summary;
            }
        } catch (error) {
            console.warn('Summary endpoint failed, deriving from lineage', error);
        }
        return deriveSummaryFromLineage(lineage);
    }

    function normalizeLineage(raw) {
        if (!raw) {
            return null;
        }
        const current = { ...raw.current, type: (raw.current && raw.current.type) || 'current' };
        const ancestors = (raw.ancestors || []).map(node => normalizeNode(node, 'ancestor')).filter(Boolean);
        const descendants = (raw.descendants || []).map(node => normalizeNode(node, 'descendant')).filter(Boolean);
        return {
            current,
            ancestors,
            descendants,
            metadata: raw.metadata || {}
        };
    }

    function normalizeNode(node, fallbackType) {
        if (!node) {
            return null;
        }
        const children = node.children || node.parents || [];
        return {
            ...node,
            type: node.type || fallbackType,
            children: children.map(child => normalizeNode(child, fallbackType)).filter(Boolean)
        };
    }

    function deriveSummaryFromLineage(lineage) {
        if (!lineage) {
            return null;
        }
        const directParents = lineage.ancestors.length;
        const directChildren = lineage.descendants.length;
        const ancestorCount = countNodes(lineage.ancestors);
        const descendantCount = countNodes(lineage.descendants);
        return {
            batch_id: lineage.current.id,
            batch_name: lineage.current.name,
            has_lineage: ancestorCount + descendantCount > 0,
            direct_parents: directParents,
            direct_children: directChildren,
            estimated_ancestors: ancestorCount,
            estimated_descendants: descendantCount,
            estimated_total_related: ancestorCount + descendantCount
        };
    }

    function countNodes(nodes) {
        if (!nodes || !nodes.length) {
            return 0;
        }
        return nodes.reduce((total, node) => total + 1 + countNodes(node.children || []), 0);
    }

    function updateSelectionCard() {
        if (!elements.selectionCard || !state.selectedBatch) {
            return;
        }
        elements.selectionCard.classList.remove('d-none');
        elements.selectedName.textContent = state.selectedBatch.name || `Batch ${state.selectedBatch.id}`;
        elements.selectedMeta.textContent = formatSelectedMeta(state.selectedBatch);
        elements.selectedDetails.innerHTML = buildDetailsList(state.selectedBatch);
        elements.manageLink.href = `${API_PREFIX}/admin/manage_batch/${state.selectedBatch.id}`;
    }

    function updateStats() {
        if (!elements.statsContainer || !state.summary) {
            elements.statsContainer?.classList.add('d-none');
            elements.statsEmpty?.classList.remove('d-none');
            return;
        }

        elements.statDirectParents.textContent = formatNumber(state.summary.direct_parents);
        elements.statDirectChildren.textContent = formatNumber(state.summary.direct_children);
        elements.statAncestors.textContent = formatNumber(state.summary.estimated_ancestors);
        elements.statDescendants.textContent = formatNumber(state.summary.estimated_descendants);
        elements.statTotal.textContent = formatNumber(state.summary.estimated_total_related);
        elements.statsContainer.classList.remove('d-none');
        elements.statsEmpty?.classList.add('d-none');
    }

    function renderHistoryTree() {
        if (!elements.svg) {
            return;
        }
        const svg = d3.select(elements.svg);
        svg.selectAll('*').remove();

        if (!state.lineage) {
            elements.placeholder?.classList.remove('d-none');
            return;
        }
        elements.placeholder?.classList.add('d-none');

        const mode = state.mode || 'full';
        if (mode === 'descendants') {
            drawSingleTree(svg, prepareTreeData(state.lineage, 'descendant'), 1);
        } else if (mode === 'ancestors') {
            drawSingleTree(svg, prepareTreeData(state.lineage, 'ancestor'), -1);
        } else {
            drawCombinedTree(svg, state.lineage);
        }
        showVisualStatus(`Viewing ${mode} tree for ${state.selectedBatch.name || 'selected batch'}.`);
    }

    function prepareTreeData(lineage, focus) {
        const current = { ...lineage.current };
        current.children = focus === 'ancestor' ? lineage.ancestors : lineage.descendants;
        return current;
    }

    function drawSingleTree(svg, rootData, orientation) {
        if (!rootData.children || !rootData.children.length) {
            if (elements.placeholder) {
                elements.placeholder.classList.remove('d-none');
                const message = orientation < 0 ? 'No ancestor information found for this batch.' : 'No descendants recorded for this batch.';
                const textEl = elements.placeholder.querySelector('p');
                if (textEl) {
                    textEl.textContent = message;
                }
            }
            return;
        }

        const hierarchy = d3.hierarchy(rootData);
        const treeLayout = d3.tree().nodeSize([NODE_VERTICAL_GAP, NODE_HORIZONTAL_GAP]);
        treeLayout(hierarchy);
        hierarchy.each(node => {
            node.y = node.depth * NODE_HORIZONTAL_GAP * orientation;
        });

        renderSvg(svg, hierarchy.descendants(), hierarchy.links());
    }

    function drawCombinedTree(svg, lineage) {
        const descendantsRoot = d3.hierarchy({ ...lineage.current, children: lineage.descendants });
        const ancestorsRoot = d3.hierarchy({ ...lineage.current, children: lineage.ancestors });
        const treeLayout = d3.tree().nodeSize([NODE_VERTICAL_GAP, NODE_HORIZONTAL_GAP]);

        treeLayout(descendantsRoot);
        descendantsRoot.each(node => {
            node.y = node.depth * NODE_HORIZONTAL_GAP;
        });

        treeLayout(ancestorsRoot);
        ancestorsRoot.each(node => {
            node.y = -node.depth * NODE_HORIZONTAL_GAP;
        });

        const nodes = [];
        const links = [];

        descendantsRoot.descendants().forEach(node => nodes.push(node));
        descendantsRoot.links().forEach(link => links.push(link));

        ancestorsRoot.descendants().forEach(node => {
            if (node.depth > 0) {
                nodes.push(node);
            }
        });
        ancestorsRoot.links().forEach(link => {
            if (link.target.depth > 0) {
                links.push(link);
            }
        });

        renderSvg(svg, nodes, links);
    }

    function renderSvg(svg, nodes, links) {
        const nodeData = nodes.map(node => ({
            x: node.x,
            y: node.y,
            data: node.data,
            relation: node.data.type || (node.y < 0 ? 'ancestor' : node.y > 0 ? 'descendant' : 'current')
        }));

        const linkData = links.map(link => ({
            source: {
                x: link.source.x,
                y: link.source.y,
                relation: link.source.data.type || (link.source.y < 0 ? 'ancestor' : link.source.y > 0 ? 'descendant' : 'current')
            },
            target: {
                x: link.target.x,
                y: link.target.y,
                relation: link.target.data.type || (link.target.y < 0 ? 'ancestor' : link.target.y > 0 ? 'descendant' : 'current')
            }
        }));

        const xExtent = d3.extent(nodeData, node => node.x);
        const yExtent = d3.extent(nodeData, node => node.y);
        const width = Math.max(400, (yExtent[1] - yExtent[0]) + VIEWBOX_MARGIN * 2);
        const height = Math.max(400, (xExtent[1] - xExtent[0]) + VIEWBOX_MARGIN * 2);
        svg.attr('viewBox', `${yExtent[0] - VIEWBOX_MARGIN} ${xExtent[0] - VIEWBOX_MARGIN} ${width} ${height}`);

        const g = svg.append('g');
        const diagonal = d3.linkHorizontal().x(point => point.y).y(point => point.x);

        g.append('g')
            .selectAll('path')
            .data(linkData)
            .join('path')
            .attr('class', link => `history-tree-link history-tree-link--${link.target.relation}`)
            .attr('d', link => diagonal({ source: { x: link.source.x, y: link.source.y }, target: { x: link.target.x, y: link.target.y } }));

        const nodeGroup = g.append('g')
            .selectAll('g')
            .data(nodeData)
            .join('g')
            .attr('class', node => `history-tree-node history-tree-node--${node.relation}`)
            .attr('transform', node => `translate(${node.y},${node.x})`)
            .on('mouseenter', (event, datum) => showTooltip(event, datum))
            .on('mousemove', event => moveTooltip(event))
            .on('mouseleave', hideTooltip)
            .on('click', (event, datum) => handleNodeClick(event, datum));

        nodeGroup.append('circle').attr('r', 16);

        nodeGroup.append('text')
            .attr('dy', '0.35em')
            .attr('dx', node => {
                if (node.relation === 'ancestor') {
                    return -22;
                }
                if (node.relation === 'descendant') {
                    return 22;
                }
                return 0;
            })
            .attr('text-anchor', node => {
                if (node.relation === 'ancestor') {
                    return 'end';
                }
                if (node.relation === 'descendant') {
                    return 'start';
                }
                return 'middle';
            })
            .text(node => truncate(node.data.name || `Batch ${node.data.id}`, 22));
    }

    function showTooltip(event, datum) {
        if (!tooltipEl) {
            return;
        }
        tooltipEl.textContent = buildTooltipText(datum);
        tooltipEl.style.display = 'block';
        moveTooltip(event);
    }

    function moveTooltip(event) {
        if (!tooltipEl || !event) {
            return;
        }
        const pageX = event.pageX ?? 0;
        const pageY = event.pageY ?? 0;
        tooltipEl.style.left = `${pageX}px`;
        tooltipEl.style.top = `${pageY - 20}px`;
    }

    function hideTooltip() {
        if (tooltipEl) {
            tooltipEl.style.display = 'none';
        }
    }

    function handleNodeClick(event, datum) {
        event?.stopPropagation();
        if (!datum || !datum.id || (state.selectedBatch && datum.id === state.selectedBatch.id)) {
            return;
        }
        selectBatch({ id: datum.id });
    }

    function showSourceFeedback(payload) {
        if (!elements.feedback || !payload) {
            return;
        }
        const metadata = state.lineage && state.lineage.metadata;
        const messages = [];
        if (payload.source === 'v2') {
            messages.push('Optimized API v2 response');
            if (payload.cached) {
                messages.push('served from cache');
            }
        } else {
            messages.push('Classic API v1 response');
        }
        if (metadata && (metadata.has_more_ancestors || metadata.has_more_descendants)) {
            messages.push('partial tree shown; refresh to load deeper levels');
        }
        elements.feedback.textContent = messages.join(' | ');
        elements.feedback.classList.toggle('d-none', !messages.length);
    }

    function updateMeta() {
        if (!elements.meta || !state.summary) {
            if (elements.meta) {
                elements.meta.textContent = '';
            }
            return;
        }
        const parts = [];
        parts.push(`Ancestors: ${formatNumber(state.summary.estimated_ancestors)}`);
        parts.push(`Descendants: ${formatNumber(state.summary.estimated_descendants)}`);
        if (state.lineageSource) {
            parts.push(`Source: ${state.lineageSource.toUpperCase()}`);
        }
        parts.push(`Mode: ${state.mode}`);
        elements.meta.textContent = parts.join(' | ');
    }

    function showVisualStatus(message) {
        if (elements.visualStatus) {
            elements.visualStatus.textContent = message;
        }
    }

    function copyDirectLink() {
        if (!state.selectedBatch) {
            return;
        }
        const url = new URL(window.location.origin + `${API_PREFIX}/history-tree`);
        url.searchParams.set('batch_id', state.selectedBatch.id);
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(url.toString())
                .then(() => showVisualStatus('Direct link copied to clipboard.'))
                .catch(() => showVisualStatus('Unable to copy link automatically.'));
        } else {
            showVisualStatus('Clipboard not supported in this browser.');
        }
    }

    function exportSvg() {
        if (!elements.svg) {
            return;
        }
        const svgCopy = elements.svg.cloneNode(true);
        svgCopy.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        const blob = new Blob([svgCopy.outerHTML], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `history_tree_${state.selectedBatch ? state.selectedBatch.id : 'export'}.svg`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }

    function updateUrl(batchId) {
        const url = new URL(window.location.href);
        url.pathname = `${API_PREFIX}/history-tree`;
        if (batchId) {
            url.searchParams.set('batch_id', batchId);
        } else {
            url.searchParams.delete('batch_id');
        }
        window.history.replaceState({}, '', url);
    }

    function formatBatchMeta(batch) {
        if (!batch) {
            return '';
        }
        const parts = [];
        if (batch.cell_line) {
            parts.push(batch.cell_line);
        }
        if (batch.parental_cell_line) {
            parts.push(`parent: ${batch.parental_cell_line}`);
        }
        if (batch.date_frozen) {
            parts.push(formatDate(batch.date_frozen));
        }
        return parts.join(' | ');
    }

    function formatSelectedMeta(batch) {
        const parts = [];
        if (batch.cell_line) {
            parts.push(batch.cell_line);
        }
        if (batch.passage_number) {
            parts.push(`Passage ${batch.passage_number}`);
        }
        if (batch.date_frozen) {
            parts.push(`Frozen ${formatDate(batch.date_frozen)}`);
        }
        return parts.join(' | ');
    }

    function buildDetailsList(batch) {
        const rows = [];
        rows.push(renderDetail('Batch ID', batch.id));
        rows.push(renderDetail('Cell line', batch.cell_line || 'N/A'));
        rows.push(renderDetail('Parental line', batch.parental_cell_line || 'N/A'));
        rows.push(renderDetail('Passage', batch.passage_number || 'N/A'));
        rows.push(renderDetail('Vials', batch.vial_count != null ? batch.vial_count : 'N/A'));
        return rows.join('');
    }

    function renderDetail(label, value) {
        return `
            <dt class="col-5 text-muted">${escapeHtml(String(label))}</dt>
            <dd class="col-7">${escapeHtml(String(value))}</dd>
        `;
    }

    function buildTooltipText(data) {
        const parts = [];
        parts.push(data.name || `Batch ${data.id}`);
        if (data.cell_line) {
            parts.push(`Cell line: ${data.cell_line}`);
        }
        if (data.passage_number) {
            parts.push(`Passage ${data.passage_number}`);
        }
        return parts.join(' | ');
    }

    function formatDate(value) {
        try {
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) {
                return value;
            }
            return date.toISOString().slice(0, 10);
        } catch (error) {
            return value;
        }
    }

    function escapeHtml(text) {
        if (text == null) {
            return '';
        }
        return String(text).replace(/[&<>"']/g, char => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[char]);
    }

    function truncate(text, maxLength) {
        if (!text) {
            return '';
        }
        const safe = String(text);
        return safe.length > maxLength ? `${safe.slice(0, maxLength - 3)}...` : safe;
    }

    function formatNumber(value) {
        const number = Number(value || 0);
        return Number.isFinite(number) ? number.toLocaleString() : '0';
    }

    function buildApiUrl(path) {
        if (!path.startsWith('/')) {
            return `${API_PREFIX}/${path}`;
        }
        return `${API_PREFIX}${path}`;
    }

    async function fetchJson(url, options) {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }
        return response.json();
    }

    function debounce(fn, delay) {
        let timer = null;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), delay);
        };
    }

    return { init };
})();

document.addEventListener('DOMContentLoaded', HistoryTreeApp.init);
