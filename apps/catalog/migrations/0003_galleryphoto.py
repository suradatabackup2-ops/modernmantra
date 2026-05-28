# Modern Mantra — adds the GalleryPhoto model (DB-backed, R2-stored gallery).

import apps.catalog.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_package_data_trip'),
    ]

    operations = [
        migrations.CreateModel(
            name='GalleryPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=apps.catalog.models.gallery_image_path)),
                ('caption', models.CharField(blank=True, help_text='Shown on hover and in the lightbox', max_length=160)),
                ('category', models.CharField(choices=[('base', 'Modern Mantra Base'), ('nature', 'Nature & Landscape'), ('group', 'Group Moments'), ('winter', 'Winter & Snow'), ('water', 'Waterfalls')], default='nature', help_text='Controls which filter tab the photo appears under', max_length=16)),
                ('is_active', models.BooleanField(default=True, help_text='Uncheck to hide without deleting')),
                ('display_order', models.PositiveSmallIntegerField(default=100, help_text='Lower numbers shown first')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Gallery photo',
                'verbose_name_plural': 'Gallery photos',
                'ordering': ['display_order', '-created_at'],
            },
        ),
    ]
