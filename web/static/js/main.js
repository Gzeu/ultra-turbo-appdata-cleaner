// Ultra-Turbo AppData Cleaner - Main JavaScript Functions

// Global variables
let socket = null;
let currentTheme = 'dark';
let notificationCount = 0;

// Initialize main application
function initializeApp() {
    console.log('🚀 Initializing Ultra-Turbo AppData Cleaner Web Interface');
    
    // Initialize theme
    initializeTheme();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize WebSocket
    initializeWebSocket();
    
    // Load initial data
    loadInitialData();
}

// Theme management
function initializeTheme() {
    const savedTheme = localStorage.getItem('utac-theme') || 'dark';
    setTheme(savedTheme);
}

function setTheme(theme) {
    currentTheme = theme;
    document.body.setAttribute('data-bs-theme', theme);
    
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'bi bi-sun';
        } else {
            icon.className = 'bi bi-moon';
        }
    }
    
    localStorage.setItem('utac-theme', theme);
}

function toggleTheme() {
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// Event listeners
function setupEventListeners() {
    // Theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Global keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl+Shift+D for dashboard
        if (event.ctrlKey && event.shiftKey && event.key === 'D') {
            window.location.href = '/';
        }
        // Ctrl+Shift+C for cleaner
        else if (event.ctrlKey && event.shiftKey && event.key === 'C') {
            window.location.href = '/cleaner';
        }
        // Ctrl+Shift+S for settings
        else if (event.ctrlKey && event.shiftKey && event.key === 'S') {
            event.preventDefault();
            window.location.href = '/settings';
        }
    });
}

// WebSocket initialization
function initializeWebSocket() {
    if (socket && socket.connected) {
        socket.disconnect();
    }
    
    console.log('🔌 Connecting to WebSocket...');
    socket = io();
    
    socket.on('connect', function() {
        console.log('✅ WebSocket connected');
        updateConnectionStatus(true);
    });
    
    socket.on('disconnect', function() {
        console.log('❌ WebSocket disconnected');
        updateConnectionStatus(false);
    });
    
    socket.on('reconnect', function() {
        console.log('🔄 WebSocket reconnected');
        updateConnectionStatus(true);
        loadInitialData();
    });
    
    // Progress updates
    socket.on('progress_update', handleProgressUpdate);
    
    // Operation completion
    socket.on('operation_completed', handleOperationCompleted);
    socket.on('operation_failed', handleOperationFailed);
    
    // System updates
    socket.on('system_stats_update', handleSystemStatsUpdate);
    
    // Notifications
    socket.on('notification', handleNotification);
    socket.on('error', handleError);
}

// Connection status management
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    const textElement = document.getElementById('connection-text');
    const iconElement = statusElement.querySelector('i');
    
    if (connected) {
        statusElement.className = 'nav-link connection-connected';
        textElement.textContent = 'Connected';
        iconElement.className = 'bi bi-circle-fill text-success';
    } else {
        statusElement.className = 'nav-link connection-disconnected';
        textElement.textContent = 'Disconnected';
        iconElement.className = 'bi bi-circle-fill text-danger';
    }
}

// Progress handling
function handleProgressUpdate(data) {
    console.log('📊 Progress update:', data);
    
    // Update progress modal if visible
    const progressModal = document.getElementById('progressModal');
    if (progressModal && progressModal.classList.contains('show')) {
        updateProgressModal(data);
    }
    
    // Update any page-specific progress indicators
    if (typeof updatePageProgress === 'function') {
        updatePageProgress(data);
    }
}

function updateProgressModal(data) {
    document.getElementById('progress-operation-name').textContent = data.operation_name;
    document.getElementById('progress-percentage').textContent = data.percentage.toFixed(1) + '%';
    document.getElementById('progress-current-item').textContent = data.current_item || '-';
    document.getElementById('progress-status-message').textContent = data.status_message || '-';
    document.getElementById('progress-items-processed').textContent = data.items_processed || 0;
    document.getElementById('progress-items-failed').textContent = data.items_failed || 0;
    document.getElementById('progress-elapsed-time').textContent = formatDuration(data.elapsed_seconds || 0);
    
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = data.percentage + '%';
    
    // Update close button state
    const closeBtn = document.getElementById('progress-close-btn');
    if (data.status === 'completed' || data.status === 'failed') {
        closeBtn.disabled = false;
        progressBar.classList.remove('progress-bar-animated');
    }
}

// Show progress modal
function showProgressModal(operationName = 'Operation') {
    const modal = new bootstrap.Modal(document.getElementById('progressModal'));
    
    // Reset modal content
    document.getElementById('progress-operation-name').textContent = operationName;
    document.getElementById('progress-percentage').textContent = '0%';
    document.getElementById('progress-current-item').textContent = '-';
    document.getElementById('progress-status-message').textContent = 'Starting...';
    document.getElementById('progress-items-processed').textContent = '0';
    document.getElementById('progress-items-failed').textContent = '0';
    document.getElementById('progress-elapsed-time').textContent = '0s';
    
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = '0%';
    progressBar.classList.add('progress-bar-animated');
    
    document.getElementById('progress-close-btn').disabled = true;
    
    modal.show();
}

// Hide progress modal
function hideProgressModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
    if (modal) {
        modal.hide();
    }
}

// Operation completion handlers
function handleOperationCompleted(data) {
    console.log('✅ Operation completed:', data);
    
    showNotification(
        `${data.operation_name} completed successfully!`,
        'success'
    );
    
    addActivityItem(data.operation_name, 'Operation completed', 'success');
    
    // Enable close button in progress modal
    document.getElementById('progress-close-btn').disabled = false;
    
    // Auto-hide progress modal after delay
    setTimeout(() => {
        hideProgressModal();
    }, 2000);
}

function handleOperationFailed(data) {
    console.log('❌ Operation failed:', data);
    
    showNotification(
        `${data.operation_name} failed: ${data.error}`,
        'danger'
    );
    
    addActivityItem(data.operation_name, `Failed: ${data.error}`, 'error');
    
    // Enable close button
    document.getElementById('progress-close-btn').disabled = false;
}

// System stats updates
function handleSystemStatsUpdate(data) {
    console.log('📊 System stats update:', data);
    
    if (typeof updateSystemStats === 'function') {
        updateSystemStats(data.stats);
    }
}

// Notifications
function showNotification(message, type = 'info', duration = 5000) {
    const notificationsArea = document.getElementById('notifications-area');
    if (!notificationsArea) return;
    
    notificationCount++;
    const notificationId = 'notification-' + notificationCount;
    
    const alertClass = {
        'info': 'alert-primary',
        'success': 'alert-success', 
        'warning': 'alert-warning',
        'danger': 'alert-danger'
    }[type] || 'alert-primary';
    
    const icon = {
        'info': 'bi-info-circle',
        'success': 'bi-check-circle',
        'warning': 'bi-exclamation-triangle',
        'danger': 'bi-x-circle'
    }[type] || 'bi-info-circle';
    
    const notification = document.createElement('div');
    notification.id = notificationId;
    notification.className = `alert ${alertClass} alert-dismissible notification`;
    notification.innerHTML = `
        <i class="bi ${icon}"></i>
        ${message}
        <button type="button" class="btn-close" onclick="closeNotification('${notificationId}')"></button>
    `;
    
    notificationsArea.appendChild(notification);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            closeNotification(notificationId);
        }, duration);
    }
}

function closeNotification(notificationId) {
    const notification = document.getElementById(notificationId);
    if (notification) {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
}

function handleNotification(data) {
    showNotification(data.message, data.type);
}

function handleError(data) {
    console.error('❌ Server error:', data);
    showNotification(data.message, 'danger');
}

// Activity feed
function addActivityItem(title, message, type = 'info') {
    const activityFeed = document.getElementById('activity-feed');
    if (!activityFeed) return;
    
    // Remove "no activity" placeholder if exists
    const placeholder = activityFeed.querySelector('.text-muted');
    if (placeholder && placeholder.textContent.includes('No recent activity')) {
        placeholder.remove();
    }
    
    const timestamp = new Date().toLocaleTimeString();
    const icon = {
        'info': 'bi-info-circle',
        'success': 'bi-check-circle',
        'warning': 'bi-exclamation-triangle', 
        'error': 'bi-x-circle'
    }[type] || 'bi-info-circle';
    
    const activityItem = document.createElement('div');
    activityItem.className = `activity-item ${type} fade-in-up`;
    activityItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <div class="fw-bold">
                    <i class="bi ${icon}"></i>
                    ${title}
                </div>
                <div class="small text-muted">${message}</div>
            </div>
            <small class="text-muted">${timestamp}</small>
        </div>
    `;
    
    activityFeed.insertBefore(activityItem, activityFeed.firstChild);
    
    // Limit activity items (keep only last 20)
    const items = activityFeed.querySelectorAll('.activity-item');
    if (items.length > 20) {
        items[items.length - 1].remove();
    }
}

function clearActivity() {
    const activityFeed = document.getElementById('activity-feed');
    if (activityFeed) {
        activityFeed.innerHTML = `
            <div class="text-muted text-center py-3">
                <i class="bi bi-clock-history fs-1 mb-2 d-block"></i>
                No recent activity
            </div>
        `;
    }
}

// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    if (seconds < 60) {
        return Math.round(seconds) + 's';
    } else if (seconds < 3600) {
        return Math.round(seconds / 60) + 'm';
    } else {
        return Math.round(seconds / 3600) + 'h';
    }
}

function formatFileAge(ageInDays) {
    if (ageInDays < 1) {
        return 'Today';
    } else if (ageInDays < 7) {
        return Math.round(ageInDays) + 'd';
    } else if (ageInDays < 30) {
        return Math.round(ageInDays / 7) + 'w';
    } else if (ageInDays < 365) {
        return Math.round(ageInDays / 30) + 'mo';
    } else {
        return Math.round(ageInDays / 365) + 'y';
    }
}

function getSafetyLevelClass(level) {
    const classes = {
        1: 'safety-very-safe',
        2: 'safety-safe',
        3: 'safety-moderate',
        4: 'safety-risky',
        5: 'safety-dangerous'
    };
    return classes[level] || 'bg-secondary';
}

function getSafetyLevelText(level) {
    const texts = {
        1: 'Very Safe',
        2: 'Safe',
        3: 'Moderate',
        4: 'Risky',
        5: 'Dangerous'
    };
    return texts[level] || 'Unknown';
}

function getFileTypeIcon(extension, category) {
    // Category-based icons
    if (category === 'temp') return 'bi-clock';
    if (category === 'cache') return 'bi-database';
    if (category === 'log') return 'bi-journal-text';
    if (category === 'backup') return 'bi-archive';
    
    // Extension-based icons
    const iconMap = {
        '.txt': 'bi-file-text',
        '.log': 'bi-journal-text',
        '.tmp': 'bi-clock',
        '.cache': 'bi-database',
        '.bak': 'bi-archive',
        '.old': 'bi-archive'
    };
    
    return iconMap[extension] || 'bi-file-earmark';
}

// API calls
async function makeAPICall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showNotification(`API Error: ${error.message}`, 'danger');
        throw error;
    }
}

// Load initial data
function loadInitialData() {
    // Load system info if on dashboard
    if (window.location.pathname === '/' && typeof loadSystemInfo === 'function') {
        loadSystemInfo();
    }
    
    // Load settings if on settings page
    if (window.location.pathname === '/settings' && typeof loadCurrentSettings === 'function') {
        loadCurrentSettings();
    }
}

// Global quick actions
function quickScan() {
    console.log('🔍 Starting quick scan...');
    showProgressModal('Quick System Scan');
    
    makeAPICall('/api/scan/quick', { method: 'POST' })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            console.log('Quick scan started:', data.operation_id);
            addActivityItem('Quick Scan', 'Scan started', 'info');
        })
        .catch(error => {
            hideProgressModal();
            showNotification(`Quick scan failed: ${error.message}`, 'danger');
        });
}

function quickClean() {
    if (confirm('Start quick cleaning of temporary files?\n\nThis will:\n• Clean temp files older than 7 days\n• Clear browser cache\n• Create automatic backup')) {
        console.log('🧹 Starting quick clean...');
        showProgressModal('Quick Clean');
        
        makeAPICall('/api/clean/temp', {
            method: 'POST',
            body: JSON.stringify({ max_age_days: 7, create_backup: true })
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            console.log('Quick clean started:', data.operation_id);
            addActivityItem('Quick Clean', 'Cleaning started', 'info');
        })
        .catch(error => {
            hideProgressModal();
            showNotification(`Quick clean failed: ${error.message}`, 'danger');
        });
    }
}

function fullScan() {
    window.location.href = '/cleaner?action=full_scan';
}

function showSettings() {
    window.location.href = '/settings';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && socket && socket.connected) {
        // Refresh data when page becomes visible
        loadInitialData();
    }
});

// Global error handler
window.addEventListener('error', function(event) {
    console.error('💥 Global error:', event.error);
    showNotification(`Unexpected error: ${event.error.message}`, 'danger');
});

// Export global functions
window.UTAC = {
    showNotification,
    makeAPICall,
    formatBytes,
    formatDuration,
    addActivityItem,
    showProgressModal,
    hideProgressModal
};