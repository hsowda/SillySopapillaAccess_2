// Global error handler
window.onerror = function(message, source, lineno, colno, error) {
    console.error('Global error:', {
        message: message,
        source: source,
        lineno: lineno,
        colno: colno,
        error: error
    });
    return false;
};

// Utility function for error logging
function logError(context, error) {
    console.error(`Error in ${context}:`, {
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
    });
}

document.addEventListener('DOMContentLoaded', function() {
    try {
        const loginForm = document.getElementById('loginForm');
        const externalContentModal = document.getElementById('externalContentModal') ? 
            new bootstrap.Modal(document.getElementById('externalContentModal')) : null;
        const gmailModal = document.getElementById('gmailModal') ? 
            new bootstrap.Modal(document.getElementById('gmailModal')) : null;
        const logoutButton = document.getElementById('logoutButton');
        const gmailButton = document.getElementById('gmailButton');
        const externalContentFrame = document.getElementById('externalContentFrame');
        const gmailFrame = document.querySelector('#gmailModal iframe');

        // Handle iframe loading errors
        function handleIframeError(iframe, fallbackUrl) {
            try {
                iframe.addEventListener('error', function(e) {
                    logError('iframe loading', e);
                    if (fallbackUrl) {
                        window.open(fallbackUrl, '_blank');
                        if (iframe === gmailFrame && gmailModal) {
                            gmailModal.hide();
                        }
                    }
                });
            } catch (error) {
                logError('handleIframeError setup', error);
            }
        }

        // Set up iframe error handlers
        if (externalContentFrame) {
            handleIframeError(externalContentFrame);
        }

        if (gmailFrame) {
            handleIframeError(gmailFrame, 'https://gmail.com');
            
            gmailFrame.addEventListener('load', function() {
                try {
                    const test = gmailFrame.contentWindow.location.href;
                } catch (e) {
                    logError('Gmail iframe access', e);
                    window.open('https://gmail.com', '_blank');
                    if (gmailModal) {
                        gmailModal.hide();
                    }
                }
            });
        }
        
        if (loginForm) {
            loginForm.addEventListener('submit', function(e) {
                try {
                    e.preventDefault();
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const remember = document.getElementById('remember').checked;
                    
                    if (!email || !password) {
                        alert('Please fill in all fields');
                        return;
                    }

                    fetch('/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: new URLSearchParams({
                            'email': email,
                            'password': password,
                            'remember': remember
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            if (externalContentFrame && externalContentModal) {
                                externalContentFrame.src = data.redirect_url;
                                externalContentModal.show();
                            }
                        } else {
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
                        logError('login fetch', error);
                        alert('An error occurred during login. Please try again.');
                    });
                } catch (error) {
                    logError('login form submission', error);
                    alert('An error occurred. Please try again.');
                }
            });
        }

        if (logoutButton) {
            logoutButton.addEventListener('click', function() {
                try {
                    fetch('/logout')
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }
                            if (externalContentModal) {
                                externalContentModal.hide();
                            }
                            window.location.href = '/login';
                        })
                        .catch(error => {
                            logError('logout', error);
                            alert('An error occurred during logout. Please try again.');
                        });
                } catch (error) {
                    logError('logout button click', error);
                    alert('An error occurred. Please try again.');
                }
            });
        }

        if (gmailButton) {
            gmailButton.addEventListener('click', function() {
                try {
                    if (externalContentModal) {
                        externalContentModal.hide();
                    }
                    if (gmailModal) {
                        gmailModal.show();
                    }
                } catch (error) {
                    logError('Gmail modal', error);
                    window.open('https://gmail.com', '_blank');
                }
            });
        }
    } catch (error) {
        logError('DOM Content Loaded', error);
    }
});
