# Generated by Django 5.0.7 on 2024-07-18 22:54

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailNotification',
            fields=[
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False, unique=True)),
                ('type', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='InviteCodes',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('uses', models.IntegerField(default=0)),
                ('enabled', models.BooleanField(default=True)),
                ('expires', models.TimeField(blank=True, null=True)),
                ('code', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='NotificationMessageType',
            fields=[
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Cookies',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('value', models.CharField(max_length=255)),
                ('expires_at', models.DateTimeField()),
                ('user_uid', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.user', to_field='uid')),
            ],
        ),
        migrations.CreateModel(
            name='EmailNotify',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('date', models.DateField()),
                ('notification_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backendApi.emailnotification')),
                ('to_uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.user', to_field='uid')),
            ],
        ),
        migrations.CreateModel(
            name='NotificationMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('message', models.TextField()),
                ('from_uid', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sender_uid', to='user.user', to_field='uid')),
                ('to_uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.user', to_field='uid')),
                ('message_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backendApi.notificationmessagetype')),
            ],
        ),
        migrations.CreateModel(
            name='OtpTokenVerify',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('token', models.CharField(max_length=255)),
                ('expires_at', models.DateTimeField()),
                ('user_uid', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.user', to_field='uid')),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionCodes',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('enabled', models.BooleanField(default=True)),
                ('expires', models.TimeField(blank=True, null=True)),
                ('days', models.IntegerField(default=30)),
                ('code', models.CharField(max_length=30)),
                ('used_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.user', to_field='uid')),
            ],
        ),
        migrations.CreateModel(
            name='Subscriptions',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('item_price_id', models.CharField(max_length=50)),
                ('customer_id', models.CharField(max_length=50)),
                ('subscription_id', models.CharField(max_length=50)),
                ('invoice_id', models.CharField(max_length=50)),
                ('item_type', models.CharField(max_length=50)),
                ('quantity', models.IntegerField(default=1)),
                ('unit_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('activated_at', models.DateTimeField()),
                ('billing_period', models.IntegerField(default=1)),
                ('billing_period_unit', models.CharField(max_length=50)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('currency_code', models.CharField(max_length=50)),
                ('current_term_start', models.DateTimeField()),
                ('current_term_end', models.DateTimeField()),
                ('next_billing_at', models.DateTimeField()),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('remaining_billing_cycles', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(max_length=50)),
                ('total_dues', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('archived', models.BooleanField(default=False)),
                ('user_uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.user', to_field='uid')),
            ],
        ),
        migrations.CreateModel(
            name='Payments',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('customer_id', models.CharField(max_length=100)),
                ('txn_id', models.CharField(max_length=100)),
                ('payment_type', models.CharField(max_length=50)),
                ('gateway', models.CharField(max_length=50)),
                ('issuing_country', models.CharField(max_length=50)),
                ('card_last4', models.CharField(blank=True, max_length=4, null=True)),
                ('card_brand', models.CharField(blank=True, max_length=50, null=True)),
                ('card_funding_type', models.CharField(blank=True, max_length=50, null=True)),
                ('card_expiry_month', models.CharField(blank=True, max_length=50, null=True)),
                ('card_expiry_year', models.CharField(blank=True, max_length=50, null=True)),
                ('paypal_email', models.CharField(blank=True, max_length=50, null=True)),
                ('bank_last4', models.CharField(blank=True, max_length=4, null=True)),
                ('bank_person_name_on_account', models.CharField(blank=True, max_length=50, null=True)),
                ('bank_name', models.CharField(blank=True, max_length=50, null=True)),
                ('bank_account_type', models.CharField(blank=True, max_length=50, null=True)),
                ('archived', models.BooleanField(default=False)),
                ('txn_date', models.DateField(blank=True, null=True)),
                ('txn_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('txn_timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backendApi.subscriptions')),
            ],
        ),
    ]
