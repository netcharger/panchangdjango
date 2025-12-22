(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Wait a bit for Django admin to fully load
        setTimeout(function() {
            // Get the filter elements - Django admin uses specific IDs
            var mainCategorySelect = $('#changelist-filter select[name="main_category"]');
            var subCategorySelect = $('#changelist-filter select[name="sub_category"]');
            
            // Function to update subcategory dropdown based on main category
            function updateSubCategoryFilter() {
                var mainCategoryId = mainCategorySelect.val();
                
                if (mainCategoryId) {
                    // Reload the page with main_category filter to update subcategory options
                    var currentUrl = window.location.href;
                    var url = new URL(currentUrl);
                    url.searchParams.set('main_category', mainCategoryId);
                    
                    // Clear subcategory if it doesn't belong to the new main category
                    // The server will handle filtering the options
                    url.searchParams.delete('sub_category');
                    
                    // Reload to get updated subcategory options
                    window.location.href = url.toString();
                } else {
                    // If main category is cleared, reload to show all subcategories
                    var currentUrl = window.location.href;
                    var url = new URL(currentUrl);
                    url.searchParams.delete('main_category');
                    url.searchParams.delete('sub_category');
                    window.location.href = url.toString();
                }
            }
            
            // Listen for main category changes
            if (mainCategorySelect.length) {
                mainCategorySelect.on('change', function() {
                    updateSubCategoryFilter();
                });
            }
        }, 100);
    });
})(django.jQuery);
