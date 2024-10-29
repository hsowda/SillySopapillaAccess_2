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
        const logoutButtons = document.querySelectorAll('.logout-btn');
        const externalContentFrame = document.getElementById('externalContentFrame');

        // Handle iframe loading errors for external content
        if (externalContentFrame) {
            externalContentFrame.addEventListener('error', function(e) {
                logError('iframe loading', e);
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

        // Handle logout for all logout buttons
        if (logoutButtons.length > 0) {
            logoutButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    try {
                        e.preventDefault();
                        fetch('/logout', {
                            method: 'GET',
                            credentials: 'same-origin'
                        })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }
                            // Hide modal if it exists and is shown
                            if (externalContentModal) {
                                externalContentModal.hide();
                                // Wait for modal to finish hiding before redirecting
                                setTimeout(() => {
                                    window.location.href = '/login';
                                }, 300);
                            } else {
                                window.location.href = '/login';
                            }
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
            });
        }
    } catch (error) {
        logError('DOM Content Loaded', error);
    }
});
