/**
 * Dashboard WebSocket Client
 * Handles real-time communication between dashboards and server
 */

class DashboardClient {
  constructor(dashboardType) {
    this.dashboardType = dashboardType;
    this.socket = null;
    this.connected = false;
    this.listeners = {};
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.init();
  }

  init() {
    // Import socket.io library
    if (typeof io === 'undefined') {
      console.error('Socket.IO library not found. Include it with: <script src="https://cdn.socket.io/4.7.0/socket.io.min.js"></script>');
      return;
    }

    this.socket = io(window.location.origin, {
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: 10000,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.setupEventHandlers();
  }

  setupEventHandlers() {
    // Connection events
    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      this.connected = true;
      this.reconnectAttempts = 0;
      this.emit('connected');
      this.joinDashboard();
    });

    this.socket.on('disconnect', () => {
      console.log('❌ WebSocket disconnected');
      this.connected = false;
      this.emit('disconnected');
    });

    this.socket.on('connection_response', (data) => {
      console.log('Server response:', data);
    });

    this.socket.on('dashboard_joined', (data) => {
      console.log(`Joined dashboard: ${data.dashboard}`);
      this.emit('dashboard_joined', data);
    });

    // Order events
    this.socket.on('new_order', (data) => {
      console.log('New order:', data);
      this.emit('new_order', data);
    });

    this.socket.on('order_updated', (data) => {
      console.log('Order updated:', data);
      this.emit('order_updated', data);
    });

    this.socket.on('order_status_changed', (data) => {
      console.log('Order status changed:', data);
      this.emit('order_status_changed', data);
    });

    // Inventory events
    this.socket.on('inventory_updated', (data) => {
      console.log('Inventory updated:', data);
      this.emit('inventory_updated', data);
    });

    // KPI events
    this.socket.on('kpi_updated', (data) => {
      console.log('KPI updated:', data);
      this.emit('kpi_updated', data);
    });
  }

  joinDashboard() {
    if (!this.socket) return;
    this.socket.emit('join_dashboard', { dashboard: this.dashboardType });
  }

  leaveDashboard() {
    if (!this.socket) return;
    this.socket.emit('leave_dashboard', { dashboard: this.dashboardType });
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  off(event, callback) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
  }

  emit(event, data = null) {
    if (!this.listeners[event]) return;
    this.listeners[event].forEach(callback => callback(data));
  }

  disconnect() {
    this.leaveDashboard();
    if (this.socket) {
      this.socket.disconnect();
    }
  }
}

/**
 * Utility functions for dashboards
 */
const DashboardUtils = {
  // Format currency
  formatCurrency: (amount) => {
    return `₹${Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  },

  // Format time
  formatTime: (date) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  },

  // Format date
  formatDate: (date) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  },

  // Calculate elapsed time
  getElapsedTime: (startTime) => {
    const diff = Date.now() - new Date(startTime).getTime();
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  },

  // Get status badge color
  getStatusColor: (status) => {
    const colors = {
      'queued': 'info',
      'preparing': 'warning',
      'ready': 'success',
      'served': 'success',
      'cancelled': 'error',
      'completed': 'success',
      'pending': 'info',
      'low_stock': 'warning',
      'out_of_stock': 'error'
    };
    return colors[status] || 'info';
  },

  // Show toast notification
  showToast: (message, type = 'info', duration = 3000) => {
    const container = document.getElementById('toast-container') || (() => {
      const div = document.createElement('div');
      div.id = 'toast-container';
      div.className = 'toast-container';
      document.body.appendChild(div);
      return div;
    })();

    const toast = document.createElement('div');
    toast.className = `toast ${type} fade-in`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  // Create loading skeleton
  createSkeleton: (count = 3) => {
    let html = '';
    for (let i = 0; i < count; i++) {
      html += `
        <div class="skeleton skeleton-card">
          <div class="skeleton skeleton-text"></div>
          <div class="skeleton skeleton-text" style="width: 80%;"></div>
          <div class="skeleton skeleton-text" style="width: 60%;"></div>
        </div>
      `;
    }
    return html;
  },

  // Animate number change
  animateNumber: (element, endValue, duration = 500) => {
    const startValue = parseFloat(element.textContent) || 0;
    const startTime = Date.now();
    const range = endValue - startValue;

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const currentValue = startValue + (range * progress);
      element.textContent = Math.round(currentValue);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }
};

/**
 * API Helper for REST calls
 */
const DashboardAPI = {
  async get(endpoint) {
    try {
      const response = await fetch(endpoint);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error(`GET ${endpoint} failed:`, error);
      throw error;
    }
  },

  async post(endpoint, data) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error(`POST ${endpoint} failed:`, error);
      throw error;
    }
  },

  async put(endpoint, data) {
    try {
      const response = await fetch(endpoint, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error(`PUT ${endpoint} failed:`, error);
      throw error;
    }
  }
};

