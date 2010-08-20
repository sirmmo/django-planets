from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404
from django.views.generic import date_based, list_detail
from galaxy.models import *

def post_list(request, page=0, planet=""):
    """
    Post list

    Template: ``galaxy/post_list.html``
    Context:
      object_list
          list of objects
      is_paginated
          are the results paginated?
      results_per_page
          number of objects per page (if paginated)
      has_next
          is there a next page?
      has_previous
          is there a prev page?
      page
          the current page
      next
          the next page
      previous
          the previous page
      pages
          number of pages, total
      hits
          number of objects, total
      last_on_page
          the result number of the last of object in the
          object_list (1-indexed)
      first_on_page
          the result number of the first object in the
          object_list (1-indexed)
      page_range:
          A list of the page numbers (1-indexed).
    """
    return list_detail.object_list(
        request,
        queryset = Post.objects.active(),
        paginate_by = 20,
        page = page,
    )
  
def blog_list(request,planet=""):
    """
    Blog list

    Template: ``galaxy/blog_list.html``
    Context:
      object_list
        List of blogs in the galaxy.
    """
    return list_detail.object_list(
        request,
        queryset = Blog.objects.filter(active=True),
        template_name = 'galaxy/blog_list.html',
    )
  
def blog_detail(request, slug,planet=""):
    """
    Blog detail

    Template: ``galaxy/blog_detail.html``
    Context:
      object_list
        List of posts specific to the given blog.
      blog
        Given blog.
    """
    try:
        blog = Blog.objects.get(slug__iexact=slug)
    except Blog.DoesNotExist:
        raise Http404

    return list_detail.object_list(
        request,
        queryset = blog.post_set.active(),
        extra_context = { 'blog': blog, },
        template_name = 'galaxy/blog_detail.html',
    )

def post_archive_year(request, year,planet=""):
    """
    Post archive year

    Templates: ``galaxy/post_archive_year.html``
    Context:
    date_list
      List of months in this year with objects
    year
      This year
    object_list
      List of objects published in the given month
      (Only available if make_object_list argument is True)
    """
    return date_based.archive_year(
        request,
        year = year,
        date_field = 'posted',
        queryset = Post.objects.active(),
        make_object_list = True,
    )

def post_archive_month(request, year, month,planet=""):
    """
    Post archive month

    Templates: ``galaxy/post_archive_month.html``
    Context:
    month:
      (date) this month
    next_month:
      (date) the first day of the next month, or None if the next month is in the future
    previous_month:
      (date) the first day of the previous month
    object_list:
      list of objects published in the given month
    """
    return date_based.archive_month(
        request,
        year = year,
        month = month,
        date_field = 'posted',
        queryset = Post.objects.active(),
    )

def post_archive_day(request, year, month, day,planet=""):
    """
    Post archive day

    Templates: ``galaxy/post_archive_day.html``
    Context:
    object_list:
      list of objects published that day
    day:
      (datetime) the day
    previous_day
      (datetime) the previous day
    next_day
      (datetime) the next day, or None if the current day is today
    """
    return date_based.archive_day(
        request,
        year = year,
        month = month,
        day = day,
        date_field = 'posted',
        queryset = Post.objects.active(),
    )