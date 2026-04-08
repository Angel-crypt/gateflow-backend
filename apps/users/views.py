from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import IsAdmin
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Obtener tokens JWT.

    Retorna `access`, `refresh` y el objeto `user` con el perfil completo del usuario autenticado.
    """

    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """
    Cerrar sesión.

    Invalida el `refresh` token enviado en el cuerpo. A partir de este momento
    dicho token no podrá usarse para generar nuevos `access` tokens.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Se requiere el token de refresco."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response({"detail": "Token inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """
    Perfil del usuario autenticado.

    Retorna los datos completos del usuario que realiza la petición,
    incluyendo su parque industrial y destinos asociados.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    """
    Cambiar contraseña.

    Requiere la contraseña actual para confirmar la identidad.
    La nueva contraseña debe tener al menos 8 caracteres.
    Retorna 204 sin cuerpo si el cambio fue exitoso.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserListCreateView(generics.ListCreateAPIView):
    """
    Listar y crear usuarios del parque. Solo Admin.

    **GET** — Retorna todos los usuarios (guardias e inquilinos) del mismo parque industrial
    que el admin autenticado. Soporta filtros por query param:
    - `role`: `guard` | `tenant`
    - `is_active`: `true` | `false`

    **POST** — Crea un nuevo usuario asignado automáticamente al parque del admin.
    Solo se permiten roles `guard` y `tenant`; no se puede crear otro admin.
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        qs = User.objects.filter(park=self.request.user.park, is_superuser=False).order_by("id")

        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        return qs

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Detalle, editar y eliminar usuario del parque. Solo Admin.

    **GET** — Retorna el usuario por id dentro del mismo parque del admin.
    **PATCH** — Actualiza parcialmente email, nombre, apellido, rol o estado activo.
    **DELETE** — Elimina el usuario.
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        return User.objects.filter(park=self.request.user.park, is_superuser=False).order_by("id")

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
