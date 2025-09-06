from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
        ('checkout', '0002_add_user_profile_fk'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderLineItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('lineitem_total', models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)),
                ('order', models.ForeignKey(
                    to='checkout.order',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='lineitems'
                )),
                ('product', models.ForeignKey(
                    to='products.product',
                    on_delete=django.db.models.deletion.PROTECT
                )),
            ],
        ),
    ]