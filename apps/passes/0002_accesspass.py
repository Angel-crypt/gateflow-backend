import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("passes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesspass",
            name="qr_code",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="accesspass",
            name="is_used",
            field=models.BooleanField(default=False),
        ),
    ]