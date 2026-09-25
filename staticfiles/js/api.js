const API_BASE_URL = '/api';
const AUTH_URL = '/auth/jwt/create/';

const api = {
    getTokens: function() {
        return {
            access: localStorage.getItem('access_token'),
            refresh: localStorage.getItem('refresh_token')
        };
    },
    
    setTokens: function(access, refresh) {
        localStorage.setItem('access_token', access);
        if (refresh) localStorage.setItem('refresh_token', refresh);
        
        // Synchronize with cookies for server-side TemplateView authentication
        document.cookie = `access=${access}; path=/; max-age=2592000; SameSite=Lax`;
        if (refresh) {
            document.cookie = `refresh=${refresh}; path=/; max-age=2592000; SameSite=Lax`;
        }
    },
    
    clearTokens: function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Clear cookies
        document.cookie = 'access=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        document.cookie = 'refresh=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    },

    getHeaders: function(isFormData = false) {
        const tokens = this.getTokens();
        const headers = {};
        if (tokens.access) {
            headers['Authorization'] = `Bearer ${tokens.access}`;
        }
        if (!isFormData) {
            headers['Content-Type'] = 'application/json';
        }
        return headers;
    },

    _isRefreshing: false,
    _refreshSubscribers: [],

    subscribeTokenRefresh: function(cb) {
        this._refreshSubscribers.push(cb);
    },

    onRefreshed: function(token) {
        this._refreshSubscribers.forEach(cb => cb(token));
        this._refreshSubscribers = [];
    },

    handleResponse: async function(response, originalRequestConfig) {
        if (response.status === 401) {
            const tokens = this.getTokens();
            if (!tokens.refresh) {
                this.clearTokens();
                window.location.href = '/login/';
                throw new Error('Unauthorized');
            }

            if (!this._isRefreshing) {
                this._isRefreshing = true;
                try {
                    const res = await fetch('/auth/jwt/refresh/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ refresh: tokens.refresh })
                    });
                    if (res.ok) {
                        const data = await res.json();
                        // Djoser might rotate refresh tokens depending on SIMPLE_JWT config
                        this.setTokens(data.access, data.refresh || tokens.refresh);
                        this._isRefreshing = false;
                        this.onRefreshed(data.access);
                    } else {
                        // Refresh token is invalid/expired
                        this.clearTokens();
                        window.location.href = '/login/';
                        throw new Error('Session expired');
                    }
                } catch(e) {
                    this._isRefreshing = false;
                    this.clearTokens();
                    window.location.href = '/login/';
                    throw new Error('Session expired');
                }
            }

            // Wait for the refresh to finish and retry original request
            return new Promise((resolve, reject) => {
                this.subscribeTokenRefresh(async (newToken) => {
                    originalRequestConfig.headers['Authorization'] = `Bearer ${newToken}`;
                    try {
                        const retryResponse = await fetch(originalRequestConfig.url, originalRequestConfig);
                        resolve(await this.parseResponse(retryResponse));
                    } catch(err) {
                        reject(err);
                    }
                });
            });
        }
        
        return this.parseResponse(response);
    },

    parseResponse: async function(response) {
        let data;
        try {
            data = await response.json();
        } catch(e) {
            if(!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            return null; // Empty response (e.g. 204 No Content)
        }
        
        if (!response.ok) {
            throw data; // Throw the parsed JSON error body
        }
        return data;
    },

    get: async function(endpoint, params = {}) {
        const url = new URL(API_BASE_URL + endpoint, window.location.origin);
        Object.keys(params).forEach(key => {
            if(params[key] !== null && params[key] !== '') {
                url.searchParams.append(key, params[key]);
            }
        });
        
        const config = { method: 'GET', headers: this.getHeaders(), url: url.toString() };
        const response = await fetch(config.url, config);
        return this.handleResponse(response, config);
    },

    post: async function(endpoint, body = {}, isFormData = false) {
        const url = API_BASE_URL + endpoint;
        const config = {
            method: 'POST',
            headers: this.getHeaders(isFormData),
            body: isFormData ? body : JSON.stringify(body),
            url: url
        };
        const response = await fetch(config.url, config);
        return this.handleResponse(response, config);
    },

    put: async function(endpoint, body = {}, isFormData = false) {
        const url = API_BASE_URL + endpoint;
        const config = {
            method: 'PUT',
            headers: this.getHeaders(isFormData),
            body: isFormData ? body : JSON.stringify(body),
            url: url
        };
        const response = await fetch(config.url, config);
        return this.handleResponse(response, config);
    },

    patch: async function(endpoint, body = {}, isFormData = false) {
        const url = API_BASE_URL + endpoint;
        const config = {
            method: 'PATCH',
            headers: this.getHeaders(isFormData),
            body: isFormData ? body : JSON.stringify(body),
            url: url
        };
        const response = await fetch(config.url, config);
        return this.handleResponse(response, config);
    },

    delete: async function(endpoint) {
        const url = API_BASE_URL + endpoint;
        const config = {
            method: 'DELETE',
            headers: this.getHeaders(),
            url: url
        };
        const response = await fetch(config.url, config);
        return this.handleResponse(response, config);
    },

    // Global logout hitting custom BlockJWT endpoint
    logout: async function() {
        const tokens = this.getTokens();
        if(tokens.access && tokens.refresh) {
            try {
                // Post to your custom logout view to block JWTs
                await fetch('/auth/jwt/logout/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ access: tokens.access, refresh: tokens.refresh })
                });
            } catch(e) {
                console.error("Logout API failed, continuing with local clear.");
            }
        }
        this.clearTokens();
        window.location.href = '/login/';
    }
};

// Global Notifications Utility
const notify = {
    show: function(message, type = 'success') {
        const toastContainer = document.getElementById('toastContainer');
        if(!toastContainer) return alert(message);
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type} border-0 mb-2`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    },
    success: function(msg) { this.show(msg, 'success'); },
    error: function(msg) { this.show(msg, 'danger'); },
    warning: function(msg) { this.show(msg, 'warning'); },
    info: function(msg) { this.show(msg, 'info'); }
};

// Extract Form validation errors and display them
function extractErrorMessage(err) {
    if(typeof err === 'string') return err;
    if(err.detail) return err.detail;
    if(err.non_field_errors) return err.non_field_errors.join(' ');
    
    // Check if it's an object with field errors
    const firstKey = Object.keys(err)[0];
    if(firstKey && Array.isArray(err[firstKey])) {
        return `${firstKey}: ${err[firstKey].join(' ')}`;
    }
    
    return 'An unknown error occurred.';
}

function getStatusBadgeClass(status) {
    const mapping = {
        'pending': 'warning text-dark',
        'confirmed': 'info text-dark',
        'processing': 'primary',
        'dispatched': 'secondary',
        'delivered': 'success',
        'cancelled': 'danger',
        'returned': 'dark',
        'return_requested': 'warning text-dark',
        'partially_returned': 'dark'
    };
    return mapping[status.toLowerCase()] || 'secondary';
}
