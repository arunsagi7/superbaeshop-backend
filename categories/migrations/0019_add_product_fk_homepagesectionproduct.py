from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('categories', '0018_auto_20260715_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepagesectionproduct',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='homepage_sections', to='product_management.Products'),
        ),
    ]
