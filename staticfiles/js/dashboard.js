let salesChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();

    const dateFilterForm = document.getElementById('dateFilterForm');
    const resetBtn = document.getElementById('resetBtn');

    dateFilterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const start = document.getElementById('startDate').value;
        const end = document.getElementById('endDate').value;
        loadDashboard({ start_date: start, end_date: end });
    });

    resetBtn.addEventListener('click', () => {
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        loadDashboard();
    });
});

async function loadDashboard(params = {}) {
    const loading = document.getElementById('loading');
    const content = document.getElementById('dashboardContent');
    
    loading.classList.remove('d-none');
    content.classList.add('d-none');

    try {
        const data = await api.get('/dashboard/', params);
        
        // Populate KPI Cards
        const statCards = document.getElementById('statCards');
        statCards.innerHTML = `
            <div class="col">
                <div class="card shadow-sm h-100 border-0 border-start border-primary border-4">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Total Sales</h6>
                        <h3 class="card-title fw-bold">$${data.sales.total_sales || '0.00'}</h3>
                    </div>
                </div>
            </div>
            <div class="col">
                <div class="card shadow-sm h-100 border-0 border-start border-info border-4">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Total Orders</h6>
                        <h3 class="card-title fw-bold">${data.overview.total_orders || 0}</h3>
                    </div>
                </div>
            </div>
            <div class="col">
                <div class="card shadow-sm h-100 border-0 border-start border-warning border-4">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Pending Orders</h6>
                        <h3 class="card-title fw-bold">${data.overview.order_statuses ? (data.overview.order_statuses.pending || 0) : 0}</h3>
                    </div>
                </div>
            </div>
            <div class="col">
                <div class="card shadow-sm h-100 border-0 border-start border-success border-4">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Delivered Orders</h6>
                        <h3 class="card-title fw-bold">${data.overview.order_statuses ? (data.overview.order_statuses.delivered || 0) : 0}</h3>
                    </div>
                </div>
            </div>
        `;

        // Render Sales Chart
        renderSalesChart(data.sales_chart || []);

        // Order Status Distribution
        renderStatusDistribution(data.overview.order_statuses || {}, data.overview.total_orders || 0);

        // Populate Recent Orders
        const tbody = document.getElementById('recentOrdersBody');
        tbody.innerHTML = '';
        if(data.recent_orders && data.recent_orders.length > 0) {
            data.recent_orders.forEach(order => {
                tbody.innerHTML += `
                    <tr>
                        <td><a href="/orders/${order.id}/" class="text-decoration-none fw-bold">#${order.order_number}</a></td>
                        <td>${order.customer_name}</td>
                        <td><span class="badge bg-${getStatusBadgeClass(order.status)}">${order.status}</span></td>
                        <td>$${order.total}</td>
                        <td>${new Date(order.created_at).toLocaleDateString()}</td>
                    </tr>
                `;
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">No recent orders</td></tr>';
        }

        // Populate Top Products
        const topList = document.getElementById('topProductsList');
        topList.innerHTML = '';
        if (data.top_products && data.top_products.length > 0) {
            data.top_products.forEach(p => {
                topList.innerHTML += `
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-3">
                        <div>
                            <h6 class="mb-0 fw-bold"><a href="/products/${p.product__id}/" class="text-decoration-none text-dark">${p.product_title_snapshot}</a></h6>
                            <small class="text-muted">SKU: ${p.sku_snapshot}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-primary rounded-pill mb-1">${p.units_sold} sold</span><br>
                            <small class="fw-bold text-success">$${p.revenue}</small>
                        </div>
                    </li>
                `;
            });
        } else {
            topList.innerHTML = '<li class="list-group-item text-center text-muted py-4">Not enough data.</li>';
        }

        // Populate Low Stock
        const lowStockList = document.getElementById('lowStockList');
        lowStockList.innerHTML = '';
        if (data.low_stock_products && data.low_stock_products.length > 0) {
            data.low_stock_products.forEach(p => {
                lowStockList.innerHTML += `
                    <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-2">
                        <div class="d-flex align-items-center gap-2">
                            <img src="${p.image || p.image_url || '/static/images/placeholder.png'}" class="rounded" style="width: 40px; height: 40px; object-fit: cover;">
                            <div>
                                <h6 class="mb-0 small"><a href="/products/${p.id}/" class="text-decoration-none text-dark">${p.title}</a></h6>
                                <small class="text-muted">${p.sku}</small>
                            </div>
                        </div>
                        <span class="badge bg-danger rounded-pill">${p.stock} left</span>
                    </li>
                `;
            });
        } else {
            lowStockList.innerHTML = '<li class="list-group-item text-center text-muted py-4">All stock levels look good!</li>';
        }

        loading.classList.add('d-none');
        content.classList.remove('d-none');

    } catch(err) {
        notify.error('Failed to load dashboard data');
        loading.innerHTML = '<div class="alert alert-danger mx-5">Failed to load dashboard. Please try again.</div>';
    }
}

function renderSalesChart(chartData) {
    const ctx = document.getElementById('salesChart').getContext('2d');
    
    if (salesChartInstance) {
        salesChartInstance.destroy();
    }

    const labels = chartData.map(d => d.date);
    const values = chartData.map(d => parseFloat(d.sales));

    salesChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Sales ($)',
                data: values,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: function(value) { return '$' + value; } }
                }
            }
        }
    });
}

function renderStatusDistribution(statuses, total) {
    const container = document.getElementById('statusDistribution');
    container.innerHTML = '';
    
    if (total === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">No active orders</p>';
        return;
    }

    const relevantStatuses = ['pending', 'processing', 'dispatched', 'delivered', 'returned', 'cancelled'];
    
    relevantStatuses.forEach(s => {
        const count = statuses[s] || 0;
        if (count > 0) {
            const percentage = ((count / total) * 100).toFixed(1);
            const badgeClass = getStatusBadgeClass(s).split(' ')[0]; // Extract just the color part e.g., 'primary'
            
            container.innerHTML += `
                <div class="mb-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span class="small fw-bold text-capitalize">${s}</span>
                        <span class="small text-muted">${count} (${percentage}%)</span>
                    </div>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar bg-${badgeClass}" role="progressbar" style="width: ${percentage}%" aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
            `;
        }
    });
}
