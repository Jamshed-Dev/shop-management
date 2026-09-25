// Product Types API and DOM logic

async function loadProductTypes() {
    const tbody = document.getElementById('typesTableBody');
    try {
        const data = await api.get('/product-types/');
        const results = data.results || data;
        tbody.innerHTML = '';
        
        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No product types found.</td></tr>';
            return;
        }

        results.forEach(item => {
            const statusBadge = item.is_active 
                ? '<span class="badge bg-success">Active</span>' 
                : '<span class="badge bg-secondary">Inactive</span>';
            
            tbody.innerHTML += `
                <tr>
                    <td>${item.id}</td>
                    <td>${item.title}</td>
                    <td>${item.slug}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <a href="/product-types/${item.id}/edit/" class="btn btn-sm btn-outline-primary">Edit</a>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteProductType(${item.id})">Delete</button>
                    </td>
                </tr>
            `;
        });
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Failed to load product types.</td></tr>';
        notify.error('Failed to load product types');
    }
}

async function initProductTypeForm() {
    const form = document.getElementById('typeForm');
    const saveBtn = document.getElementById('saveBtn');
    const overlay = document.getElementById('formLoadingOverlay');
    
    // Check if edit mode by looking at URL
    const match = window.location.pathname.match(/\/product-types\/(\d+)\/edit\//);
    let editId = null;
    let originalData = null;
    
    if (match) {
        editId = match[1];
        document.getElementById('pageTitle').textContent = 'Edit Product Type';
        if (overlay) {
            overlay.classList.remove('d-none');
            overlay.classList.add('d-flex');
        }
        
        try {
            const data = await api.get(`/product-types/${editId}/`);
            originalData = data;
            
            document.getElementById('title').value = data.title;
            document.getElementById('slug').value = data.slug;
            document.getElementById('description').value = data.description || '';
            document.getElementById('is_active').checked = data.is_active;
        } catch(err) {
            notify.error('Failed to load product type details.');
            saveBtn.disabled = true;
        } finally {
            if (overlay) {
                overlay.classList.remove('d-flex');
                overlay.classList.add('d-none');
            }
        }
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
        
        const currentData = {
            title: document.getElementById('title').value,
            slug: document.getElementById('slug').value,
            description: document.getElementById('description').value,
            is_active: document.getElementById('is_active').checked
        };
        
        let payload = {};
        
        for (const key in currentData) {
            if (editId) {
                let origVal = originalData[key];
                if (origVal === null) origVal = '';
                let curVal = currentData[key];
                if (curVal === null) curVal = '';
                
                if (String(origVal) !== String(curVal)) {
                    payload[key] = currentData[key];
                }
            } else {
                payload[key] = currentData[key];
            }
        }
        
        try {
            if (editId) {
                await api.patch(`/product-types/${editId}/`, payload);
                notify.success('Product Type updated successfully');
            } else {
                await api.post('/product-types/', payload);
                notify.success('Product Type created successfully');
            }
            setTimeout(() => { window.location.href = '/product-types/'; }, 1000);
        } catch(err) {
            notify.error(extractErrorMessage(err));
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Product Type';
        }
    });
}

async function deleteProductType(id) {
    if(!confirm('Are you sure you want to delete this product type?')) return;
    try {
        await api.delete(`/product-types/${id}/`);
        notify.success('Product Type deleted.');
        loadProductTypes();
    } catch(err) {
        notify.error(extractErrorMessage(err) || 'Failed to delete product type');
    }
}
