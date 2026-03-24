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
    )

    class Meta:
        model = AccessPass
        fields = ["destination", "visitor_name", "plate", "pass_type", "valid_from", "valid_to", "is_active"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            user: User = request.user  # type: ignore[assignment]
            qs = Destination.objects.filter(park=user.park, is_active=True)
            if user.role == User.Role.TENANT:
                qs = qs.filter(responsible=user)
            elif user.role == "admin":
                qs = qs.filter(type=Destination.Type.AREA)
            self.fields["destination"].queryset = qs  # type: ignore[union-attr, attr-defined]

    def validate(self, attrs: dict) -> dict:
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
