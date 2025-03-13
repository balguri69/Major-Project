// Image preview functionality for file inputs
document.addEventListener('DOMContentLoaded', function() {
    // For sender image upload
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            previewImage(this, 'imagePreview');
        });
    }
    
    // For receiver encoded image upload
    const encodedImageInput = document.getElementById('encoded_image');
    if (encodedImageInput) {
        encodedImageInput.addEventListener('change', function() {
            previewImage(this, 'encodedImagePreview');
        });
    }
    
    // Function to create/update image preview
    function previewImage(input, previewId) {
        // Check if preview element exists, create if not
        let preview = document.getElementById(previewId);
        if (!preview) {
            preview = document.createElement('div');
            preview.id = previewId;
            preview.className = 'mt-3';
            input.parentNode.appendChild(preview);
        }
        
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                preview.innerHTML = `
                    <p>Preview:</p>
                    <img src="${e.target.result}" alt="Preview" class="img-fluid" style="max-height: 200px; max-width: 100%;">
                `;
            }
            
            reader.readAsDataURL(input.files[0]);
        } else {
            preview.innerHTML = '';
        }
    }
});

// Tab persistence
document.addEventListener('DOMContentLoaded', function() {
    // Get active tab from localStorage
    const activeTab = localStorage.getItem('activeTab');
    
    // If there is an active tab stored
    if (activeTab) {
        // Find the tab button
        const tabButton = document.querySelector(`button[data-bs-target="${activeTab}"]`);
        
        // If the tab button exists, click it
        if (tabButton) {
            tabButton.click();
        }
    }
    
    // Add event listeners to all tab buttons
    const tabButtons = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', function(event) {
            // Store the active tab in localStorage
            localStorage.setItem('activeTab', event.target.getAttribute('data-bs-target'));
        });
    });
});