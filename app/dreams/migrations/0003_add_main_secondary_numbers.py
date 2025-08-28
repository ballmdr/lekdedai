# Generated migration for DreamKeyword model updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dreams', '0002_remove_dreaminterpretation_dream_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='dreamkeyword',
            name='main_number',
            field=models.CharField(default='0', help_text='เลขหลักเดียว 0-9', max_length=1, verbose_name='เลขเด่น'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dreamkeyword',
            name='secondary_number',
            field=models.CharField(default='0', help_text='เลขหลักเดียว 0-9', max_length=1, verbose_name='เลขรอง'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dreamkeyword',
            name='common_numbers',
            field=models.CharField(default='', help_text='ใส่เลขคั่นด้วยเครื่องหมายจุลภาค เช่น 12,34,56', max_length=100, verbose_name='เลขที่มักตี'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='dreamkeyword',
            name='numbers',
            field=models.CharField(blank=True, help_text='จะถูกสร้างอัตโนมัติจาก common_numbers', max_length=100, verbose_name='เลขที่เกี่ยวข้อง'),
        ),
    ]