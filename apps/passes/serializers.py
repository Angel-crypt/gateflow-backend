from typing import Any

from rest_framework import serializers

from apps.destinations.models import Destination
from apps.users.models import User

from .models import AccessPass


class DestinationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["id", "name", "type"]


class CreatedBySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class AccessPassSerializer(serializers.ModelSerializer):
    destination = DestinationSummarySerializer(read_only=True)
    created_by = CreatedBySummarySerializer(read_only=True)

    class Meta:
        model = AccessPass
        fields = [
            "id",
            "destination",
            "created_by",
            "visitor_name",
            "plate",
            "pass_type",
            "valid_from",
            "valid_to",
            "is_active",
            "is_used",
            "created_at",
        ]


class AccessPassWriteSerializer(serializers.ModelSerializer):
    destination = serializers.PrimaryKeyRelatedField(
        queryset=Destination.objects.none(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = AccessPass
        fields = ["destination", "visitor_name", "plate", "pass_type", "valid_from", "valid_to", "is_active"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            user: User = request.user  # type: ignore[assignment]
            if user.role == User.Role.TENANT:
                qs = Destination.objects.filter(responsible=user, is_active=True)
            else:
                qs = Destination.objects.filter(park=user.park, is_active=True)
            self.fields["destination"].queryset = qs  # type: ignore[union-attr, attr-defined]

    def _get_user_destinations(self, user: User):  # type: ignore[return]
        if user.role == User.Role.TENANT:
            return Destination.objects.filter(responsible=user, is_active=True)
        return Destination.objects.filter(park=user.park, is_active=True)

    def validate(self, attrs: dict) -> dict:
        user: User = self.context["request"].user  # type: ignore[assignment]

        # Auto-assign destination on create if not provided
        if not self.instance and not attrs.get("destination"):
            destinations = self._get_user_destinations(user)
            if destinations.count() == 1:
                attrs["destination"] = destinations.first()
            else:
                raise serializers.ValidationError({"destination": "Debes seleccionar un destino."})

        valid_from = attrs.get("valid_from") or (self.instance.valid_from if self.instance else None)
        valid_to = attrs.get("valid_to") or (self.instance.valid_to if self.instance else None)
        if valid_from and valid_to and valid_to <= valid_from:
            raise serializers.ValidationError({"valid_to": "La fecha de fin debe ser posterior a la de inicio."})

        return attrs

    def create(self, validated_data: dict) -> AccessPass:
        return AccessPass.objects.create(
            created_by=self.context["request"].user,
            **validated_data,
        )
