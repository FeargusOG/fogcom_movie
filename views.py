from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.shortcuts import render
from .models import Movie, MovieNotFound
from .forms import MovieSearchForm
import urllib.parse
import requests
import json
import os
import time
import logging
import cloudinary
import cloudinary.uploader
import cloudinary.api
import traceback

# Minimum number of IMDB votes to have - otherwise we get stuff that is too niche.
IMDB_VOTE_COUNT_MINIMUM = 5000
# Minimum 'The Movie DB' rating - this simply decides what movies to look for in IMDB.
TMDB_MIN_RATING = '6.5'
# Game list template page
MOVIELIST_TEMPLATE = 'movie_fortune/movie_list.html'
# Context object name for game list - used in the HTML.
MOVIELIST_CON = 'movie_list'
# Stand-Up Comedian List
STANDUP_COMEDIANS = ["Dave Chappelle", "Trevor Noah", "Ali Wong", "Bo Burnham", "Hasan Minhaj", "Louis C.K.", "Kevin Hart", "Eddie Murphy", "Jeff Dunham", "Aziz Ansari", "Hannah Gadsby", "John Mulaney", "Ricky Gervais", "Adam Sandler", "Gad Elmaleh", "Chris Rock", "Sarah Silverman", "Bill Burr", "Jim Jefferies", "Jimmy Carr", "Chelsea Peretti", "George Carlin", "Jerry Seinfeld", "Richard Pryor"]

FILTER_INCLUDE = 1
FILTER_EXCLUDE = 2
FILTER_EXCUSIVE = 3

# Get an instance of a logger
logger = logging.getLogger(__name__)

def get_search_form(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = MovieSearchForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # redirect to a new URL:
            return HttpResponseRedirect('results/{0}/{1}/{2}/{3}/{4}/{5}'.format(form.cleaned_data['lang'], form.cleaned_data['rating'], form.cleaned_data['start'], form.cleaned_data['end'], form.cleaned_data['doc'], form.cleaned_data['sup']))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = MovieSearchForm()

    return render(request, 'movie_fortune/movie_params.html', {'form': form})

class MovieListView(generic.ListView):
    template_name = MOVIELIST_TEMPLATE
    context_object_name = MOVIELIST_CON

    def __init__(self):
        self.lang = ""
        self.rating = 0
        self.start_year = ""
        self.end_year = ""
        self.documentary_filter = 0
        self.standup_filter = 0

    def get_queryset(self):
        movie_list = []
        page = 1
        min_vote_count = self.get_min_vote_count()
        min_rating = self.get_min_tmdb_rating()

        self.set_lang(self.kwargs['lang'])
        self.set_min_rating(self.kwargs['rating'])
        self.set_start_year(self.kwargs['start'])
        self.set_end_year(self.kwargs['end'])
        self.set_documentary_filter(int(self.kwargs['doc']))
        self.set_standup_filter(int(self.kwargs['sup']))
        print(self.get_documentary_filter())
        print(self.get_standup_filter())

        try:
            # Process the first page
            response_json = self.request_movie_list_json(page, self.get_start_date(), self.get_end_date(), min_vote_count, min_rating, self.get_lang())
            self.process_movie_list_json(movie_list, response_json)

            # Process any additional pages
            for i in range(1, self.get_number_of_pages(response_json)):
                page += 1
                response_json = self.request_movie_list_json(page, self.get_start_date(), self.get_end_date(), min_vote_count, min_rating, self.get_lang())
                self.process_movie_list_json(movie_list, response_json)

            movie_list.sort(key=lambda x: x.get_imdb_rating(), reverse=True)
            for movie in movie_list:
                logger.info(movie)

        except Exception as e:
            logger.error(traceback.format_exc())

        return movie_list

    def process_movie_list_json(self, movie_list, response_json):
        for movie_json in response_json["results"]:
            movie = self.get_movie_from_cache(movie_json["id"])
            if movie and not movie.needs_update():
                logger.info("Movie in cache is fresh: " + movie.get_title())
                if "tmdb" in movie.get_poster_path():
                    self.update_poster_path(movie, self.upload_thumb_to_cloudinary(movie_json["poster_path"]))
            elif self.is_movie_not_found(movie_json["id"]):
                logger.info("Movie is not found in OMDB: " + movie_json["title"])
                #self.set_movie_not_found_scores(movie_json["id"], movie_json["popularity"], movie_json["vote_average"])
                continue
            else:
                title = movie_json["title"]

                if not movie:
                    logger.info("Movie not found in cache: " + title)
                elif movie.needs_update():
                    logger.info("Movie in cache is stale: " + title)

                id = movie_json["id"]
                release_date = movie_json["release_date"]
                poster_path = self.get_image_url(movie_json["poster_path"])
                overview = movie_json["overview"]

                response_json = self.request_movie_details_json(title)

                if response_json["Response"] == "True":
                    # Skip if there is no IMDB rating.
                    if response_json["imdbRating"] == "N/A":
                        continue

                    # Skip if there are no IMDB votes.
                    if response_json["imdbVotes"] == "N/A":
                        continue
                    
                    # Set the core movie details
                    imdb_votes = int(response_json["imdbVotes"].replace(",", ""))
                    imdb_rating = float(response_json["imdbRating"])
                    imdb_id = response_json["imdbID"]
                    certification = response_json["Rated"]
                    runtime = response_json["Runtime"]
                    genre = response_json["Genre"]
                    language = response_json["Language"]
                    is_documentary = False
                    is_standup = False

                    if "Documentary" in genre:
                        is_documentary = True

                    if any(substring in title for substring in STANDUP_COMEDIANS):
                        is_standup = True

                    # Set the optional scores
                    metascore = -1
                    rt_rating = -1
                    
                    if response_json["Metascore"] != "N/A":
                        metascore = int(response_json["Metascore"])

                    for rating in response_json["Ratings"]:
                        if rating["Source"] == "Rotten Tomatoes":
                            rt_rating = int(response_json["Ratings"][1]["Value"].replace("%", ""))

                    # Add the movie to the cache, even if it doesn't meet the search requirements below
                    movie = self.set_movie_in_cache(id, title, language, release_date, poster_path, overview, imdb_rating, imdb_votes, imdb_id, metascore, rt_rating, certification, runtime, genre, is_documentary, is_standup)
                else:
                    logger.warning("No OMDB response for: " + title)
                    self.set_movie_not_found(id, title, movie_json["original_language"], release_date, poster_path, overview, "", movie_json["popularity"], movie_json["vote_average"])
                    continue

            # Check filters:
            # If docs are excluded and this is a doc
            if self.get_documentary_filter() == FILTER_EXCLUDE and movie.get_is_documentary():
                continue
            
            # If docs are wanted exclusively and this is not a doc
            if self.get_documentary_filter() == FILTER_EXCUSIVE and not movie.get_is_documentary():
                continue

            # If stand-ups are excluded and this is a stand-up
            if self.get_standup_filter() == FILTER_EXCLUDE and movie.get_is_standup():
                continue
            
            # If stand-ups are wanted exclusively and this is not a stand-up
            if self.get_standup_filter() == FILTER_EXCUSIVE and not movie.get_is_standup():
                continue

            # Add to list if the votes and any of the ratings are high enough.
            if movie.get_imdb_votes() >= IMDB_VOTE_COUNT_MINIMUM:
                if movie.get_imdb_rating() >= (self.get_min_rating() / 10.0):
                    movie_list.append(movie)
                elif movie.get_rt_rating() >= self.get_min_rating():
                    movie_list.append(movie)
                elif movie.get_metascore() >= self.get_min_rating():
                    movie_list.append(movie)


    ###
    # Cloudinary Calls
    ###
    def upload_thumb_to_cloudinary(self, thumbnail_url):
        """
        Upload a thumbnail to the cloudinary datastore.
        Args:
            thumbnail_url: The url of the thumbnail to upload to cloudinary.
        Returns:
            string: Return the url of the image now stored in cloudinary.
        """
        upload_result = cloudinary.uploader.upload(thumbnail_url)
        return upload_result['url']
    
    ###
    # Postgres Calls
    ###
    def update_poster_path(self, movie, poster_path):
        """
        Update a the movie's poster path in the DB.
        Args:
            movie: The Movie object with the path to udpate.
            poster_path: The new poster path.
        """
        movie.poster_path = poster_path
        movie.save()

    def get_movie_from_cache(self, id):
        movie = None
        try:
            movie = Movie.objects.get(id=id)
        except Movie.DoesNotExist:
            pass
        return movie

    def set_movie_in_cache(self, id, title, language, release_date, poster_path, overview, imdb_rating, imdb_votes, imdb_id, metascore, rt_rating, certification, runtime, genre, is_documentary, is_standup):
        movie, created = Movie.objects.update_or_create(id=id, title=title, language=language, release_date=release_date, poster_path=poster_path, overview=overview, imdb_rating=imdb_rating, imdb_votes=imdb_votes, imdb_id=imdb_id, metascore=metascore, rt_rating=rt_rating, certification=certification, runtime=runtime, genre=genre, documentary=is_documentary, standup=is_standup)
        return movie

    def set_movie_not_found(self, id, title, language, release_date, poster_path, overview, imdb_id, tmdb_popularity, tmdb_rating):
        movie_not_found_record, created = MovieNotFound.objects.update_or_create(id=id, title=title, language=language, release_date=release_date, poster_path=poster_path, overview=overview, imdb_id=imdb_id, tmdb_popularity=tmdb_popularity, tmdb_rating=tmdb_rating)
        return movie_not_found_record

    def is_movie_not_found(self, id):
        movie_not_found = None
        try:
            movie_not_found = MovieNotFound.objects.get(id=id)
        except MovieNotFound.DoesNotExist:
            pass
        return movie_not_found

    def set_movie_not_found_scores(self, id, tmdb_popularity, tmdb_rating):
        movie_not_found = None
        try:
            movie_not_found = MovieNotFound.objects.get(id=id)
            movie_not_found.tmdb_popularity = tmdb_popularity
            movie_not_found.tmdb_rating = tmdb_rating
            movie_not_found.save()
        except MovieNotFound.DoesNotExist:
            pass

    ###
    # The OMDB Api Calls
    ###
    def get_movie_detail_title_search_url(self, title):
        url = "http://www.omdbapi.com"
        params = {'apiKey':self.get_omdb_api_key(), 't':title}
        url_parts = list(urllib.parse.urlparse(url))
        url_parts[4] = urllib.parse.urlencode(params)
        return urllib.parse.urlunparse(url_parts)

    def request_movie_details_json(self, title):
        url = self.get_movie_detail_title_search_url(title)
        logger.info(url)
        response = requests.get(url)
        if response.status_code == 401:
            raise RuntimeError('OMDB Request limit reached!')
        return response.json()

    ###
    # The Movie DB Api Calls
    ###
    def get_movie_list_url(self, page_num, start_date, end_date, min_vote_count, min_rating, lang):
        url = "http://api.themoviedb.org/3/discover/movie"
        params = {'api_key':self.get_moviedb_api_key(), 'sort_by':'vote_average.desc', 'page':str(page_num), 'primary_release_date.gte':start_date, 'primary_release_date.lte':end_date, 'vote_count.gte':min_vote_count, 'vote_average.gte':min_rating, 'with_original_language':lang}
        url_parts = list(urllib.parse.urlparse(url))
        url_parts[4] = urllib.parse.urlencode(params)
        return urllib.parse.urlunparse(url_parts)

    def request_movie_list_json(self, page, start_date, end_date, min_vote_count, min_rating, lang):
        url = self.get_movie_list_url(page, start_date, end_date, min_vote_count, min_rating, lang)
        logger.info(url)
        response = requests.get(url)
        return response.json()

    ###
    # Helper Functions
    ###    
    def get_image_url(self, poster_path):
        if poster_path:
            return "https://image.tmdb.org/t/p/w200"+poster_path
        else:
            return ""

    def get_number_of_pages(self, response_json):
        return int(response_json["total_pages"])

    def set_start_year(self, start_year):
        self.start_year = start_year

    def get_start_date(self):
        return self.start_year + '-01-01'

    def set_end_year(self, end_year):
        self.end_year = end_year

    def get_end_date(self):
        return self.end_year + '-12-31'

    def get_min_vote_count(self):
        return '50'

    def get_min_tmdb_rating(self):
        return TMDB_MIN_RATING

    def set_documentary_filter(self, doc):
        self.documentary_filter = doc

    def get_documentary_filter(self):
        return self.documentary_filter

    def set_standup_filter(self, sup):
        self.standup_filter = sup

    def get_standup_filter(self):
        return self.standup_filter

    def set_lang(self, lang):
        self.lang = lang

    def get_lang(self):
        return self.lang

    def set_min_rating(self, rating):
        self.rating = int(rating)
    
    def get_min_rating(self):
        return self.rating

    def get_moviedb_api_key(self):
        return os.environ['MOVIEDB_API_KEY']

    def get_omdb_api_key(self):
        return os.environ['OMDB_API_KEY']
