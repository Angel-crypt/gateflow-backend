from typing import Any

from django.utils import timezone
from rest_framework import serializers

from apps.destinations.models import Destination
from apps.passes.models import AccessPass
from apps.users.models import User

from .models import AccessLog


class AccessPassSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPass
        fields = ["id", "visitor_name", "plate", "pass_type", "valid_from", "valid_to"]


class DestinationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["id", "name", "type"]


class GuardSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class AccessLogSerializer(serializers.ModelSerializer):
    access_pass = AccessPassSummarySerializer(read_only=True)
    destination = DestinationSummarySerializer(read_only=True)
    guard = GuardSummarySerializer(read_only=True)

    class Meta:
        model = AccessLog
        fields = [
            "id",
            "access_pass",
            "destination",
            "guard",
            "visitor_name",
            "plate",
            "notes",
            "access_type",
            "entry_time",
            "exit_time",
            "status",
            "created_at",
        ]


class AccessLogCreateSerializer(serializers.ModelSerializer):
    access_pass = serializers.PrimaryKeyRelatedField(
        queryset=AccessPass.objects.all(),
        required=False,
        allow_null=True,
    )
    destination = serializers.PrimaryKeyRelatedField(
        queryset=Destination.objects.none(),
        required=False,
        allow_null=True,
    )
    entry_time = serializers.DateTimeField(required=False)

    class Meta:
        model = AccessLog
        fields = ["access_pass", "destination", "visitor_name", "plate", "notes", "entry_time"]
        extra_kwargs = {
            "visitor_name": {"required": False},
            "plate": {"required": False, "allow_blank": True},
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["destination"].queryset = Destination.objects.filter(  # type: ignore[union-attr, attr-defined]
                park=request.user.park, is_active=True
            )

    def validate(self, attrs: dict) -> dict:
        access_pass: AccessPass | None = attrs.get("access_pass")

        if access_pass:
            if not access_pass.is_valid():
                raise serializers.ValidationError({"access_pass": "El pase no es válido o ha expirado."})

            guard: User = self.context["request"].user  # type: ignore[assignment]
            if access_pass.destination.park != guard.park:
                raise serializers.ValidationError({"access_pass": "El pase no pertenece a este parque."})

            # Transcribe data from the pass — no re-entry needed
            attrs["visitor_name"] = access_pass.visitor_name
            attrs["plate"] = access_pass.plate
            attrs["destination"] = access_pass.destination
        else:
            errors: dict = {}
            if not attrs.get("visitor_name"):
                errors["visitor_name"] = "Requerido para acceso manual."
            if not attrs.get("plate"):
                errors["plate"] = "Requerido para acceso manual."
            if not attrs.get("destination"):
                errors["destination"] = "Requerido para acceso manual."
            if errors:
                raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data: dict) -> AccessLog:
        access_pass = validated_data.get("access_pass")
        validated_data.setdefault("entry_time", timezone.now())
        validated_data["access_type"] = AccessLog.AccessType.QR if access_pass else AccessLog.AccessType.MANUAL
        log = AccessLog.objects.create(guard=self.context["request"].user, **validated_data)

        if access_pass and access_pass.pass_type == AccessPass.PassType.SINGLE:
            access_pass.is_used = True
            access_pass.save(update_fields=["is_used", "updated_at"])

        return log
