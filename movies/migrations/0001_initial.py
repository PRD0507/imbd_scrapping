# Generated by Django 4.2.21 on 2025-06-01 18:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('release_year', models.IntegerField()),
                ('imdb_rating', models.FloatField()),
                ('directors', models.TextField()),
                ('cast', models.TextField()),
                ('plot_summary', models.TextField()),
                ('imdb_url', models.URLField(max_length=500)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movies_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movies_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-release_year', 'title'],
                'indexes': [models.Index(fields=['title'], name='movies_movi_title_652549_idx'), models.Index(fields=['release_year'], name='movies_movi_release_81d5c9_idx'), models.Index(fields=['imdb_rating'], name='movies_movi_imdb_ra_8e4972_idx'), models.Index(fields=['is_active'], name='movies_movi_is_acti_00ce83_idx')],
            },
        ),
    ]
