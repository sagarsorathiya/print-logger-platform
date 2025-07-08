// Dashboard JavaScript
class PrintTrackingDashboard {
    constructor() {
        this.apiBase = 'http://localhost:8000/api/v1';
        this.charts = {};
        this.refreshInterval = 30000; // 30 seconds
        this.currentSection = 'dashboard';

        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupEventHandlers();
        this.initializeCharts();
        this.loadDashboardData();
        this.startAutoRefresh();
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link[href^="#"]');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = link.getAttribute('href').substring(1);
                this.showSection(sectionId);
                this.updateActiveNav(link);
            });
        });
    }

    setupEventHandlers() {
        // Refresh button
        const refreshBtn = document.querySelector('[onclick="refreshDashboard()"]');
        if (refreshBtn) {
            refreshBtn.onclick = () => this.refreshDashboard();
        }
    }

    showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.add('d-none');
        });

        // Show target section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.remove('d-none');
            this.currentSection = sectionId;

            // Load section-specific data
            this.loadSectionData(sectionId);
        }
    }

    updateActiveNav(activeLink) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        activeLink.classList.add('active');
    }

    async loadSectionData(sectionId) {
        switch (sectionId) {
            case 'dashboard':
                await this.loadDashboardData();
                break;
            case 'print-jobs':
                await this.loadPrintJobs();
                break;
            case 'agents':
                await this.loadAgents();
                break;
            case 'reports':
                await this.loadReports();
                break;
            case 'users':
                await this.loadUsers();
                break;
        }
    }

    async loadDashboardData() {
        try {
            this.showLoading();

            // Load statistics
            const stats = await this.fetchWithAuth('/reports/overview');
            this.updateStatistics(stats);

            // Load recent print jobs
            const recentJobs = await this.fetchWithAuth('/print-jobs?limit=10');
            this.updateRecentJobs(recentJobs);

            // Update charts
            await this.updateCharts();

            this.hideLoading();
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
            this.hideLoading();
        }
    }

    updateStatistics(stats) {
        if (!stats) {
            stats = {
                total_jobs: 0,
                total_pages: 0,
                color_pages: 0,
                unique_users: 0
            };
        }

        document.getElementById('total-jobs-today').textContent = stats.total_jobs || 0;
        document.getElementById('total-pages-today').textContent = stats.total_pages || 0;
        document.getElementById('color-pages-today').textContent = stats.color_pages || 0;
        document.getElementById('active-agents').textContent = stats.unique_users || 0;
    }

    updateRecentJobs(jobs) {
        const tbody = document.getElementById('recent-jobs');

        if (!jobs || jobs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No recent activity</td></tr>';
            return;
        }

        tbody.innerHTML = jobs.map(job => `
            <tr>
                <td>${this.formatTime(job.print_time || job.created_at)}</td>
                <td>${job.username}</td>
                <td>${job.printer_name}</td>
                <td>${job.document_name}</td>
                <td>${job.pages}</td>
                <td>
                    ${job.is_color ? '<span class="badge print-color">Color</span>' : '<span class="badge print-bw">B&W</span>'}
                    ${job.is_duplex ? '<span class="badge print-duplex ms-1">Duplex</span>' : ''}
                </td>
            </tr>
        `).join('');
    }

    initializeCharts() {
        // Print Trend Chart
        const trendCtx = document.getElementById('printTrendChart');
        if (trendCtx) {
            this.charts.printTrend = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Total Pages',
                        data: [],
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Color Pages',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Color Chart
        const colorCtx = document.getElementById('colorChart');
        if (colorCtx) {
            this.charts.colorChart = new Chart(colorCtx, {
                type: 'doughnut',
                data: {
                    labels: ['B&W Pages', 'Color Pages'],
                    datasets: [{
                        data: [0, 0],
                        backgroundColor: ['#6c757d', '#ffc107'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    async updateCharts() {
        try {
            // Get trend data
            const trendData = await this.fetchWithAuth('/reports/trends?period=daily');

            if (this.charts.printTrend && trendData && trendData.data_points) {
                this.charts.printTrend.data.labels = trendData.data_points.map(d => d.date);
                this.charts.printTrend.data.datasets[0].data = trendData.data_points.map(d => d.total_pages);
                this.charts.printTrend.data.datasets[1].data = trendData.data_points.map(d => d.color_pages);
                this.charts.printTrend.update();
            }

            // Update color chart
            const stats = await this.fetchWithAuth('/reports/overview');
            if (this.charts.colorChart && stats) {
                const bwPages = (stats.total_pages || 0) - (stats.color_pages || 0);
                this.charts.colorChart.data.datasets[0].data = [bwPages, stats.color_pages || 0];
                this.charts.colorChart.update();
            }
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }

    async loadPrintJobs() {
        // Placeholder for print jobs loading
        const section = document.getElementById('print-jobs');
        section.innerHTML = `
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">Print Jobs</h1>
                <div class="btn-toolbar mb-2 mb-md-0">
                    <button type="button" class="btn btn-sm btn-primary">
                        <i class="fas fa-download"></i> Export
                    </button>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <p class="text-muted">Print jobs interface will be implemented here.</p>
                    <p>Features:</p>
                    <ul>
                        <li>Search and filter print jobs</li>
                        <li>View job details</li>
                        <li>Export to CSV/Excel</li>
                        <li>Real-time updates</li>
                    </ul>
                </div>
            </div>
        `;
    }

    async loadAgents() {
        // Placeholder for agents loading
        const section = document.getElementById('agents');
        section.innerHTML = `
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">Agent Management</h1>
                <div class="btn-toolbar mb-2 mb-md-0">
                    <button type="button" class="btn btn-sm btn-primary">
                        <i class="fas fa-sync-alt"></i> Sync All
                    </button>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <p class="text-muted">Agent management interface will be implemented here.</p>
                    <p>Features:</p>
                    <ul>
                        <li>View agent status</li>
                        <li>Update agent configurations</li>
                        <li>Download agent installer</li>
                        <li>Monitor agent health</li>
                    </ul>
                </div>
            </div>
        `;
    }

    async loadReports() {
        // Placeholder for reports loading
        const section = document.getElementById('reports');
        section.innerHTML = `
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">Reports</h1>
                <div class="btn-toolbar mb-2 mb-md-0">
                    <button type="button" class="btn btn-sm btn-primary">
                        <i class="fas fa-chart-bar"></i> Generate Report
                    </button>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <p class="text-muted">Reports interface will be implemented here.</p>
                    <p>Features:</p>
                    <ul>
                        <li>Custom report generation</li>
                        <li>Scheduled reports</li>
                        <li>Statistical analysis</li>
                        <li>Cost analysis</li>
                    </ul>
                </div>
            </div>
        `;
    }

    async loadUsers() {
        try {
            // Get users data
            const users = await this.fetchWithAuth('/users');

            const section = document.getElementById('users');
            section.innerHTML = `
                <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                    <h1 class="h2">User Management</h1>
                    <div class="btn-toolbar mb-2 mb-md-0">
                        <button type="button" class="btn btn-sm btn-primary" onclick="dashboard.showCreateUserModal()">
                            <i class="fas fa-user-plus"></i> Add User
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-secondary ms-2" onclick="dashboard.syncLDAPUsers()">
                            <i class="fas fa-sync"></i> Sync LDAP
                        </button>
                    </div>
                </div>
                
                <!-- Search and Filters -->
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <input type="text" class="form-control" id="userSearch" placeholder="Search users..." 
                                       onkeyup="dashboard.filterUsers()">
                            </div>
                            <div class="col-md-2">
                                <select class="form-select" id="roleFilter" onchange="dashboard.filterUsers()">
                                    <option value="">All Roles</option>
                                    <option value="admin">Admin</option>
                                    <option value="user">User</option>
                                    <option value="viewer">Viewer</option>
                                </select>
                            </div>
                            <div class="col-md-2">
                                <select class="form-select" id="statusFilter" onchange="dashboard.filterUsers()">
                                    <option value="">All Status</option>
                                    <option value="true">Active</option>
                                    <option value="false">Inactive</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Users Table -->
                <div class="card">
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Username</th>
                                        <th>Full Name</th>
                                        <th>Email</th>
                                        <th>Role</th>
                                        <th>Status</th>
                                        <th>Type</th>
                                        <th>Last Login</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="usersTableBody">
                                    ${this.renderUsersTable(users || [])}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading users:', error);
            const section = document.getElementById('users');
            section.innerHTML = `
                <div class="alert alert-danger">
                    <h4>Error Loading Users</h4>
                    <p>Unable to load user data. Please try again later.</p>
                </div>
            `;
        }
    }

    renderUsersTable(users) {
        if (!users || users.length === 0) {
            return '<tr><td colspan="8" class="text-center text-muted">No users found</td></tr>';
        }

        return users.map(user => `
            <tr>
                <td>
                    <strong>${user.username}</strong>
                    ${user.is_ldap_user ? '<span class="badge bg-info ms-1">LDAP</span>' : ''}
                </td>
                <td>${user.full_name || '-'}</td>
                <td>${user.email || '-'}</td>
                <td>
                    <span class="badge bg-${this.getRoleBadgeColor(user.role)}">${user.role}</span>
                </td>
                <td>
                    <span class="badge bg-${user.is_active ? 'success' : 'secondary'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>${user.is_ldap_user ? 'LDAP' : 'Local'}</td>
                <td>${user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="dashboard.viewUser(${user.id})" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-secondary" onclick="dashboard.editUser(${user.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        ${!user.is_ldap_user ? `
                        <button class="btn btn-outline-warning" onclick="dashboard.resetPassword(${user.id})" title="Reset Password">
                            <i class="fas fa-key"></i>
                        </button>
                        ` : ''}
                        <button class="btn btn-outline-danger" onclick="dashboard.deleteUser(${user.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    getRoleBadgeColor(role) {
        switch (role) {
            case 'admin': return 'danger';
            case 'user': return 'primary';
            case 'viewer': return 'secondary';
            default: return 'secondary';
        }
    }

    async fetchWithAuth(endpoint, options = {}) {
        try {
            const response = await fetch(this.apiBase + endpoint, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            return null;
        }
    }

    getAuthToken() {
        // For demo purposes, return null (no authentication required)
        // In production, this would return the stored JWT token
        return localStorage.getItem('authToken');
    }

    refreshDashboard() {
        if (this.currentSection === 'dashboard') {
            this.loadDashboardData();
        } else {
            this.loadSectionData(this.currentSection);
        }
    }

    startAutoRefresh() {
        setInterval(() => {
            if (this.currentSection === 'dashboard') {
                this.loadDashboardData();
            }
        }, this.refreshInterval);
    }

    showLoading() {
        const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
        const modalElement = document.getElementById('loadingModal');

        // Remove aria-hidden when modal is shown to fix accessibility warning
        modalElement.addEventListener('shown.bs.modal', function () {
            modalElement.removeAttribute('aria-hidden');
        });

        loadingModal.show();
    }

    hideLoading() {
        const loadingModal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (loadingModal) {
            loadingModal.hide();
        }
    }

    showError(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-danger border-0';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to toast container
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        container.appendChild(toast);

        const toastInstance = new bootstrap.Toast(toast);
        toastInstance.show();

        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    formatTime(timestamp) {
        if (!timestamp) return 'N/A';

        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) { // Less than 1 minute
            return 'Just now';
        } else if (diff < 3600000) { // Less than 1 hour
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        } else if (diff < 86400000) { // Less than 1 day
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    // User Management Functions
    async filterUsers() {
        const search = document.getElementById('userSearch').value;
        const role = document.getElementById('roleFilter').value;
        const status = document.getElementById('statusFilter').value;

        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (role) params.append('role', role);
        if (status) params.append('is_active', status);

        try {
            const users = await this.fetchWithAuth(`/users?${params.toString()}`);
            document.getElementById('usersTableBody').innerHTML = this.renderUsersTable(users || []);
        } catch (error) {
            console.error('Error filtering users:', error);
        }
    }

    showCreateUserModal() {
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="createUserModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Create New User</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="createUserForm">
                                <div class="mb-3">
                                    <label for="username" class="form-label">Username *</label>
                                    <input type="text" class="form-control" id="username" required>
                                </div>
                                <div class="mb-3">
                                    <label for="fullName" class="form-label">Full Name</label>
                                    <input type="text" class="form-control" id="fullName">
                                </div>
                                <div class="mb-3">
                                    <label for="email" class="form-label">Email</label>
                                    <input type="email" class="form-control" id="email">
                                </div>
                                <div class="mb-3">
                                    <label for="role" class="form-label">Role</label>
                                    <select class="form-select" id="role">
                                        <option value="user">User</option>
                                        <option value="admin">Admin</option>
                                        <option value="viewer">Viewer</option>
                                    </select>
                                </div>
                                <div class="mb-3" id="passwordSection">
                                    <label for="password" class="form-label">Password *</label>
                                    <input type="password" class="form-control" id="password" required>
                                </div>
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="isActive" checked>
                                    <label class="form-check-label" for="isActive">Active</label>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="dashboard.createUser()">Create User</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to DOM if it doesn't exist
        if (!document.getElementById('createUserModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('createUserModal'));
        modal.show();
    }

    async createUser() {
        const form = document.getElementById('createUserForm');
        const formData = new FormData(form);

        const userData = {
            username: document.getElementById('username').value,
            full_name: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            role: document.getElementById('role').value,
            password: document.getElementById('password').value,
            is_active: document.getElementById('isActive').checked
        };

        try {
            await this.fetchWithAuth('/users/', {
                method: 'POST',
                body: JSON.stringify(userData)
            });

            // Close modal and refresh users
            bootstrap.Modal.getInstance(document.getElementById('createUserModal')).hide();
            this.loadUsers();

            this.showAlert('User created successfully', 'success');
        } catch (error) {
            console.error('Error creating user:', error);
            this.showAlert('Error creating user', 'danger');
        }
    } async viewUser(userId) {
        try {
            const user = await this.fetchWithAuth(`/users/${userId}`);
            let history = null;

            // Try to get print history, but don't fail if it errors
            try {
                history = await this.fetchWithAuth(`/users/${userId}/print-history?limit=10`);
            } catch (error) {
                console.warn('Could not load print history:', error);
                history = null;
            }

            // Handle case where history might be null due to API error
            const stats = history?.statistics || {
                total_jobs: 0,
                total_pages: 0,
                color_pages: 0,
                bw_pages: 0
            };

            const printJobs = history?.print_jobs || [];

            const modalHtml = `
                <div class="modal fade" id="viewUserModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">User Details - ${user.username}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h6>User Information</h6>
                                        <table class="table table-sm">
                                            <tr><td><strong>Username:</strong></td><td>${user.username}</td></tr>
                                            <tr><td><strong>Full Name:</strong></td><td>${user.full_name || '-'}</td></tr>
                                            <tr><td><strong>Email:</strong></td><td>${user.email || '-'}</td></tr>
                                            <tr><td><strong>Role:</strong></td><td>${user.role}</td></tr>
                                            <tr><td><strong>Status:</strong></td><td>${user.is_active ? 'Active' : 'Inactive'}</td></tr>
                                            <tr><td><strong>Type:</strong></td><td>${user.is_ldap_user ? 'LDAP' : 'Local'}</td></tr>
                                            <tr><td><strong>Last Login:</strong></td><td>${user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</td></tr>
                                        </table>
                                    </div>
                                    <div class="col-md-6">
                                        <h6>Print Statistics</h6>
                                        <table class="table table-sm">
                                            <tr><td><strong>Total Jobs:</strong></td><td>${stats.total_jobs}</td></tr>
                                            <tr><td><strong>Total Pages:</strong></td><td>${stats.total_pages}</td></tr>
                                            <tr><td><strong>Color Pages:</strong></td><td>${stats.color_pages}</td></tr>
                                            <tr><td><strong>B&W Pages:</strong></td><td>${stats.bw_pages}</td></tr>
                                        </table>
                                    </div>
                                </div>
                                
                                <h6 class="mt-4">Recent Print Jobs</h6>
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Document</th>
                                                <th>Printer</th>
                                                <th>Pages</th>
                                                <th>Date</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${printJobs.map(job => `
                                                <tr>
                                                    <td>${job.document_name}</td>
                                                    <td>${job.printer_name}</td>
                                                    <td>${job.total_pages}</td>
                                                    <td>${new Date(job.print_time).toLocaleString()}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Remove existing modal and add new one
            const existing = document.getElementById('viewUserModal');
            if (existing) existing.remove();
            document.body.insertAdjacentHTML('beforeend', modalHtml);

            const modal = new bootstrap.Modal(document.getElementById('viewUserModal'));
            modal.show();

        } catch (error) {
            console.error('Error viewing user:', error);
            this.showAlert('Error loading user details', 'danger');
        }
    }

    async editUser(userId) {
        // Implementation similar to viewUser but with editable form
        this.showAlert('Edit user functionality coming soon', 'info');
    }

    async resetPassword(userId) {
        const newPassword = prompt('Enter new password (minimum 8 characters):');
        if (!newPassword || newPassword.length < 8) {
            this.showAlert('Password must be at least 8 characters', 'warning');
            return;
        }

        try {
            await this.fetchWithAuth(`/users/${userId}/reset-password`, {
                method: 'POST',
                body: JSON.stringify({ new_password: newPassword })
            });

            this.showAlert('Password reset successfully', 'success');
        } catch (error) {
            console.error('Error resetting password:', error);
            this.showAlert('Error resetting password', 'danger');
        }
    }

    async deleteUser(userId) {
        if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
            return;
        }

        try {
            await this.fetchWithAuth(`/users/${userId}`, {
                method: 'DELETE'
            });

            this.loadUsers();
            this.showAlert('User deleted successfully', 'success');
        } catch (error) {
            console.error('Error deleting user:', error);
            this.showAlert('Error deleting user', 'danger');
        }
    }

    async syncLDAPUsers() {
        try {
            const result = await this.fetchWithAuth('/users/ldap/sync', {
                method: 'POST'
            });

            this.showAlert(`LDAP sync completed: ${result.users_synced} users synced`, 'success');
            this.loadUsers();
        } catch (error) {
            console.error('Error syncing LDAP users:', error);
            this.showAlert('LDAP sync not configured', 'warning');
        }
    }

    showAlert(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        // Add alert to top of main content
        const mainContent = document.querySelector('.container-fluid');
        if (mainContent) {
            mainContent.insertAdjacentHTML('afterbegin', alertHtml);

            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                const alert = mainContent.querySelector('.alert');
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        }
    }
}

// Global functions for inline event handlers
function refreshDashboard() {
    if (window.dashboard) {
        window.dashboard.refreshDashboard();
    }
}

function logout() {
    // Implement logout functionality
    console.log('Logout clicked');
    alert('Logout functionality will be implemented');
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PrintTrackingDashboard();
});
