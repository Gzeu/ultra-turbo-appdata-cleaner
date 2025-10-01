// Cleaner page specific JavaScript functions

let scanResults = [];
let selectedFiles = new Set();
let currentFilters = {
    category: 'all',
    safety: 'all',
    search: ''
};

let currentScanOperation = null;
let isScanning = false;

// Initialize cleaner page
function initializeCleaner() {
    console.log('🧹 Initializing cleaner page...');
    
    // Setup event listeners
    setupCleanerEventListeners();
    
    // Load last scan results if available
    loadLastScanResults();
    
    // Check URL parameters for auto-actions
    checkURLParameters();
}

// Setup event listeners
function setupCleanerEventListeners() {
    // Select all checkbox
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', toggleSelectAll);
    }
    
    // Filter change listeners
    document.getElementById('category-filter').addEventListener('change', filterResults);
    document.getElementById('safety-filter').addEventListener('change', filterResults);
    document.getElementById('search-filter').addEventListener('keyup', filterResults);
    
    // WebSocket events
    window.addEventListener('utac-scan-results', handleScanResults);
    window.addEventListener('utac-cleaning-results', handleCleaningResults);
    window.addEventListener('utac-progress-update', handleProgressUpdate);
}

// Check URL parameters for auto-actions
function checkURLParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    const action = urlParams.get('action');
    
    if (action === 'full_scan') {
        setTimeout(() => {
            document.getElementById('scan-type').value = 'full';
            startScan();
        }, 1000);
    }
}

// Start scan operation
function startScan() {
    if (isScanning) {
        showNotification('Scan already in progress', 'warning');
        return;
    }
    
    const scanType = document.getElementById('scan-type').value;
    const maxAge = parseInt(document.getElementById('max-age').value);
    const customPaths = document.getElementById('custom-paths').value
        .split('\n')
        .map(p => p.trim())
        .filter(p => p.length > 0);
    
    console.log(`🔍 Starting ${scanType} scan...`);
    
    isScanning = true;
    showProgressModal(`${scanType.charAt(0).toUpperCase() + scanType.slice(1)} Scan`);
    
    // Determine API endpoint and payload
    let endpoint, payload;
    
    switch (scanType) {
        case 'quick':
            endpoint = '/api/scan/quick';
            payload = {};
            break;
        case 'full':
            endpoint = '/api/scan/full';
            payload = { paths: customPaths.length > 0 ? customPaths : undefined };
            break;
        case 'appdata':
            endpoint = '/api/scan/appdata';
            payload = {};
            break;
        case 'temp':
            endpoint = '/api/scan/temp';
            payload = { max_age_days: maxAge };
            break;
        case 'duplicates':
            endpoint = '/api/scan/duplicates';
            payload = { paths: customPaths.length > 0 ? customPaths : ['C:\\Users'] };
            break;
        default:
            showNotification('Invalid scan type selected', 'danger');
            isScanning = false;
            return;
    }
    
    // Start scan
    makeAPICall(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload)
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentScanOperation = data.operation_id;
        addActivityItem(`${scanType.charAt(0).toUpperCase() + scanType.slice(1)} Scan`, 'Scan started', 'info');
        
        console.log(`Scan started with operation ID: ${currentScanOperation}`);
    })
    .catch(error => {
        console.error('Scan failed to start:', error);
        hideProgressModal();
        isScanning = false;
        showNotification(`Scan failed to start: ${error.message}`, 'danger');
    });
}

// Handle scan results from WebSocket
function handleScanResults(event) {
    const results = event.detail.results;
    console.log('📄 Received scan results:', results);
    
    scanResults = results.files || [];
    isScanning = false;
    
    displayScanResults(results);
    hideProgressModal();
    
    showNotification(
        `Scan completed! Found ${results.total_files || 0} files (${results.cleanable_files || 0} cleanable)`,
        'success'
    );
    
    addActivityItem('Scan Complete', `Found ${results.total_files || 0} files`, 'success');
}

// Display scan results
function displayScanResults(results) {
    console.log('📊 Displaying scan results...');
    
    // Update summary statistics
    document.getElementById('total-files').textContent = results.total_files || 0;
    document.getElementById('cleanable-files').textContent = results.cleanable_files || 0;
    document.getElementById('potential-savings').textContent = 
        (results.potential_savings_mb || 0) + ' MB';
    
    // Clear current selection
    selectedFiles.clear();
    updateSelectedCount();
    
    // Show results section
    document.getElementById('scan-results-section').style.display = 'block';
    document.getElementById('cleaning-controls-section').style.display = 'block';
    
    // Display files in table
    displayFilesTable(scanResults);
    
    // Update category filter options based on results
    updateCategoryFilterOptions(results.categories);
}

// Display files in table
function displayFilesTable(files) {
    const tableBody = document.getElementById('files-table-body');
    if (!tableBody) return;
    
    if (!files || files.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    <i class="bi bi-search fs-1 mb-2 d-block"></i>
                    No files found matching current criteria.
                </td>
            </tr>
        `;
        return;
    }
    
    let tableHTML = '';
    
    files.forEach((file, index) => {
        const safetyClass = getSafetyLevelClass(file.safety_level || 3);
        const safetyText = getSafetyLevelText(file.safety_level || 3);
        const fileIcon = getFileTypeIcon(file.extension, file.category);
        const fileAge = formatFileAge(file.age_days || 0);
        const fileSize = formatBytes(file.size || 0);
        const isSelected = selectedFiles.has(index);
        
        tableHTML += `
            <tr class="file-row ${isSelected ? 'selected' : ''}" 
                data-index="${index}"
                data-category="${file.category || 'unknown'}"
                data-safety="${file.safety_level || 3}">
                <td>
                    <input type="checkbox" class="file-checkbox" 
                           data-index="${index}" 
                           ${isSelected ? 'checked' : ''}
                           onchange="toggleFileSelection(${index})">
                </td>
                <td>
                    <i class="bi ${fileIcon} file-icon ${file.category || 'unknown'}"></i>
                    <span class="text-truncate-custom" title="${file.name}">${file.name}</span>
                </td>
                <td class="file-size">${fileSize}</td>
                <td>
                    <span class="badge bg-secondary">${file.category || 'Unknown'}</span>
                </td>
                <td>
                    <span class="badge ${safetyClass}">${safetyText}</span>
                </td>
                <td class="text-muted">${fileAge}</td>
                <td>
                    <small class="text-muted text-truncate-custom" title="${file.path}">
                        ${file.path || 'Unknown'}
                    </small>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = tableHTML;
    
    // Update select all checkbox state
    updateSelectAllCheckbox();
}

// Toggle file selection
function toggleFileSelection(index) {
    if (selectedFiles.has(index)) {
        selectedFiles.delete(index);
    } else {
        selectedFiles.add(index);
    }
    
    updateSelectedCount();
    updateCleaningControls();
    updateSelectAllCheckbox();
    
    // Update row styling
    const row = document.querySelector(`tr[data-index="${index}"]`);
    if (row) {
        row.classList.toggle('selected', selectedFiles.has(index));
    }
}

// Toggle select all
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const shouldSelectAll = selectAllCheckbox.checked;
    
    // Get visible (filtered) files only
    const visibleRows = document.querySelectorAll('#files-table-body tr.file-row:not(.hidden)');
    
    visibleRows.forEach(row => {
        const index = parseInt(row.dataset.index);
        const checkbox = row.querySelector('.file-checkbox');
        
        if (shouldSelectAll) {
            selectedFiles.add(index);
            checkbox.checked = true;
            row.classList.add('selected');
        } else {
            selectedFiles.delete(index);
            checkbox.checked = false;
            row.classList.remove('selected');
        }
    });
    
    updateSelectedCount();
    updateCleaningControls();
}

// Update select all checkbox state
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const visibleRows = document.querySelectorAll('#files-table-body tr.file-row:not(.hidden)');
    const visibleSelectedCount = Array.from(visibleRows)
        .filter(row => selectedFiles.has(parseInt(row.dataset.index))).length;
    
    if (visibleRows.length === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (visibleSelectedCount === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (visibleSelectedCount === visibleRows.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

// Select all cleanable files
function selectAllCleanable() {
    selectedFiles.clear();
    
    scanResults.forEach((file, index) => {
        if (file.cleanable || file.safety_level <= 2) {
            selectedFiles.add(index);
        }
    });
    
    // Update UI
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        const index = parseInt(checkbox.dataset.index);
        checkbox.checked = selectedFiles.has(index);
        const row = checkbox.closest('tr');
        row.classList.toggle('selected', selectedFiles.has(index));
    });
    
    updateSelectedCount();
    updateCleaningControls();
    updateSelectAllCheckbox();
    
    showNotification('Selected all safe files', 'info');
}

// Clear selection
function clearSelection() {
    selectedFiles.clear();
    
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        checkbox.checked = false;
        const row = checkbox.closest('tr');
        row.classList.remove('selected');
    });
    
    updateSelectedCount();
    updateCleaningControls();
    updateSelectAllCheckbox();
    
    showNotification('Selection cleared', 'info');
}

// Update selected count display
function updateSelectedCount() {
    const count = selectedFiles.size;
    document.getElementById('selected-count').textContent = count;
    document.getElementById('selected-files-count').textContent = count;
    
    // Calculate selected size
    let selectedSize = 0;
    selectedFiles.forEach(index => {
        if (scanResults[index]) {
            selectedSize += scanResults[index].size || 0;
        }
    });
    
    document.getElementById('selected-size').textContent = formatBytes(selectedSize);
}

// Update cleaning controls
function updateCleaningControls() {
    const startBtn = document.getElementById('start-cleaning-btn');
    if (startBtn) {
        startBtn.disabled = selectedFiles.size === 0;
    }
}

// Filter results based on current filters
function filterResults() {
    currentFilters.category = document.getElementById('category-filter').value;
    currentFilters.safety = document.getElementById('safety-filter').value;
    currentFilters.search = document.getElementById('search-filter').value.toLowerCase();
    
    const rows = document.querySelectorAll('#files-table-body tr.file-row');
    
    rows.forEach(row => {
        const shouldShow = shouldShowRow(row);
        row.classList.toggle('hidden', !shouldShow);
        row.style.display = shouldShow ? '' : 'none';
    });
    
    updateSelectAllCheckbox();
}

// Check if row should be shown based on filters
function shouldShowRow(row) {
    const index = parseInt(row.dataset.index);
    const file = scanResults[index];
    if (!file) return false;
    
    // Category filter
    if (currentFilters.category !== 'all' && file.category !== currentFilters.category) {
        return false;
    }
    
    // Safety filter
    if (currentFilters.safety !== 'all' && 
        (file.safety_level || 3).toString() !== currentFilters.safety) {
        return false;
    }
    
    // Search filter
    if (currentFilters.search && 
        !(file.name || '').toLowerCase().includes(currentFilters.search) &&
        !(file.path || '').toLowerCase().includes(currentFilters.search)) {
        return false;
    }
    
    return true;
}

// Update category filter options
function updateCategoryFilterOptions(categories) {
    const categoryFilter = document.getElementById('category-filter');
    if (!categoryFilter || !categories) return;
    
    // Keep "All Categories" option
    const currentOptions = Array.from(categoryFilter.options).slice(1);
    currentOptions.forEach(option => option.remove());
    
    // Add categories from results
    Object.keys(categories).forEach(category => {
        const option = new Option(
            category.charAt(0).toUpperCase() + category.slice(1), 
            category
        );
        categoryFilter.appendChild(option);
    });
}

// Start cleaning selected files
function startCleaning() {
    if (selectedFiles.size === 0) {
        showNotification('No files selected for cleaning', 'warning');
        return;
    }
    
    const createBackup = document.getElementById('create-backup').checked;
    const showConfirmation = document.getElementById('show-confirmation').checked;
    const safeMode = document.getElementById('safe-mode').checked;
    
    // Safety check for safe mode
    if (safeMode) {
        const riskyFiles = Array.from(selectedFiles)
            .filter(index => (scanResults[index]?.safety_level || 3) > 2);
        
        if (riskyFiles.length > 0) {
            showNotification(
                `Safe mode is enabled but ${riskyFiles.length} risky files are selected. Please deselect them or disable safe mode.`,
                'warning'
            );
            return;
        }
    }
    
    // Confirmation dialog
    if (showConfirmation) {
        const selectedSize = Array.from(selectedFiles)
            .reduce((total, index) => total + (scanResults[index]?.size || 0), 0);
        
        const message = `
            Clean ${selectedFiles.size} selected files?
            
            Estimated space freed: ${formatBytes(selectedSize)}
            Backup will be ${createBackup ? 'created' : 'skipped'}
            
            This action cannot be undone!
        `;
        
        if (!confirm(message)) {
            return;
        }
    }
    
    // Get file paths
    const filePaths = Array.from(selectedFiles)
        .map(index => scanResults[index]?.path)
        .filter(path => path);
    
    console.log(`🧹 Starting cleaning of ${filePaths.length} files...`);
    
    showProgressModal('Cleaning Files');
    
    // Start cleaning
    makeAPICall('/api/clean/selected', {
        method: 'POST',
        body: JSON.stringify({
            files: filePaths,
            backup: createBackup
        })
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        console.log('Cleaning started:', data.operation_id);
        addActivityItem('File Cleaning', 'Cleaning started', 'info');
    })
    .catch(error => {
        hideProgressModal();
        showNotification(`Cleaning failed to start: ${error.message}`, 'danger');
    });
}

// Handle cleaning results from WebSocket
function handleCleaningResults(event) {
    const results = event.detail.results;
    console.log('🧹 Received cleaning results:', results);
    
    hideProgressModal();
    
    showCleaningSummary(results);
    
    // Remove cleaned files from results and UI
    if (results.success) {
        removeCleanedFilesFromUI(results);
    }
}

// Show cleaning summary modal/notification
function showCleaningSummary(results) {
    const message = `
        Cleaning completed!
        
        Files deleted: ${results.files_deleted || 0}
        Space freed: ${formatBytes(results.bytes_freed || 0)}
        ${results.backup_created ? '✅ Backup created' : ''}
        ${results.files_failed ? `⚠️ ${results.files_failed} files failed` : ''}
    `;
    
    const notificationType = results.files_failed > 0 ? 'warning' : 'success';
    showNotification(message, notificationType, 8000);
    
    addActivityItem(
        'Cleaning Complete', 
        `${results.files_deleted} files deleted, ${formatBytes(results.bytes_freed || 0)} freed`,
        results.files_failed > 0 ? 'warning' : 'success'
    );
}

// Remove cleaned files from UI
function removeCleanedFilesFromUI(results) {
    // This would need to be implemented based on which files were actually deleted
    // For now, clear selection and suggest a new scan
    clearSelection();
    
    setTimeout(() => {
        if (confirm('Files have been cleaned. Would you like to run a new scan to see updated results?')) {
            startScan();
        }
    }, 2000);
}

// Handle progress updates
function handleProgressUpdate(event) {
    const data = event.detail;
    
    if (data.operation_id === currentScanOperation || 
        data.operation_name.toLowerCase().includes('clean')) {
        // Update any page-specific progress indicators
        console.log('Progress update for cleaner page:', data);
    }
}

// Load last scan results
function loadLastScanResults() {
    // This would load cached results from localStorage or server
    const cached = localStorage.getItem('utac-last-scan-results');
    if (cached) {
        try {
            const results = JSON.parse(cached);
            displayScanResults(results);
            console.log('📋 Loaded cached scan results');
        } catch (error) {
            console.warn('Failed to load cached results:', error);
        }
    }
}

// Load last results button
function loadLastResults() {
    loadLastScanResults();
    if (scanResults.length === 0) {
        showNotification('No previous scan results available', 'info');
    } else {
        showNotification('Previous scan results loaded', 'success');
    }
}

// Export selected files list
function exportSelectedFiles() {
    if (selectedFiles.size === 0) {
        showNotification('No files selected', 'warning');
        return;
    }
    
    const selectedData = Array.from(selectedFiles)
        .map(index => scanResults[index])
        .filter(file => file)
        .map(file => `${file.path}\t${formatBytes(file.size)}\t${file.category}\t${getSafetyLevelText(file.safety_level)}`)
        .join('\n');
    
    const header = 'File Path\tSize\tCategory\tSafety Level\n';
    const csvData = header + selectedData;
    
    const blob = new Blob([csvData], { type: 'text/tab-separated-values' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `utac_selected_files_${new Date().toISOString().slice(0, 10)}.tsv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
    showNotification('Selected files list exported', 'success');
}

console.log('✅ Cleaner JavaScript initialized');