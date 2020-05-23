import datetime

from django.db import models
from django.utils import timezone

class Movie(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    title = models.TextField()
    language = models.TextField()
    release_date = models.TextField()
    poster_path = models.TextField()
    overview = models.TextField()
    imdb_rating = models.FloatField(default=0.0)
    imdb_votes = models.IntegerField(default=0)
    imdb_id = models.TextField()
    metascore = models.IntegerField(default=0)
    rt_rating = models.IntegerField(default=0)
    certification = models.TextField()
    runtime = models.TextField()
    genre = models.TextField()
    documentary = models.BooleanField(default=False)
    standup = models.BooleanField(default=False)
    last_updated = models.DateTimeField(default=timezone.now)

    def get_id(self):
        return self.id
    
    def get_title(self):
        return self.title

    def get_language(self):
        return self.language

    def get_imdb_rating(self):
        return self.imdb_rating

    def get_release_date(self):
        return self.release_date

    def get_poster_path(self):
        return self.poster_path

    def get_overview(self):
        return self.overview

    def get_imdb_votes(self):
        return self.imdb_votes

    def get_imdb_id(self):
        return self.imdb_id

    def get_metascore(self):
        return self.metascore
    
    def get_rt_rating(self):
        return self.rt_rating

    def get_certification(self):
        return self.certification

    def get_runtime(self):
        return self.runtime

    def get_genre(self):
        return self.genre

    def get_is_documentary(self):
        return self.documentary

    def get_is_standup(self):
        return self.standup

    def get_last_updates(self):
        return self.last_updated
    
    def __str__(self):
        return self.title

    def needs_update(self):
        return self.last_updated < (timezone.now() - datetime.timedelta(days=150))

class MovieNotFound(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    title = models.TextField()
    language = models.TextField()
    release_date = models.TextField()
    poster_path = models.TextField()
    overview = models.TextField()
    imdb_id = models.TextField(default="")
    tmdb_popularity = models.FloatField(default=-1.0)
    tmdb_rating = models.FloatField(default=-1.0)

    def get_id(self):
        return self.id

    def get_title(self):
        return self.title

    def get_language(self):
        return self.language

    def get_release_date(self):
        return self.release_date

    def get_poster_path(self):
        return self.poster_path

    def get_overview(self):
        return self.overview

    def get_imdb_id(self):
        return self.imdb_id

    def get_tmdb_popularity(self):
        return self.tmdb_popularity

    def get_tmdb_rating(self):
        return self.tmdb_rating
    
    def __str__(self):
        return self.title