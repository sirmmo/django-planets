from django.conf.urls.defaults import *
from views import PlanetFeed

urlpatterns = patterns('',
    url(
        regex   = r'^$',
        view    = 'galaxy.views.post_list',
        name    = 'site_index',
    ),
    url(
        regex   = r'^.rss$',
        view    = PlanetFeed(),
        name    = 'site_index',
    ),
    url(
        regex   = r'^/page/(?P<page>\w)/$',
        view    = 'galaxy.views.post_list',
        name    = 'site_index_paginated',    
    ),
    url(
        regex   = r'^/blogs/(?P<slug>[-\w]+)/$',
        view    = 'galaxy.views.blog_detail',
        name    = 'blog_detail',
    ),
    url(
        regex   = r'^/blogs$',
        view    = 'galaxy.views.blog_list',
        name    = 'blog_list',
    ),
    url(
        regex   = r'^/blogs.opml$',
        view    = 'galaxy.views.blog_opml',
        name    = 'blog_list',
    ),
    url(
        regex   = r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$', 
        view    = 'galaxy.views.post_archive_day',
        name    = 'post_archive_day',
     ),
     url(
        regex   = r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/$',
        view    = 'galaxy.views.post_archive_month',
        name    = 'blog_archive_month',
     ),
     url(
        regex   = r'^(?P<year>\d{4})/$',
        view    = 'galaxy.views.post_archive_year',
        name    = 'blog_archive_year',
     ),
)
