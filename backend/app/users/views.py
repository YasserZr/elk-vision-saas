import logging

from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import ChangePasswordSerializer, RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that returns tokens + user data"""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Get the user based on username from request
            username = request.data.get('username')
            try:
                user = User.objects.get(username=username)
                user_serializer = UserSerializer(user)
                response.data['user'] = user_serializer.data
            except User.DoesNotExist:
                pass
        return response


class UserProfileView(APIView):
    """Get authenticated user profile"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        """Update user profile"""
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {user.username} updated their profile")
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"New user registered: {user.username}")
            return Response(
                {
                    "user": UserSerializer(user).data,
                    "message": "User registered successfully",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Change user password"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.data.get("new_password"))
            user.save()
            logger.info(f"User {user.username} changed their password")
            return Response(
                {"message": "Password updated successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
