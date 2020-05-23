from django.contrib import admin

from .models import Movie, MovieNotFound

class MovieAdmin(admin.ModelAdmin):
    search_fields = ['title',]

admin.site.register(Movie, MovieAdmin)
admin.site.register(MovieNotFound)