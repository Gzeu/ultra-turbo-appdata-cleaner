// Ultra-Turbo AppData Cleaner - WebSocket Communication

class UTACWebSocket {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second
        this.heartbeatInterval = null;
        this.isConnected = false;
        
        this.init();
    }
    
    init() {
        console.log('🔌 Initializing WebSocket connection...');
        
        this.socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true
        });
        
        this.setupEventHandlers();
        this.startHeartbeat();
    }
    
    setupEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('✅ WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            this.updateConnectionUI(true);
            this.requestInitialData();
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('❌ WebSocket disconnected:', reason);
            this.isConnected = false;
            this.updateConnectionUI(false);
            
            // Auto-reconnect unless it was intentional
            if (reason !== 'io client disconnect') {
                this.scheduleReconnect();
            }
        });
        
        this.socket.on('connect_error', (error) => {
            console.log('💥 WebSocket connection error:', error);
            this.updateConnectionUI(false);
            this.scheduleReconnect();
        });
        
        // Application-specific events
        this.socket.on('progress_update', this.handleProgressUpdate.bind(this));
        this.socket.on('operation_completed', this.handleOperationCompleted.bind(this));
        this.socket.on('operation_failed', this.handleOperationFailed.bind(this));
        this.socket.on('system_stats_update', this.handleSystemStatsUpdate.bind(this));
        this.socket.on('scan_results', this.handleScanResults.bind(this));
        this.socket.on('cleaning_results', this.handleCleaningResults.bind(this));
        this.socket.on('notification', this.handleNotification.bind(this));
        this.socket.on('error', this.handleError.bind(this));
        
        // Heartbeat response
        this.socket.on('pong', () => {
            console.log('💓 Heartbeat response received');
        });
    }
    
    updateConnectionUI(connected) {
        const statusElement = document.getElementById('connection-status');
        const textElement = document.getElementById('connection-text');
        
        if (!statusElement || !textElement) return;
        
        if (connected) {
            statusElement.className = 'nav-link connection-connected';
            textElement.textContent = 'Connected';
        } else {
            statusElement.className = 'nav-link connection-disconnected';
            textElement.textContent = 'Disconnected';
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('🚫 Max reconnection attempts reached');
            this.updateConnectionUI(false);
            if (typeof showNotification === 'function') {
                showNotification('Connection lost. Please refresh the page.', 'danger', 0);
            }
            return;
        }
        
        this.reconnectAttempts++;
        
        console.log(`🔄 Scheduling reconnection attempt ${this.reconnectAttempts} in ${this.reconnectDelay}ms`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                console.log(`🔄 Reconnection attempt ${this.reconnectAttempts}`);
                this.socket.connect();
                this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30000); // Max 30 seconds
            }
        }, this.reconnectDelay);
    }
    
    startHeartbeat() {
        // Send heartbeat every 30 seconds
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                console.log('💓 Sending heartbeat');
                this.socket.emit('ping');
            }
        }, 30000);
    }
    
    requestInitialData() {
        console.log('📊 Requesting initial data...');
        this.socket.emit('request_system_stats');
    }
    
    // Event handlers
    handleProgressUpdate(data) {
        console.log('📊 Progress update:', data);
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('utac-progress-update', {
            detail: data
        }));
        
        // Update global progress if function exists
        if (typeof updateProgressDisplay === 'function') {
            updateProgressDisplay(data);
        }
    }
    
    handleOperationCompleted(data) {
        console.log('✅ Operation completed:', data);
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('utac-operation-completed', {
            detail: data
        }));
        
        // Show success notification
        if (typeof showNotification === 'function') {
            showNotification(
                `${data.operation_name} completed successfully!`,
                'success'
            );
        }
        
        // Add to activity feed
        if (typeof addActivityItem === 'function') {
            addActivityItem(data.operation_name, data.final_message || 'Operation completed', 'success');
        }
    }
    
    handleOperationFailed(data) {
        console.log('❌ Operation failed:', data);
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('utac-operation-failed', {
            detail: data
        }));
        
        // Show error notification
        if (typeof showNotification === 'function') {
            showNotification(
                `${data.operation_name} failed: ${data.error}`,
                'danger'
            );
        }
        
        // Add to activity feed
        if (typeof addActivityItem === 'function') {
            addActivityItem(data.operation_name, `Failed: ${data.error}`, 'error');
        }
    }
    
    handleSystemStatsUpdate(data) {
        console.log('📊 System stats update:', data);
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('utac-system-stats', {
            detail: data
        }));
        
        // Update dashboard if function exists
        if (typeof updateSystemStatsDisplay === 'function') {
            updateSystemStatsDisplay(data.stats);
        }
    }
    
    handleScanResults(data) {
        console.log('🔍 Scan results received:', data);
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('utac-scan-results', {
            detail: data
        }));
        
        // Update cleaner page if function exists
        if (typeof displayScanResults === 'function') {
            displayScanResults(data.results);
        }
    }
    
    handleCleaningResults(data) {
        console.log('🧹 Cleaning results received:', data);
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('utac-cleaning-results', {
            detail: data
        }));
        
        // Show cleaning summary
        if (typeof showCleaningSummary === 'function') {
            showCleaningSummary(data.results);
        }
    }
    
    handleNotification(data) {
        console.log('🔔 Notification received:', data);
        
        if (typeof showNotification === 'function') {
            showNotification(data.message, data.type);
        }
    }
    
    handleError(data) {
        console.error('💥 Server error:', data);
        
        if (typeof showNotification === 'function') {
            showNotification(`Server Error: ${data.message}`, 'danger');
        }
    }
    
    // Public methods
    emit(event, data) {
        if (this.isConnected) {
            this.socket.emit(event, data);
        } else {
            console.warn('⚠️ Cannot emit event - WebSocket not connected:', event);
        }
    }
    
    disconnect() {
        console.log('🔌 Manually disconnecting WebSocket');
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        if (this.socket) {
            this.socket.disconnect();
        }
        this.isConnected = false;
    }
    
    reconnect() {
        console.log('🔄 Manually reconnecting WebSocket');
        this.reconnectAttempts = 0;
        this.socket.connect();
    }
    
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            socketId: this.socket ? this.socket.id : null
        };
    }
}

// Initialize WebSocket when script loads
let utacWebSocket = null;

document.addEventListener('DOMContentLoaded', function() {
    utacWebSocket = new UTACWebSocket();
    
    // Make it globally available
    window.utacWebSocket = utacWebSocket;
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (utacWebSocket) {
        utacWebSocket.disconnect();
    }
});