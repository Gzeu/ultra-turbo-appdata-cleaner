// Dashboard specific JavaScript functions

let systemStatsChart = null;
let cleanupPotentialChart = null;
let refreshInterval = null;

// Initialize dashboard
function initializeDashboard() {
    console.log('📊 Initializing dashboard...');
    
    // Initialize charts
    initializeCharts();
    
    // Setup auto-refresh
    setupSystemMonitoring();
    
    // Load initial data
    loadSystemInfo();
    estimateCleanup();
}

// Initialize Chart.js charts
function initializeCharts() {
    // Storage Analysis Chart
    const storageCtx = document.getElementById('storageChart');
    if (storageCtx) {
        systemStatsChart = new Chart(storageCtx, {
            type: 'doughnut',
            data: {
                labels: ['Used Space', 'Free Space'],
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#dc3545', '#198754'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + formatBytes(context.raw * 1024 * 1024 * 1024);
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Cleanup Potential Chart
    const cleanupCtx = document.getElementById('cleanupChart');
    if (cleanupCtx) {
        cleanupPotentialChart = new Chart(cleanupCtx, {
            type: 'pie',
            data: {
                labels: ['Temp Files', 'Cache', 'Logs', 'Other'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#ffc107', '#0dcaf0', '#198754', '#6c757d'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + formatBytes(context.raw * 1024 * 1024);
                            }
                        }
                    }
                }
            }
        });
    }
}

// Load system information
function loadSystemInfo() {
    makeAPICall('/api/system/info')
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            updateSystemStatsDisplay(data);
            updateChartsWithSystemData(data);
        })
        .catch(error => {
            console.error('Error loading system info:', error);
            showNotification('Failed to load system information', 'warning');
        });
}

// Update system statistics display
function updateSystemStatsDisplay(systemData) {
    // Update memory card
    const memoryPercentage = document.getElementById('memory-percentage');
    if (memoryPercentage && systemData.memory) {
        memoryPercentage.textContent = systemData.memory.percentage + '%';
        
        const memoryCard = memoryPercentage.closest('.card');
        if (systemData.memory.percentage > 80) {
            memoryCard.className = 'card bg-danger text-white';
        } else if (systemData.memory.percentage > 60) {
            memoryCard.className = 'card bg-warning text-dark';
        } else {
            memoryCard.className = 'card bg-primary text-white';
        }
    }
    
    // Update disk card
    const diskPercentage = document.getElementById('disk-percentage');
    if (diskPercentage && systemData.disk) {
        diskPercentage.textContent = systemData.disk.percentage + '%';
        
        const diskCard = diskPercentage.closest('.card');
        if (systemData.disk.percentage > 90) {
            diskCard.className = 'card bg-danger text-white';
        } else if (systemData.disk.percentage > 75) {
            diskCard.className = 'card bg-warning text-dark';
        } else {
            diskCard.className = 'card bg-info text-white';
        }
    }
    
    // Update CPU card
    const cpuPercentage = document.getElementById('cpu-percentage');
    if (cpuPercentage && systemData.cpu) {
        cpuPercentage.textContent = systemData.cpu.percentage + '%';
    }
    
    // Update uptime
    const uptimeElement = document.getElementById('system-uptime');
    if (uptimeElement && systemData.system) {
        uptimeElement.textContent = systemData.system.uptime_hours + 'h';
    }
    
    // Update AppData status
    updateAppDataStatus(systemData.appdata_paths);
}

// Update charts with system data
function updateChartsWithSystemData(systemData) {
    if (systemStatsChart && systemData.disk) {
        const usedGB = systemData.disk.used_gb;
        const freeGB = systemData.disk.free_gb;
        
        systemStatsChart.data.datasets[0].data = [usedGB, freeGB];
        systemStatsChart.update('none');
    }
}

// Update AppData status display
function updateAppDataStatus(appdataPaths) {
    const statusContainer = document.getElementById('appdata-status');
    if (!statusContainer || !appdataPaths) return;
    
    let statusHTML = '';
    
    Object.entries(appdataPaths).forEach(([name, info]) => {
        const badgeClass = info.accessible ? 'bg-success' : 'bg-danger';
        const badgeText = info.accessible ? 'Accessible' : 'Blocked';
        
        statusHTML += `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="fw-bold">${name.charAt(0).toUpperCase() + name.slice(1)}:</span>
                <span class="badge ${badgeClass}">${badgeText}</span>
            </div>
        `;
        
        if (info.accessible && info.size_mb !== undefined) {
            statusHTML += `
                <div class="small text-muted mb-3">
                    ${info.file_count || 0} files, ${info.size_mb}MB
                </div>
            `;
        }
    });
    
    statusContainer.innerHTML = statusHTML;
}

// Estimate cleanup potential
function estimateCleanup() {
    console.log('🧮 Estimating cleanup potential...');
    
    // Show loading state
    const estimateBtn = document.querySelector('button[onclick="estimateCleanup()"]');
    if (estimateBtn) {
        const originalText = estimateBtn.innerHTML;
        estimateBtn.innerHTML = '<i class="bi bi-arrow-repeat spin"></i> Calculating...';
        estimateBtn.disabled = true;
        
        // Quick estimation API call
        makeAPICall('/api/scan/estimate', { method: 'POST' })
            .then(data => {
                updateCleanupChart(data);
            })
            .catch(error => {
                console.error('Cleanup estimation failed:', error);
            })
            .finally(() => {
                estimateBtn.innerHTML = originalText;
                estimateBtn.disabled = false;
            });
    }
}

// Update cleanup potential chart
function updateCleanupChart(estimationData) {
    if (!cleanupPotentialChart || !estimationData) return;
    
    const categories = estimationData.categories || {};
    const data = [
        categories.temp || 0,
        categories.cache || 0, 
        categories.log || 0,
        categories.other || 0
    ];
    
    cleanupPotentialChart.data.datasets[0].data = data;
    cleanupPotentialChart.update();
}

// Setup system monitoring
function setupSystemMonitoring() {
    // Auto-refresh every 30 seconds
    refreshInterval = setInterval(() => {
        if (document.visibilityState === 'visible') {
            loadSystemInfo();
        }
    }, 30000);
    
    // Stop refresh when page is not visible
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
        } else {
            if (!refreshInterval) {
                setupSystemMonitoring();
            }
        }
    });
}

// Quick action functions for dashboard
function scanAppData() {
    console.log('📁 Starting AppData scan...');
    showProgressModal('AppData Scan');
    
    makeAPICall('/api/scan/appdata', { method: 'POST' })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            addActivityItem('AppData Scan', 'Scan started', 'info');
        })
        .catch(error => {
            hideProgressModal();
            showNotification(`AppData scan failed: ${error.message}`, 'danger');
        });
}

// Handle WebSocket events specific to dashboard
window.addEventListener('utac-system-stats', function(event) {
    updateSystemStatsDisplay(event.detail.stats);
});

window.addEventListener('utac-operation-completed', function(event) {
    const data = event.detail;
    
    // Update relevant dashboard elements
    if (data.operation_name.includes('Scan')) {
        // Refresh cleanup estimation after scan
        setTimeout(() => {
            estimateCleanup();
        }, 1000);
    }
    
    if (data.operation_name.includes('Clean')) {
        // Refresh system info after cleaning
        setTimeout(() => {
            loadSystemInfo();
        }, 2000);
    }
});

// Cleanup when leaving page
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

// CSS animation for spinning icon
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .spin {
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);

console.log('✅ Dashboard JavaScript initialized');