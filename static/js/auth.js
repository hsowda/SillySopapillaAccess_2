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
        const logoutButton = document.getElementById('logoutButton');
        const gmailButton = document.getElementById('gmailButton');
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
                const mailtoLink = 'mailto:someone@example.com?subject=This%20is%20the%20subject&cc=someone_else@example.com&body=This%20is%20the%20body';
                window.open(mailtoLink, '_blank');
            });
        }
    } catch (error) {
        logError('DOM Content Loaded', error);
    }
});
