from typing import Any

from rest_framework import serializers

from apps.users.models import User

from .models import Destination, IndustrialPark


class IndustrialParkSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustrialPark
        fields = ["id", "name"]


class ResponsibleSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class DestinationSerializer(serializers.ModelSerializer):
    park = IndustrialParkSerializer(read_only=True)
    responsible = ResponsibleSummarySerializer(read_only=True)

    class Meta:
        model = Destination
        fields = ["id", "name", "type", "park", "responsible", "is_active"]


class DestinationWriteSerializer(serializers.ModelSerializer):
    responsible = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.none(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Destination
        fields = ["name", "type", "responsible", "is_active"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["responsible"].queryset = User.objects.filter(  # type: ignore[union-attr, attr-defined]
                park=request.user.park
            )

    def validate_responsible(self, user: User | None) -> User | None:
        request = self.context.get("request")
        if user and request and user.park != request.user.park:
            raise serializers.ValidationError("El responsable debe pertenecer al mismo parque.")
        return user

    def create(self, validated_data: dict) -> Destination:
        park = self.context["request"].user.park
        return Destination.objects.create(park=park, **validated_data)
