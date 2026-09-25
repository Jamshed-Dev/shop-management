// Collections API and DOM logic

async function loadCollections() {
    const tbody = document.getElementById('collectionsTableBody');
    try {
        const data = await api.get('/collections/');
        const results = data.results || data;
        tbody.innerHTML = '';
        
        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No collections found.</td></tr>';
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
                        <a href="/collections/${item.id}/edit/" class="btn btn-sm btn-outline-primary">Edit</a>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteCollection(${item.id})">Delete</button>
                    </td>
                </tr>
            `;
        });
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Failed to load collections.</td></tr>';
        notify.error('Failed to load collections');
    }
}

async function initCollectionForm() {
    const form = document.getElementById('collectionForm');
    const saveBtn = document.getElementById('saveBtn');
    
    const imageInput = document.getElementById('image');
    const imageUrlInput = document.getElementById('image_url');
    const imagePreview = document.getElementById('imagePreview');
    const overlay = document.getElementById('formLoadingOverlay');

    if (imageInput && imageUrlInput && imagePreview) {
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
    }
    
    // Check if edit mode by looking at URL
    const match = window.location.pathname.match(/\/collections\/(\d+)\/edit\//);
    let editId = null;
    let originalData = null;
    
    if (match) {
        editId = match[1];
        document.getElementById('pageTitle').textContent = 'Edit Collection';
        if (overlay) {
            overlay.classList.remove('d-none');
            overlay.classList.add('d-flex');
        }
        
        try {
            const data = await api.get(`/collections/${editId}/`);
            originalData = data;
            
            document.getElementById('title').value = data.title;
            document.getElementById('slug').value = data.slug;
            document.getElementById('description').value = data.description || '';
            document.getElementById('is_active').checked = data.is_active;
            
            if (imageUrlInput && imagePreview) {
                if (data.image_url) {
                    imageUrlInput.value = data.image_url;
                }
                if (data.image) {
                    imagePreview.src = data.image;
                } else if (data.image_url) {
                    imagePreview.src = data.image_url;
                }
            }
        } catch(err) {
            notify.error('Failed to load collection details.');
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
        
        const hasFile = imageInput && imageInput.files.length > 0;
        let payload;
        let isFormData = false;
        
        const currentData = {
            title: document.getElementById('title').value,
            slug: document.getElementById('slug').value,
            description: document.getElementById('description').value,
            is_active: document.getElementById('is_active').checked,
            image_url: (imageUrlInput ? imageUrlInput.value : '')
        };
        
        if (hasFile || editId === null) {
            isFormData = true;
            payload = new FormData();
            
            for (const key in currentData) {
                if (editId) {
                    let origVal = originalData[key];
                    if (origVal === null) origVal = '';
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
            payload = {};
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
        }
        
        try {
            if (editId) {
                await api.patch(`/collections/${editId}/`, payload, isFormData);
                notify.success('Collection updated successfully');
            } else {
                await api.post('/collections/', payload, isFormData);
                notify.success('Collection created successfully');
            }
            setTimeout(() => { window.location.href = '/collections/'; }, 1000);
        } catch(err) {
            notify.error(extractErrorMessage(err));
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Collection';
        }
    });
}

async function deleteCollection(id) {
    if(!confirm('Are you sure you want to delete this collection?')) return;
    try {
        await api.delete(`/collections/${id}/`);
        notify.success('Collection deleted.');
        loadCollections();
    } catch(err) {
        notify.error(extractErrorMessage(err) || 'Failed to delete collection');
    }
}
