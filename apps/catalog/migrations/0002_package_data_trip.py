from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="data_trip",
            field=models.CharField(
                blank=True,
                max_length=200,
                help_text="Must match the data-trip attribute on the packages.html card exactly. Leave blank to auto-use the package name.",
            ),
        ),
    ]
