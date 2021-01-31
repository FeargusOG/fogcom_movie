from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'', views.get_mft, name=''),
    url(r'search', views.get_search_form, name='search'),
    url(r'^results/(?P<lang>[\w-]+)/(?P<rating>[0-9]+)/(?P<start>[0-9]+)/(?P<end>[0-9]+)/(?P<doc>[0-9]+)/(?P<sup>[0-9]+)/$', views.MovieListView.as_view(), name='results'),
]
