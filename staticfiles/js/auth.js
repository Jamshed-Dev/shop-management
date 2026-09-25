document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const submitBtn = document.getElementById('submitBtn');
            const errorAlert = document.getElementById('errorAlert');
            
            errorAlert.classList.add('d-none');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Signing in...';
            
            try {
                // 1. Get tokens
                const response = await fetch('/auth/jwt/create/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email, password: password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    api.setTokens(data.access, data.refresh);
                    
                    // 2. Fetch user profile to ensure they are staff/admin
                    try {
                        const profileResponse = await fetch('/auth/user-profile/', {
                            method: 'GET',
                            headers: { 'Authorization': `Bearer ${data.access}` }
                        });
                        
                        if (profileResponse.ok) {
                            const profileData = await profileResponse.json();
                            // In a real application, check profileData[0].is_staff or similar
                            // The UserProfileViewSet list() method returns a single serialized object or a list?
                            // In views.py: return Response(serializer.data) which is the user object.
                            
                            if (profileData.is_staff === false) {
                                api.clearTokens();
                                throw new Error("You do not have permission to access the admin dashboard.");
                            }
                            
                            // Check next param
                            const urlParams = new URLSearchParams(window.location.search);
                            const nextUrl = urlParams.get('next');
                            if (nextUrl && nextUrl.startsWith('/')) {
                                window.location.href = nextUrl;
                            } else {
                                window.location.href = '/dashboard/';
                            }
                        } else {
                            throw new Error("Failed to verify user permissions.");
                        }
                    } catch(permErr) {
                        api.clearTokens();
                        throw permErr;
                    }
                } else {
                    throw data;
                }
            } catch (err) {
                errorAlert.classList.remove('d-none');
                errorAlert.textContent = extractErrorMessage(err) || 'Invalid login credentials.';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Sign In';
            }
        });
    }
    
    // Global Logout listener
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            api.logout();
        });
    }

    // Protect routes (basic frontend check, backend still secures API)
});
