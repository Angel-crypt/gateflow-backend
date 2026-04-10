from rest_framework import serializers

from apps.access.models import AccessLog


class AccessTableSerializer(serializers.ModelSerializer):
    destination = serializers.CharField(source="destination.name")
    guard = serializers.SerializerMethodField()
    pass_id = serializers.SerializerMethodField()
    pass_type = serializers.SerializerMethodField()

    class Meta:
        model = AccessLog
        fields = [
            "id",
            "visitor_name",
            "plate",
            "destination",
            "access_type",
            "pass_id",
            "pass_type",
            "guard",
            "entry_time",
            "exit_time",
            "status",
        ]

    def get_guard(self, obj: AccessLog) -> str:
        if not obj.guard:
            return ""
        full_name = f"{obj.guard.first_name} {obj.guard.last_name}".strip()
        return full_name or obj.guard.email

    def get_pass_id(self, obj: AccessLog) -> int | None:
        return obj.access_pass_id if obj.access_pass_id else None

    def get_pass_type(self, obj: AccessLog) -> str | None:
        if obj.access_pass:
            return obj.access_pass.get_pass_type_display()
        return None
