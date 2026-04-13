from django.db import migrations, models


def add_legacy_name(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="contenttype",
            options={
                "verbose_name": "content type",
                "verbose_name_plural": "content types",
            },
        ),
        migrations.AlterField(
            model_name="contenttype",
            name="name",
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.RunPython(
            migrations.RunPython.noop,
            add_legacy_name,
            hints={"model_name": "contenttype"},
        ),
        migrations.RemoveField(
            model_name="contenttype",
            name="name",
        ),
    ]
