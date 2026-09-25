// Orders API and DOM logic
let currentOrderPage = 1;

async function loadOrders() {
    const tbody = document.getElementById('ordersTableBody');
    const search = document.getElementById('searchOrder')?.value || '';
    const status = document.getElementById('filterStatus')?.value || '';
    
    try {
        const data = await api.get('/orders/', {
            page: currentOrderPage,
            search: search,
            status: status
        });
        
        const results = data.results || data;
        tbody.innerHTML = '';
        
        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No orders found.</td></tr>';
            if (document.getElementById('pageInfo')) document.getElementById('pageInfo').textContent = 'Showing 0 results';
            return;
        }

        results.forEach(order => {
            tbody.innerHTML += `
                <tr class="cursor-pointer" onclick="window.location.href='/orders/${order.id}/'">
                    <td><strong>#${order.order_number}</strong></td>
                    <td>${order.customer_name}</td>
                    <td>$${order.total}</td>
                    <td><span class="badge bg-${getStatusBadgeClass(order.status)}">${order.status}</span></td>
                    <td>${order.payment_status}</td>
                    <td>${new Date(order.created_at).toLocaleDateString()}</td>
                </tr>
            `;
        });
        
        if (data.count !== undefined) {
            document.getElementById('pageInfo').textContent = `Total: ${data.count}`;
            document.getElementById('prevPage').disabled = !data.previous;
            document.getElementById('nextPage').disabled = !data.next;
            
            document.getElementById('prevPage').onclick = () => { if(data.previous) { currentOrderPage--; loadOrders(); } };
            document.getElementById('nextPage').onclick = () => { if(data.next) { currentOrderPage++; loadOrders(); } };
        }
    } catch(err) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Failed to load orders.</td></tr>';
        notify.error('Failed to load orders');
    }
}

async function loadOrderDetail() {
    const match = window.location.pathname.match(/\/orders\/(\d+)\//);
    if (!match) return;
    const orderId = match[1];

    try {
        const order = await api.get(`/orders/${orderId}/`);
        
        const editBtn = document.getElementById('editOrderBtn');
        if (editBtn) editBtn.href = `/orders/${orderId}/edit/`;
        
        // Populate header & info
        document.getElementById('orderNumberTitle').textContent = order.order_number;
        document.getElementById('customerName').textContent = order.customer_name;
        document.getElementById('customerEmail').textContent = order.customer_email || 'N/A';
        document.getElementById('customerPhone').textContent = order.customer_phone;
        document.getElementById('shippingAddress').textContent = order.shipping_address;
        
        document.getElementById('orderStatusBadge').innerHTML = `<span class="badge bg-${getStatusBadgeClass(order.status)}">${order.status.toUpperCase()}</span>`;
        document.getElementById('paymentStatus').innerHTML = `<span class="badge bg-${order.payment_status === 'paid' ? 'success' : 'secondary'}">${order.payment_status.toUpperCase()}</span>`;
        document.getElementById('orderDate').textContent = new Date(order.created_at).toLocaleString();
        
        const tbody = document.getElementById('orderItemsBody');
        tbody.innerHTML = '';
        
        if (!order.items || order.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No items found.</td></tr>';
        } else {
            order.items.forEach(item => {
                let title = item.product_detail ? item.product_detail.title : item.product_title_snapshot;
                let sku = item.product_detail ? item.product_detail.sku : item.sku_snapshot;
                let image = item.product_detail && (item.product_detail.image || item.product_detail.image_url) 
                    ? (item.product_detail.image || item.product_detail.image_url) 
                    : '/static/images/placeholder.png';
                let productLink = item.product ? `<a href="/products/${item.product}/" class="text-decoration-none fw-bold">${title}</a>` : `<span class="fw-bold">${title}</span>`;
                if(!item.product) productLink += ' <span class="badge bg-danger ms-2">Unavailable</span>';
    
                tbody.innerHTML += `
                    <tr>
                        <td><img src="${image}" class="img-thumbnail" style="width:50px;height:50px;object-fit:cover;"></td>
                        <td>${productLink}</td>
                        <td>${sku}</td>
                        <td class="text-end">$${item.unit_price}</td>
                        <td class="text-center">${item.quantity}</td>
                        <td class="text-end fw-bold">$${item.subtotal}</td>
                    </tr>
                `;
            });
        }
        
        document.getElementById('orderSubtotal').textContent = `$${order.subtotal}`;
        document.getElementById('orderDiscount').textContent = `$${order.discount}`;
        document.getElementById('orderShipping').textContent = `$${order.shipping_cost}`;
        document.getElementById('orderTax').textContent = `$${order.tax}`;
        document.getElementById('orderTotal').innerHTML = `<strong>$${order.total}</strong>`;

        // Render Action Buttons based on status
        renderStatusActions(order);

        // Load timeline
        loadTimeline(orderId);
        
        // Setup Return form if eligible
        setupReturnForm(order);

    } catch (err) {
        notify.error('Failed to load order details');
    }
}

function renderStatusActions(order) {
    const container = document.getElementById('statusActions');
    
    // Valid backend transitions to enforce frontend logic
    const validTransitions = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['processing', 'cancelled'],
        'processing': ['dispatched', 'cancelled'],
        'dispatched': ['delivered', 'return_requested', 'returned'],
        'delivered': ['return_requested', 'returned'],
        'return_requested': ['returned', 'partially_returned', 'delivered'],
        'partially_returned': ['returned'],
        'returned': [],
        'cancelled': []
    };

    const currentStatus = order.status;
    const allowedNext = validTransitions[currentStatus] || [];
    
    const existingDropdown = document.getElementById('statusDropdownContainer');
    if (existingDropdown) existingDropdown.remove();

    if (allowedNext.length > 0) {
        const statuses = {
            'pending': 'Pending',
            'confirmed': 'Confirmed',
            'processing': 'Processing',
            'dispatched': 'Dispatched',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled',
            'return_requested': 'Return Requested',
            'returned': 'Returned',
            'partially_returned': 'Partially Returned'
        };

        let options = `<option value="" disabled selected>Change Status...</option>`;
        allowedNext.forEach(val => {
            options += `<option value="${val}">${statuses[val] || val}</option>`;
        });

        const dropdownHTML = `
            <div class="input-group input-group-sm ms-2" id="statusDropdownContainer">
                <select class="form-select border-primary" id="orderStatusDropdown">
                    ${options}
                </select>
                <button class="btn btn-primary" onclick="updateOrderStatusFromDropdown(${order.id})" id="updateStatusBtn">Update</button>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', dropdownHTML);
    }
}

async function updateOrderStatusFromDropdown(orderId) {
    const dropdown = document.getElementById('orderStatusDropdown');
    const newStatus = dropdown.value;
    const btn = document.getElementById('updateStatusBtn');

    if(!newStatus) return;
    if(!confirm(`Change status to ${newStatus}?`)) return;

    btn.disabled = true;
    btn.textContent = 'Updating...';

    try {
        if (newStatus === 'dispatched') {
            await api.post(`/orders/${orderId}/dispatch_order/`);
            notify.success('Order dispatched! Stock deducted.');
        } else {
            await api.post(`/orders/${orderId}/change_status/`, { status: newStatus });
            notify.success('Status updated successfully');
        }
        loadOrderDetail(); // Refresh
    } catch(err) {
        notify.error(extractErrorMessage(err));
        btn.disabled = false;
        btn.textContent = 'Update';
    }
}

async function loadTimeline(orderId) {
    try {
        const order = await api.get(`/orders/${orderId}/`);
        const tl = document.getElementById('orderTimeline');
        
        let logsHTML = '<ul class="list-unstyled mb-0 border-start border-2 ms-2 ps-3">';
        if(order.status_logs && order.status_logs.length > 0) {
            order.status_logs.forEach((log, index) => {
                const isLatest = index === 0;
                logsHTML += `
                    <li class="mb-3 position-relative">
                        <span class="position-absolute translate-middle p-1 rounded-circle bg-${isLatest ? 'primary' : 'secondary'}" style="left: -17px; top: 5px;"></span>
                        <div class="fw-bold">${log.old_status ? `${log.old_status} &rarr; ${log.new_status}` : 'Order Created'}</div>
                        <div class="text-muted small">${new Date(log.created_at).toLocaleString()}</div>
                    </li>
                `;
            });
            logsHTML += '</ul>';
            tl.innerHTML = logsHTML;
        } else {
            tl.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-clock-history fs-3 text-muted"></i>
                    <p class="text-muted mt-2 mb-0">No history available</p>
                </div>
            `;
        }
    } catch(e) {
        console.error(e);
    }
}

function setupReturnForm(order) {
    const card = document.getElementById('returnsCard');
    const returnItemsDiv = document.getElementById('returnItems');
    
    // Only show returns for dispatched, delivered, or partially_returned
    const returnableStatuses = ['dispatched', 'delivered', 'partially_returned'];
    if (!card || !returnableStatuses.includes(order.status)) {
        if(card) card.classList.add('d-none');
        return;
    }
    
    card.classList.remove('d-none');
    returnItemsDiv.innerHTML = '';
    
    order.items.forEach(item => {
        returnItemsDiv.innerHTML += `
            <div class="mb-2">
                <label class="form-label mb-0" style="font-size: 0.85rem">${item.product_title_snapshot} (Max: ${item.quantity - item.returned_quantity})</label>
                <input type="number" class="form-control form-control-sm return-qty-input" 
                    data-item-id="${item.id}" min="0" max="${item.quantity - item.returned_quantity}" value="0">
            </div>
        `;
    });
    
    document.getElementById('returnForm').onsubmit = async (e) => {
        e.preventDefault();
        const inputs = document.querySelectorAll('.return-qty-input');
        const itemsToReturn = [];
        
        inputs.forEach(input => {
            const qty = parseInt(input.value);
            if (qty > 0) {
                itemsToReturn.push({
                    order_item_id: input.getAttribute('data-item-id'),
                    quantity: qty
                });
            }
        });
        
        if (itemsToReturn.length === 0) {
            return notify.warning('Please enter a quantity to return.');
        }
        
        const btn = document.getElementById('processReturnBtn');
        btn.disabled = true;
        btn.textContent = 'Processing...';
        
        try {
            await api.post(`/orders/${order.id}/return_order/`, { items: itemsToReturn });
            notify.success('Return processed and stock added back.');
            inputs.forEach(i => i.value = 0);
            loadOrderDetail(); // Refresh
        } catch(err) {
            notify.error(extractErrorMessage(err));
        } finally {
            btn.disabled = false;
            btn.textContent = 'Process Return';
        }
    };
}

// -------------------------------------------------------------
// CREATE AND EDIT ORDER LOGIC
// -------------------------------------------------------------

let orderItems = [];

// Financial Inputs
function setupFinancialListeners() {
    const inputs = document.querySelectorAll('.calc-input');
    inputs.forEach(input => {
        input.addEventListener('input', calculateTotals);
    });
}

function calculateTotals() {
    let subtotal = 0;
    orderItems.forEach(item => {
        subtotal += (item.price * item.qty);
    });
    
    const discount = parseFloat(document.getElementById('inputDiscount')?.value || 0) || 0;
    const shipping = parseFloat(document.getElementById('inputShipping')?.value || 0) || 0;
    const tax = parseFloat(document.getElementById('inputTax')?.value || 0) || 0;
    
    const grandTotal = subtotal + shipping + tax - discount;
    
    const subtotalEl = document.getElementById('calcSubtotal');
    const grandTotalEl = document.getElementById('calcGrandTotal');
    const btn = document.getElementById('submitOrderBtn');
    
    if(subtotalEl) subtotalEl.textContent = '$' + subtotal.toFixed(2);
    if(grandTotalEl) grandTotalEl.textContent = '$' + grandTotal.toFixed(2);
    
    if (grandTotal < 0) {
        if(grandTotalEl) grandTotalEl.classList.add('text-danger');
        if(btn) btn.disabled = true;
    } else {
        if(grandTotalEl) grandTotalEl.classList.remove('text-danger');
        if(btn) btn.disabled = (orderItems.length === 0);
    }
}

async function initOrderCreate() {
    setupFinancialListeners();
    setupProductSearch();
    
    document.getElementById('orderForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (orderItems.length === 0) {
            return notify.warning('Please add at least one product to the order.');
        }
        
        const btn = document.getElementById('submitOrderBtn');
        btn.disabled = true;
        btn.textContent = 'Processing...';
        
        const payload = {
            customer_name: document.getElementById('customer_name').value,
            customer_phone: document.getElementById('customer_phone').value,
            customer_email: document.getElementById('customer_email').value || '',
            shipping_address: document.getElementById('shipping_address').value,
            billing_address: document.getElementById('billing_address').value || '',
            payment_method: document.getElementById('payment_method').value,
            notes: document.getElementById('notes').value || '',
            discount: parseFloat(document.getElementById('inputDiscount').value || 0),
            shipping_cost: parseFloat(document.getElementById('inputShipping').value || 0),
            tax: parseFloat(document.getElementById('inputTax').value || 0),
            items: orderItems.map(item => ({
                product_id: item.id,
                quantity: item.qty
            }))
        };
        
        try {
            await api.post('/orders/', payload);
            notify.success('Order created successfully!');
            setTimeout(() => { window.location.href = '/orders/'; }, 1000);
        } catch(err) {
            notify.error(extractErrorMessage(err));
            btn.disabled = false;
            btn.textContent = 'Place Order';
        }
    });
}

function setupProductSearch() {
    const searchBtn = document.getElementById('productSearchBtn');
    const searchInput = document.getElementById('productSearchInput');
    const searchResults = document.getElementById('productSearchResults');
    
    if(!searchBtn) return;
    
    searchBtn.addEventListener('click', async () => {
        const query = searchInput.value.trim();
        searchResults.innerHTML = '<tr><td colspan="6" class="text-center py-3">Searching...</td></tr>';
        try {
            const data = await api.get('/products/', { search: query, is_active: 'true' });
            const results = data.results || data;
            
            searchResults.innerHTML = '';
            if (results.length === 0) {
                searchResults.innerHTML = '<tr><td colspan="6" class="text-center py-3 text-muted">No products found.</td></tr>';
                return;
            }
            
            results.forEach(p => {
                const imgSrc = p.image || p.image_url || '/static/images/placeholder.png';
                let actionBtn = '';
                if (p.stock > 0) {
                    const pData = encodeURIComponent(JSON.stringify(p));
                    actionBtn = `<button class="btn btn-sm btn-outline-primary" onclick="addOrderItem('${pData}')">Select</button>`;
                } else {
                    actionBtn = '<span class="text-danger small">Out of stock</span>';
                }
                
                searchResults.innerHTML += `
                    <tr>
                        <td><img src="${imgSrc}" class="img-thumbnail" style="width:40px;height:40px;object-fit:cover;"></td>
                        <td>${p.sku}</td>
                        <td>${p.title}</td>
                        <td>$${p.main_price}</td>
                        <td>${p.stock}</td>
                        <td>${actionBtn}</td>
                    </tr>
                `;
            });
        } catch (err) {
            searchResults.innerHTML = '<tr><td colspan="6" class="text-center py-3 text-danger">Search failed.</td></tr>';
        }
    });
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchBtn.click();
    });
}

window.addOrderItem = function(pDataStr) {
    const p = JSON.parse(decodeURIComponent(pDataStr));
    
    const existing = orderItems.find(i => i.id === p.id);
    if (existing) {
        if (existing.qty < p.stock) {
            existing.qty++;
            renderOrderItems();
        } else {
            notify.warning(`Only ${p.stock} units available for ${p.title}.`);
        }
    } else {
        orderItems.push({
            id: p.id,
            sku: p.sku,
            title: p.title,
            price: parseFloat(p.main_price),
            stock: p.stock,
            qty: 1
        });
        renderOrderItems();
    }
    
    const modalEl = document.getElementById('productSearchModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
};

window.removeOrderItem = function(id) {
    orderItems = orderItems.filter(i => i.id !== id);
    renderOrderItems();
};

window.updateOrderItemQty = function(id, newQty) {
    const item = orderItems.find(i => i.id === id);
    if (!item) return;
    
    const qty = parseInt(newQty);
    if (isNaN(qty) || qty <= 0) {
        return notify.warning('Quantity must be at least 1.');
    }
    
    if (qty > item.stock) {
        notify.warning(`Only ${item.stock} units available for ${item.title}.`);
        renderOrderItems(); 
        return;
    }
    
    item.qty = qty;
    renderOrderItems();
};

function renderOrderItems(readOnly = false) {
    const tbody = document.getElementById('orderItemsBody');
    const submitBtn = document.getElementById('submitOrderBtn');
    
    if (orderItems.length === 0) {
        tbody.innerHTML = '<tr id="emptyItemsRow"><td colspan="6" class="text-center py-5 text-muted"><i class="bi bi-cart-x fs-1 d-block mb-2"></i>No products added yet.</td></tr>';
        if(submitBtn) submitBtn.disabled = true;
        calculateTotals();
        return;
    }
    
    tbody.innerHTML = '';
    
    orderItems.forEach(item => {
        const itemTotal = item.price * item.qty;
        
        let qtyCol = readOnly 
            ? `<td class="text-center">${item.qty}</td>` 
            : `<td>
                 <input type="number" class="form-control form-control-sm text-center mx-auto" 
                    value="${item.qty}" min="1" max="${item.stock > 0 ? item.stock : 9999}" style="width: 80px;"
                    onchange="updateOrderItemQty(${item.id}, this.value)">
               </td>`;
               
        let actionCol = readOnly 
            ? `<td class="text-end text-muted small"><i class="bi bi-lock-fill"></i> Locked</td>`
            : `<td class="text-end">
                 <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeOrderItem(${item.id})">
                     <i class="bi bi-trash"></i>
                 </button>
               </td>`;
        
        tbody.innerHTML += `
            <tr>
                <td><strong>${item.title}</strong></td>
                <td>${item.sku}</td>
                <td class="text-end">$${item.price.toFixed(2)}</td>
                ${qtyCol}
                <td class="text-end fw-bold">$${itemTotal.toFixed(2)}</td>
                ${actionCol}
            </tr>
        `;
    });
    
    if(submitBtn) submitBtn.disabled = false;
    calculateTotals();
}

async function initOrderEdit() {
    setupFinancialListeners();
    setupProductSearch();
    
    const form = document.getElementById('orderForm');
    const saveBtn = document.getElementById('submitOrderBtn');
    const addProductBtn = document.getElementById('addProductBtn');
    
    const match = window.location.pathname.match(/\/orders\/(\d+)\/edit\//);
    let editId = null;
    let orderIsDispatched = false;
    
    if (match) {
        editId = match[1];
        
        // Setup Cancel Button Link
        document.getElementById('cancelEditBtn').href = `/orders/${editId}/`;
        
        try {
            const data = await api.get(`/orders/${editId}/`);
            document.getElementById('orderNumberTitle').textContent = `#${data.order_number}`;
            
            document.getElementById('customer_name').value = data.customer_name;
            document.getElementById('customer_phone').value = data.customer_phone;
            document.getElementById('customer_email').value = data.customer_email || '';
            document.getElementById('shipping_address').value = data.shipping_address;
            document.getElementById('billing_address').value = data.billing_address || '';
            document.getElementById('payment_method').value = data.payment_method;
            
            if(document.getElementById('payment_status')) {
                document.getElementById('payment_status').value = data.payment_status;
            }
            
            document.getElementById('notes').value = data.notes || '';
            document.getElementById('inputDiscount').value = data.discount;
            document.getElementById('inputShipping').value = data.shipping_cost;
            document.getElementById('inputTax').value = data.tax;
            
            // Check if order is dispatched or beyond (items cannot be edited)
            const lockedStatuses = ['dispatched', 'delivered', 'returned', 'partially_returned', 'cancelled'];
            orderIsDispatched = lockedStatuses.includes(data.status);
            
            if (orderIsDispatched) {
                if (addProductBtn) addProductBtn.style.display = 'none';
                const warning = document.getElementById('itemEditWarning');
                if (warning) warning.classList.remove('d-none');
            }
            
            orderItems = (data.items || []).map(item => ({
                id: item.product,
                sku: item.sku_snapshot,
                title: item.product_title_snapshot,
                price: parseFloat(item.unit_price),
                stock: 9999, // Allow editing qty if not dispatched
                qty: item.quantity
            }));
            
            renderOrderItems(orderIsDispatched); // Pass true to render read-only items
            
        } catch(err) {
            notify.error('Failed to load order details.');
            if(saveBtn) saveBtn.disabled = true;
        }
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!orderIsDispatched && orderItems.length === 0) {
            return notify.warning('Order must have at least one product.');
        }
        
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
        
        const payload = {
            customer_name: document.getElementById('customer_name').value,
            customer_phone: document.getElementById('customer_phone').value,
            customer_email: document.getElementById('customer_email').value || '',
            shipping_address: document.getElementById('shipping_address').value,
            billing_address: document.getElementById('billing_address').value || '',
            payment_method: document.getElementById('payment_method').value,
            notes: document.getElementById('notes').value || '',
            discount: parseFloat(document.getElementById('inputDiscount').value || 0),
            shipping_cost: parseFloat(document.getElementById('inputShipping').value || 0),
            tax: parseFloat(document.getElementById('inputTax').value || 0)
        };
        
        if (document.getElementById('payment_status')) {
            payload.payment_status = document.getElementById('payment_status').value;
        }
        
        if (!orderIsDispatched) {
            payload.items = orderItems.map(item => ({
                product_id: item.id,
                quantity: item.qty,
                unit_price: item.price
            }));
        }
        
        try {
            await api.patch(`/orders/${editId}/`, payload);
            notify.success('Order updated successfully');
            setTimeout(() => { window.location.href = `/orders/${editId}/`; }, 1000);
        } catch(err) {
            notify.error(extractErrorMessage(err));
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Changes';
        }
    });
}
