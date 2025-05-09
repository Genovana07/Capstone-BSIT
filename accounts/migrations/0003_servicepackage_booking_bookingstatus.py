# Generated by Django 5.1.3 on 2025-05-09 03:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_delete_customuser'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ServicePackage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('price', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('contact_number', models.CharField(max_length=15)),
                ('event_date', models.DateField()),
                ('event_time', models.TimeField()),
                ('event_type', models.CharField(max_length=50)),
                ('location', models.CharField(max_length=255)),
                ('audience_size', models.PositiveIntegerField()),
                ('status', models.CharField(default='Processing', max_length=20)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.servicepackage')),
            ],
        ),
        migrations.CreateModel(
            name='BookingStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='Processing', max_length=20)),
                ('booking', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='accounts.booking')),
            ],
        ),
    ]
