// Inventory API and DOM logic
let currentInvPage = 1;

async function loadInventory() {
    const tbody = document.getElementById('inventoryTableBody');
    const type = document.getElementById('filterType')?.value || '';
    
    try {
        const data = await api.get('/inventory-transactions/', {
            page: currentInvPage,
            transaction_type: type
        });
        
        const results = data.results || data;
        tbody.innerHTML = '';
        
        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">No transactions found.</td></tr>';
            if (document.getElementById('pageInfo')) document.getElementById('pageInfo').textContent = 'Showing 0 results';
            return;
        }

        results.forEach(tx => {
            const isPos = tx.quantity > 0;
            const qtyStr = isPos ? `+${tx.quantity}` : `${tx.quantity}`;
            const qtyClass = isPos ? 'text-success fw-bold' : 'text-danger fw-bold';
            
            const prodName = tx.variant ? `Variant #${tx.variant}` : `Product #${tx.product}`;
            const orderLink = tx.order ? `<a href="/orders/${tx.order}/">#${tx.order}</a>` : '-';
            
            tbody.innerHTML += `
                <tr>
                    <td>${tx.id}</td>
                    <td>${prodName}</td>
                    <td>${tx.transaction_type}</td>
                    <td class="${qtyClass}">${qtyStr}</td>
                    <td>${tx.stock_after}</td>
                    <td>${orderLink}</td>
                    <td>${tx.reason || ''}</td>
                    <td>${new Date(tx.created_at).toLocaleString()}</td>
                </tr>
            `;
        });
        
        if (data.count !== undefined) {
            document.getElementById('pageInfo').textContent = `Total: ${data.count}`;
            document.getElementById('prevPage').disabled = !data.previous;
            document.getElementById('nextPage').disabled = !data.next;
            
            document.getElementById('prevPage').onclick = () => { if(data.previous) { currentInvPage--; loadInventory(); } };
            document.getElementById('nextPage').onclick = () => { if(data.next) { currentInvPage++; loadInventory(); } };
        }
    } catch(err) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Failed to load inventory logs.</td></tr>';
        notify.error('Failed to load inventory');
    }
}
