# apps/users/serializers.py
from typing import Any, cast

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.destinations.models import Destination, IndustrialPark

from .models import User


class IndustrialParkSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustrialPark
        fields = ["id", "name"]


class DestinationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["id", "name", "type"]


class UserSerializer(serializers.ModelSerializer):
    park = IndustrialParkSerializer(read_only=True)
    destinations = DestinationSummarySerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "role", "is_active", "park", "destinations"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Contraseña actual incorrecta.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Las contraseñas no coinciden."})
        return attrs

    def save(self, **kwargs) -> User:
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    destinations = serializers.PrimaryKeyRelatedField(
        queryset=Destination.objects.none(),
        many=True,
        required=False,
    )

    class Meta:
        model = User
        fields = ["email", "password", "role", "destinations"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            park = request.user.park
            field = cast(serializers.ManyRelatedField, self.fields["destinations"])
            field.child_relation.queryset = Destination.objects.filter(park=park)  # type: ignore[union-attr]

    def validate_role(self, value: str) -> str:
        if value not in (User.Role.GUARD, User.Role.COMPANY):
            raise serializers.ValidationError("Solo se pueden crear usuarios con rol guard o company.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs.get("role") == User.Role.COMPANY and not attrs.get("destinations"):
            raise serializers.ValidationError({"destinations": "Los usuarios company requieren al menos un destino."})
        return attrs

    def create(self, validated_data: dict) -> User:
        destinations = validated_data.pop("destinations", [])
        park = self.context["request"].user.park
        user = User.objects.create_user(park=park, **validated_data)
        if destinations:
            user.destinations.set(destinations)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs: dict) -> dict[str, Any]:
        data: dict[str, Any] = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
