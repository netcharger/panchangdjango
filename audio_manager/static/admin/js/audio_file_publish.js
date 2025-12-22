(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Handle publish/unpublish button clicks in detail view (change page)
        $(document).on('click', '.publish-toggle-btn', function(e) {
            e.preventDefault();
            e.stopPropagation();
            var $btn = $(this);
            var url = $btn.attr('href');
            var $statusText = $btn.closest('.publish-button-container').find('.publish-status-text');
            var originalText = $btn.text();
            
            // Disable button and show loading
            $btn.prop('disabled', true).text('Processing...');
            
            $.ajax({
                url: url,
                type: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                success: function(data) {
                    if (data.success) {
                        // Update button text and status
                        if (data.is_published) {
                            $btn.text('Unpublish').removeClass('publish-btn').addClass('unpublish-btn');
                            $statusText.html('<strong>Status:</strong> <span style="color: green;">Currently Published</span>');
                        } else {
                            $btn.text('Publish').removeClass('unpublish-btn').addClass('publish-btn');
                            $statusText.html('<strong>Status:</strong> <span style="color: red;">Currently Unpublished</span>');
                        }
                        
                        // Update the is_published checkbox if it exists
                        var $checkbox = $('#id_is_published');
                        if ($checkbox.length) {
                            $checkbox.prop('checked', data.is_published);
                        }
                        
                        // Show success message
                        var $messages = $('.messagelist');
                        if ($messages.length === 0) {
                            $messages = $('<ul class="messagelist"></ul>');
                            $('.content').first().prepend($messages);
                        }
                        $messages.prepend('<li class="success">' + data.message + '</li>');
                        
                        // Fade out message after 3 seconds
                        setTimeout(function() {
                            $messages.find('li:first').fadeOut(function() {
                                $(this).remove();
                                if ($messages.find('li').length === 0) {
                                    $messages.remove();
                                }
                            });
                        }, 3000);
                    }
                },
                error: function(xhr, status, error) {
                    alert('Error: ' + (xhr.responseJSON?.message || 'Failed to toggle publish status'));
                    $btn.text(originalText);
                },
                complete: function() {
                    $btn.prop('disabled', false);
                }
            });
            
            return false;
        });
        
        // Handle publish/unpublish button clicks in list view
        $(document).on('click', '.publish-toggle-list-btn', function(e) {
            e.preventDefault();
            e.stopPropagation();
            var $btn = $(this);
            var $cell = $btn.closest('td');
            var url = $btn.attr('href');
            var originalText = $btn.text();
            
            // Disable button and show loading
            $btn.prop('disabled', true).text('...');
            
            $.ajax({
                url: url,
                type: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                success: function(data) {
                    if (data.success) {
                        // Update status and button
                        if (data.is_published) {
                            $cell.find('.publish-status').html('<span style="color: green; font-weight: bold;">✓ Published</span>');
                            $btn.text('Unpublish');
                        } else {
                            $cell.find('.publish-status').html('<span style="color: red; font-weight: bold;">✗ Unpublished</span>');
                            $btn.text('Publish');
                        }
                        
                        // Show success message at top of page
                        var $messages = $('.messagelist');
                        if ($messages.length === 0) {
                            $messages = $('<ul class="messagelist"></ul>');
                            $('.content').first().prepend($messages);
                        }
                        $messages.prepend('<li class="success">' + data.message + '</li>');
                        
                        // Fade out message after 3 seconds
                        setTimeout(function() {
                            $messages.find('li:first').fadeOut(function() {
                                $(this).remove();
                                if ($messages.find('li').length === 0) {
                                    $messages.remove();
                                }
                            });
                        }, 3000);
                    }
                },
                error: function(xhr, status, error) {
                    alert('Error: ' + (xhr.responseJSON?.message || 'Failed to toggle publish status'));
                    $btn.text(originalText);
                },
                complete: function() {
                    $btn.prop('disabled', false);
                }
            });
            
            return false;
        });
    });
})(django.jQuery);

