from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWT
from auth_app.models import BlockJWT

class JWTAuthentication(BaseJWT):
    def authenticate(self, request):
        header = self.get_header(request)
        
        if header is None:
            # Fallback to reading from cookie for template views
            raw_token = request.COOKIES.get('access')
            if raw_token:
                # Convert string to bytes since get_raw_token expects bytes and returns bytes
                raw_token = raw_token.encode('utf-8')
        else:
            raw_token = self.get_raw_token(header)
            
        if not raw_token:
            return None
        
        # Check if the token is blocked
        if BlockJWT.objects.filter(access=raw_token).exists():
            return None
        
        # Validate the token
        validated_token = self.get_validated_token(raw_token)

        # Return the user and the validated token
        return self.get_user(validated_token), validated_token


