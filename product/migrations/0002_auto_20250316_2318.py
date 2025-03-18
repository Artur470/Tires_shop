from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='new_field',
            field=models.CharField(max_length=100, default='default_value'),
        ),
    ]
