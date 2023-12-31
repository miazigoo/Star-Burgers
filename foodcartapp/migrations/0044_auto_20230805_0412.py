# Generated by Django 3.2.15 on 2023-08-05 01:12

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, verbose_name='Комментарий к заказу'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='price',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10, validators=[django.core.validators.MinValueValidator(limit_value=0)], verbose_name='Сумма'),
            preserve_default=False,
        ),
    ]
