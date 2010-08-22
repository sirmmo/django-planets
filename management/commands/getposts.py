from django.core.management.base import BaseCommand, CommandError
from galaxy.models import *

import settings
class Command(BaseCommand):
	args = ''
	help = 'Closes the specified poll for voting'

	def handle(self, *args, **options):
		parser = OptionParser()
		parser.add_option('-f', '--firstrun', dest='firstrun', default=False, action='store_true', help="Use this for your first run")

		(options, args) = parser.parse_args()
		
		do_get(options.firstrun)



import sys
import os
import pprint
import datetime
import feedparser
from optparse import OptionParser
from django.template.defaultfilters import slugify
from galaxy.utilities import clean_body, clean_title

VERSION = '0.1'
URL = 'http://www.djangogalaxy.com/'
USER_AGENT = 'Galaxy %s - %s' % (VERSION, URL)
TESTING = False

def do_get(first_run=False):
    from galaxy.models import Blog, Post

    from galaxy.time_utilities import Central, time_to_datetime
    from django.conf import settings

    # Delete all posts, for debugging only
    
    if TESTING or first_run:
        print('**** TESTING MODE ****')
        print('Clearing out all posts from DB') 
        [p.delete() for p in Post.objects.all()]
        print('Activating all blogs')
        all_blogs = Blog.objects.all()
        for b in all_blogs: 
            b.active = True
            b.save()

    blogs = Blog.objects.filter(active__exact=True)
    print('%s feeds to check' % (len(blogs)))

    for blog in blogs:
        print('Checking "%s"' % (blog.name,))
        if TESTING:
            print('Clearing ETAG')
            blog.etag = None
        
        if blog.feed:
            rss_location = blog.feed
        else: continue
        
        try:
            d = feedparser.parse(rss_location, agent=USER_AGENT, \
                etag=blog.etag)
        except:
            print('Could not process feed')
            continue
        if hasattr(d, 'status'):
            print('feed status: %s' % d.status)
            if d.status == 304:
                print('Feed has not changed since our last attempt.')
                continue
            if d.status >= 400:
                print('HTTP error while trying to grab the feed.')
                continue
        if hasattr(d, 'bozo') and d.bozo:
            print('Bozo flag was set.')

        blog.etag = d.get('etag', '')
        if blog.etag is None:
            blog.etag = ''
        num_with_tags = 0
        for entry in d.entries:
            # Do some digging to find a valid time
            #date_posted = entry.get('modified_parsed', d.get('modified_parsed', d.get('modified', None)))
            appropriate_post = False
            created = False
            active = True
            guid = entry.get('guid', entry.get('link', None))
            
            try:
                existing_post = Post.objects.get(guid__iexact=guid)
                print('skipping, already seen this one')
                continue
            except Post.DoesNotExist:
                print('Post does not already exist in DB')
                pass
            
            date_posted = entry.get('modified_parsed', None)
            if date_posted:
                date_posted = time_to_datetime(date_posted, Central)
            else:
                print('Blog "%s" has bad dates' % (blog.name,))
                blog.bad_dates = True
                date_posted = datetime.datetime.now(Central)
            title = entry.get('title', None)
            body = entry.get('summary', None)
            if not body:
                body = entry.content[0].get('value', '')
            if body != '':
                body = clean_body(body)
            if title == body:
                body = '' 
            if title != '':
                title = clean_title(title)
            link = entry.get('feedburner_origlink', entry.get('link', None))
            title = title.encode('ascii', 'xmlcharrefreplace')
            if body:
                body = body.encode('ascii', 'xmlcharrefreplace')
            author = None 
            author = entry.get('author_detail', None)
            if not author:
                author = entry.get('author', None)
            else:
                author = author.get('name', None)
            if author:
                author = author.encode('ascii', 'xmlcharrefreplace')
            else:
                author = ''
            
            # Process tags if they exist
            tags = entry.get('tags', '')
            if tags != '':
                num_with_tags += 1
                tags = ' '.join([tag.term.lower() for tag in tags])
                print('Found tags: %s' % (tags,))
            
  
            appropriate_post = True

            if appropriate_post or blog.override:
                print('Post looks good, creating')
                
                if first_run:
                    active = not blog.bad_dates            
                post, created = Post.objects.get_or_create(
                    guid__iexact=guid, 
                    defaults = {
                        'blog'  : blog,
                        'title' : title,
                        'slug'  : slugify(title[:50]),
                        'body'  : body,
                        'link'  : link,
                        'guid'  : guid,
                        'author': author,
                        'posted': date_posted.replace(tzinfo=None),
                        'tags'  : tags,
                        'active': not blog.bad_dates
                    }
                )
            else:
                print('Post not worthy. Skipping.')
                
            if created:
                print("Creating the following post in the DB:")
                print("Blog name  : %s" % blog.name.encode('ascii', 'xmlcharrefreplace'))
                print("Post title : %s" % title)
                print("Post slug  : %s" % slugify(title[:50]))
                print("Post author: %s" % author)
                print("Post body  : %s chars" % len(body))
                print("Post link  : %s" % link)
                print("Post GUID  : %s" % guid)
                print("Post tags  : %s" % tags)
                print("Post posted: %s" % date_posted)
                print("Feed ver.  : %s" % d.version)
                print("-"*50)
        
        if num_with_tags == 0:
            print('Blog "%s" has no tags' % (blog.name,))
            blog.bad_tags = True
        else:
            blog.bad_tags = False
        blog.save()
        