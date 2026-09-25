// Products API and DOM logic
let currentPage = 1;

async function loadProducts() {
    const tbody = document.getElementById('productsTableBody');
    const search = document.getElementById('searchTitle')?.value || '';
    const status = document.getElementById('filterStatus')?.value || '';
    
    try {
        const data = await api.get('/products/', {
            page: currentPage,
            search: search,
            is_active: status
        });
        
        const results = data.results || data;
        tbody.innerHTML = '';
        
        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No products found.</td></tr>';
            document.getElementById('pageInfo').textContent = 'Showing 0 results';
            return;
        }

        results.forEach(item => {
            const statusBadge = item.is_active 
                ? '<span class="badge bg-success">Active</span>' 
                : '<span class="badge bg-secondary">Inactive</span>';
                
            let stockClass = 'stock-available';
            if (item.stock === 0) stockClass = 'stock-out';
            else if (item.stock <= 5) stockClass = 'stock-low';
            
            const imgSrc = item.image || item.image_url || '/static/images/placeholder.png';
            
            tbody.innerHTML += `
                <tr>
                    <td><img src="${imgSrc}" alt="${item.title}" class="img-thumbnail" style="width:40px; height:40px; object-fit:cover;"></td>
                    <td>${item.sku}</td>
                    <td><strong>${item.title}</strong></td>
                    <td>$${item.main_price}</td>
                    <td class="${stockClass}">${item.stock}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <div class="btn-group">
                            <a href="/products/${item.id}/" class="btn btn-sm btn-outline-secondary">View</a>
                            <a href="/products/${item.id}/edit/" class="btn btn-sm btn-outline-primary">Edit</a>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        // Handle pagination controls if backend provides count
        if (data.count !== undefined) {
            document.getElementById('pageInfo').textContent = `Total: ${data.count}`;
            document.getElementById('prevPage').disabled = !data.previous;
            document.getElementById('nextPage').disabled = !data.next;
            
            document.getElementById('prevPage').onclick = () => { if(data.previous) { currentPage--; loadProducts(); } };
            document.getElementById('nextPage').onclick = () => { if(data.next) { currentPage++; loadProducts(); } };
        }
        
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Failed to load products.</td></tr>';
        notify.error('Failed to load products');
    }
}

async function loadSelectOptions() {
    try {
        const collections = await api.get('/collections/');
        const types = await api.get('/product-types/');
        
        const cSelect = document.getElementById('collection');
        const tSelect = document.getElementById('product_type');
        
        cSelect.innerHTML = '<option value="">Select Collection</option>';
        (collections.results || collections).forEach(c => {
            cSelect.innerHTML += `<option value="${c.id}">${c.title}</option>`;
        });
        
        tSelect.innerHTML = '<option value="">Select Product Type</option>';
        (types.results || types).forEach(t => {
            tSelect.innerHTML += `<option value="${t.id}">${t.title}</option>`;
        });
    } catch(err) {
        notify.error('Failed to load options for collections/types.');
    }
}

async function initProductForm() {
    await loadSelectOptions();
    
    const form = document.getElementById('productForm');
    const saveBtn = document.getElementById('saveBtn');
    
    const imageInput = document.getElementById('image');
    const imageUrlInput = document.getElementById('image_url');
    const imagePreview = document.getElementById('imagePreview');
    const overlay = document.getElementById('formLoadingOverlay');

    // Image preview logic
    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        } else if (imageUrlInput.value) {
            imagePreview.src = imageUrlInput.value;
        } else {
            imagePreview.src = '/static/images/placeholder.png';
        }
    });

    imageUrlInput.addEventListener('input', (e) => {
        if (!imageInput.files[0]) {
            imagePreview.src = e.target.value || '/static/images/placeholder.png';
        }
    });

    const match = window.location.pathname.match(/\/products\/(\d+)\/edit\//);
    let editId = null;
    let originalData = null;

    if (match) {
        editId = match[1];
        document.getElementById('pageTitle').textContent = 'Edit Product';
        if (overlay) overlay.classList.remove('d-none');
        if (overlay) overlay.classList.add('d-flex');
        
        try {
            const data = await api.get(`/products/${editId}/`);
            originalData = data;
            
            document.getElementById('title').value = data.title;
            document.getElementById('sku').value = data.sku;
            document.getElementById('slug').value = data.slug;
            document.getElementById('collection').value = data.collection || '';
            document.getElementById('product_type').value = data.product_type || '';
            document.getElementById('short_description').value = data.short_description || '';
            document.getElementById('description').value = data.description || '';
            document.getElementById('main_price').value = data.main_price;
            document.getElementById('old_price').value = data.old_price || '';
            document.getElementById('stock').value = data.stock;
            document.getElementById('is_active').checked = data.is_active;
            document.getElementById('is_featured').checked = data.is_featured;
            
            if (data.image_url) {
                imageUrlInput.value = data.image_url;
            }
            if (data.image) {
                imagePreview.src = data.image;
            } else if (data.image_url) {
                imagePreview.src = data.image_url;
            }
        } catch(err) {
            notify.error('Failed to load product details.');
            saveBtn.disabled = true;
        } finally {
            if (overlay) overlay.classList.remove('d-flex');
            if (overlay) overlay.classList.add('d-none');
        }
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
        
        const hasFile = imageInput.files.length > 0;
        let payload;
        let isFormData = false;
        
        const currentData = {
            title: document.getElementById('title').value,
            sku: document.getElementById('sku').value,
            slug: document.getElementById('slug').value,
            collection: document.getElementById('collection').value || null,
            product_type: document.getElementById('product_type').value,
            short_description: document.getElementById('short_description').value,
            description: document.getElementById('description').value,
            main_price: document.getElementById('main_price').value,
            old_price: document.getElementById('old_price').value || null,
            stock: document.getElementById('stock').value,
            is_active: document.getElementById('is_active').checked,
            is_featured: document.getElementById('is_featured').checked,
            image_url: imageUrlInput.value || ''
        };
        
        if (hasFile || editId === null) {
            // Use FormData for creations or if a new file is explicitly uploaded
            isFormData = true;
            payload = new FormData();
            
            for (const key in currentData) {
                // If editing, only append changed fields
                if (editId) {
                    let origVal = originalData[key];
                    if (origVal === null) origVal = ''; // normalize null to empty string for comparison
                    let curVal = currentData[key];
                    if (curVal === null) curVal = '';
                    
                    if (String(origVal) !== String(curVal)) {
                        payload.append(key, currentData[key]);
                    }
                } else {
                    if (currentData[key] !== null) {
                        payload.append(key, currentData[key]);
                    }
                }
            }
            if (hasFile) {
                payload.append('image', imageInput.files[0]);
            }
        } else {
            // No file uploaded, use JSON
            payload = {};
            for (const key in currentData) {
                if (editId) {
                    let origVal = originalData[key];
                    if (origVal === null) origVal = ''; 
                    let curVal = currentData[key];
                    if (curVal === null) curVal = '';
                    
                    // Only send if changed
                    if (String(origVal) !== String(curVal)) {
                        payload[key] = currentData[key];
                    }
                } else {
                    payload[key] = currentData[key];
                }
            }
        }
        
        try {
            if (editId) {
                await api.patch(`/products/${editId}/`, payload, isFormData);
                notify.success('Product updated successfully');
            } else {
                await api.post('/products/', payload, isFormData);
                notify.success('Product created successfully');
            }
            setTimeout(() => { window.location.href = '/products/'; }, 1000);
        } catch(err) {
            notify.error(extractErrorMessage(err));
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Product';
        }
    });
}

async function loadProductDetail() {
    const match = window.location.pathname.match(/\/products\/(\d+)\//);
    if (!match || window.location.pathname.includes('/edit/')) return;
    
    const editId = match[1];
    document.getElementById('editProductBtn').href = `/products/${editId}/edit/`;
    
    try {
        const data = await api.get(`/products/${editId}/`);
        
        document.getElementById('detailTitle').textContent = data.title;
        document.getElementById('detailSku').textContent = data.sku;
        document.getElementById('detailSlug').textContent = data.slug;
        document.getElementById('detailShortDesc').textContent = data.short_description || 'N/A';
        document.getElementById('detailDesc').textContent = data.description || 'N/A';
        
        document.getElementById('detailStatusBadge').innerHTML = data.is_active 
            ? '<span class="badge bg-success">Active</span>' 
            : '<span class="badge bg-secondary">Inactive</span>';
            
        const imgSrc = data.image || data.image_url || '/static/images/placeholder.png';
        document.getElementById('detailImage').src = imgSrc;
        
        document.getElementById('detailMainPrice').textContent = '$' + data.main_price;
        document.getElementById('detailOldPrice').textContent = data.old_price ? '$' + data.old_price : 'N/A';
        document.getElementById('detailNewPrice').textContent = data.new_price ? '$' + data.new_price : 'N/A';
        
        document.getElementById('detailStock').textContent = data.stock;
        
        let stockClass = 'text-success';
        let stockText = 'In Stock';
        if (data.stock === 0) { stockClass = 'text-danger'; stockText = 'Out of Stock'; }
        else if (data.stock <= 5) { stockClass = 'text-warning'; stockText = 'Low Stock'; }
        
        document.getElementById('detailStockStatus').innerHTML = `<span class="${stockClass}">${stockText}</span>`;
        
        document.getElementById('detailCollection').textContent = data.collection_details ? data.collection_details.title : 'None';
        document.getElementById('detailProductType').textContent = data.product_type_details ? data.product_type_details.title : 'None';
        
        document.getElementById('detailCreatedAt').textContent = new Date(data.created_at).toLocaleString();
        document.getElementById('detailUpdatedAt').textContent = new Date(data.updated_at).toLocaleString();
        
    } catch(err) {
        notify.error('Failed to load product details.');
    }
}
