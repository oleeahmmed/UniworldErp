document.addEventListener('DOMContentLoaded', function() {
    const html = document.documentElement;
    const orderItemsFormset = document.getElementById('orderItemsFormset');
    const contextMenu = document.getElementById('contextMenu');
    const addRowBtn = document.getElementById('addRowBtn');
    const removeRowBtn = document.getElementById('removeRowBtn');

    let targetRow = null;

    // Formset functionality
    orderItemsFormset.addEventListener('contextmenu', showContextMenu);
    document.addEventListener('click', hideContextMenu);

    addRowBtn.addEventListener('click', () => {
        addFormsetRow();
        hideContextMenu();
    });

    removeRowBtn.addEventListener('click', () => {
        if (targetRow && orderItemsFormset.children.length > 1) {
            targetRow.remove();
            updateFormsetIndexes();
        }
        hideContextMenu();
    });

    orderItemsFormset.addEventListener('input', updateTotal);

    function addFormsetRow() {
        const totalForms = document.querySelector('[name$="-TOTAL_FORMS"]');
        if (!totalForms) {
            console.error("Could not find TOTAL_FORMS input");
            return;
        }
        const newIndex = parseInt(totalForms.value);
        const lastRow = orderItemsFormset.querySelector('.formset-row:last-child');
        if (!lastRow) {
            console.error("Could not find last formset row");
            return;
        }
        const newRow = lastRow.cloneNode(true);
        
        newRow.innerHTML = newRow.innerHTML.replace(/-(\d+)-/g, function(match, p1) {
            return `-${newIndex}-`;
        });
        newRow.querySelectorAll('input').forEach(input => {
            input.value = '';
            input.name = input.name.replace(/-\d+-/, `-${newIndex}-`);
            input.id = input.id.replace(/-\d+-/, `-${newIndex}-`);
        });
        
        orderItemsFormset.appendChild(newRow);
        totalForms.value = newIndex + 1;
        updateFormsetIndexes();
    }

    function updateFormsetIndexes() {
        const rows = orderItemsFormset.querySelectorAll('.formset-row');
        const totalForms = document.querySelector('[name$="-TOTAL_FORMS"]');
        if (!totalForms) {
            console.error("Could not find TOTAL_FORMS input");
            return;
        }
        rows.forEach((row, index) => {
            row.querySelectorAll('input').forEach(input => {
                input.name = input.name.replace(/-\d+-/, `-${index}-`);
                input.id = input.id.replace(/-\d+-/, `-${index}-`);
            });
        });
        totalForms.value = rows.length;
    }

    function showContextMenu(e) {
        e.preventDefault();
        targetRow = e.target.closest('.formset-row');
        contextMenu.style.display = 'block';
        contextMenu.style.left = `${e.clientX}px`;
        contextMenu.style.top = `${e.clientY}px`;
    }

    function hideContextMenu() {
        contextMenu.style.display = 'none';
    }

    function updateTotal(e) {
        if (e.target.name.includes('quantity') || e.target.name.includes('unit_price')) {
            const row = e.target.closest('tr');
            const quantity = parseFloat(row.querySelector('input[name$="quantity"]').value) || 0;
            const unitPrice = parseFloat(row.querySelector('input[name$="unit_price"]').value) || 0;
            const total = quantity * unitPrice;
            row.querySelector('input[name$="total"]').value = total.toFixed(2);
        }
    }

    // Dark mode toggle
    const toggleCheckbox = document.getElementById('toggle');
    toggleCheckbox.addEventListener('change', function() {
        if (this.checked) {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }
    });
});