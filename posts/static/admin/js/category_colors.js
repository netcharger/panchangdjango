(function() {
    'use strict';

    // Add CSS styles
    var style = document.createElement('style');
    style.textContent = `
        /* Color parent categories (no parent) - Light blue background */
        #result_list tbody tr[data-category-type="parent"] {
            background-color:rgb(81, 191, 255) !important;
            font-size: 1.2rem !important;
        }
        /* Color child categories (has parent) - Light orange background */
        #result_list tbody tr[data-category-type="child"] {
            background-color: #fff4e6 !important;
        }
    `;
    document.head.appendChild(style);

    function colorCategoryRows() {
        const rows = document.querySelectorAll('#result_list tbody tr');
        rows.forEach(function(row) {
            const parentCell = row.querySelector('td.field-parent');
            if (parentCell) {
                const parentText = parentCell.textContent.trim();
                // Check if parent column is empty or contains dash (Django's empty value display)
                if (parentText === '' || parentText === '-') {
                    // Parent category - light blue background
                    row.style.backgroundColor = '#e8f4f8';
                    row.setAttribute('data-category-type', 'parent');
                } else {
                    // Child category - light orange background
                    row.style.backgroundColor = '#fff4e6';
                    row.setAttribute('data-category-type', 'child');
                }
            }
        });
    }

    // Run on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', colorCategoryRows);
    } else {
        colorCategoryRows();
    }

    // Also run after AJAX updates (for filtering, sorting, pagination, etc.)
    setTimeout(function() {
        const observer = new MutationObserver(colorCategoryRows);
        const resultList = document.getElementById('result_list');
        if (resultList) {
            observer.observe(resultList, { childList: true, subtree: true });
        }
    }, 100);
})();

