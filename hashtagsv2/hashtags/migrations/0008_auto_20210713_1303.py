# Generated by Django 2.2 on 2021-07-13 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hashtags', '0007_hashtag_has_audio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hashtag',
            name='hashtag',
            field=models.CharField(db_index=True, max_length=128),
        ),
    ]
