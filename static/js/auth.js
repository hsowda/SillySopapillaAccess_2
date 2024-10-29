document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const externalContentModal = new bootstrap.Modal(document.getElementById('externalContentModal'));
    const gmailModal = new bootstrap.Modal(document.getElementById('gmailModal'));
    const logoutButton = document.getElementById('logoutButton');
    const gmailButton = document.getElementById('gmailButton');
    const externalContentFrame = document.getElementById('externalContentFrame');
    const gmailFrame = document.querySelector('#gmailModal iframe');

    // Handle iframe loading errors
    function handleIframeError(iframe, fallbackUrl) {
        iframe.addEventListener('error', function() {
            console.error(`Failed to load iframe content for ${iframe.src}`);
            if (fallbackUrl) {
                window.open(fallbackUrl, '_blank');
                if (iframe === gmailFrame) {
                    gmailModal.hide();
                }
            }
        });
    }

    // Set up iframe error handlers
    if (externalContentFrame) {
        handleIframeError(externalContentFrame);
    }

    if (gmailFrame) {
        handleIframeError(gmailFrame, 'https://gmail.com');
        
        // Add load event listener to detect X-Frame-Options blocking
        gmailFrame.addEventListener('load', function() {
            try {
                // Try to access iframe content - will throw error if blocked
                const test = gmailFrame.contentWindow.location.href;
            } catch (e) {
                console.error('Gmail iframe access blocked:', e);
                window.open('https://gmail.com', '_blank');
                gmailModal.hide();
            }
        });
    }
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                alert('Please fill in all fields');
                return;
            }

            // Submit form via AJAX
            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'email': email,
                    'password': password
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Set iframe source and show modal
                    if (externalContentFrame) {
                        externalContentFrame.src = data.redirect_url;
                        externalContentModal.show();
                    }
                } else {
                    // Show error message
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
                    alertDiv.innerHTML = `
                        ${data.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    loginForm.insertAdjacentElement('beforebegin', alertDiv);
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                alert('An error occurred during login. Please try again.');
            });
        });
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', function() {
            fetch('/logout')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    externalContentModal.hide();
                    window.location.href = '/login';
                })
                .catch(error => {
                    console.error('Logout error:', error);
                    alert('An error occurred during logout. Please try again.');
                });
        });
    }

    if (gmailButton) {
        gmailButton.addEventListener('click', function() {
            try {
                externalContentModal.hide();
                gmailModal.show();
            } catch (error) {
                console.error('Gmail modal error:', error);
                window.open('https://gmail.com', '_blank');
            }
        });
    }
});
