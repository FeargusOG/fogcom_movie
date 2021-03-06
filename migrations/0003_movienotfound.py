# Generated by Django 2.1.7 on 2020-03-24 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movie_fortune', '0002_movie_language'),
    ]

    operations = [
        migrations.CreateModel(
            name='MovieNotFound',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('title', models.TextField()),
                ('language', models.TextField()),
                ('release_date', models.TextField()),
                ('poster_path', models.TextField()),
                ('overview', models.TextField()),
                ('imdb_id', models.TextField(default='')),
            ],
        ),
    ]
