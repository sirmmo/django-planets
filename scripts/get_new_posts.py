#!/usr/bin/env python
# encoding: utf-8
import sys
import os
import pprint
import datetime
import feedparser
from optparse import OptionParser
from django.template.defaultfilters import slugify
from galaxy.utilities import clean_body, clean_title, is_about_topic

VERSION = '0.1'
URL = 'http://www.djangogalaxy.com/'
USER_AGENT = 'Galaxy %s - %s' % (VERSION, URL)
TESTING = True
TOPIC = 'django'

def main(first_run=False):
    from galaxy.models import Blog, Post
    from galaxy.debugging import logging
    from galaxy.time_utilities import Central, time_to_datetime
    from django.conf import settings

    # Delete all posts, for debugging only
    
    if TESTING or first_run:
        logging.info('**** TESTING MODE ****')
        logging.info('Clearing out all posts from DB') 
        [p.delete() for p in Post.objects.all()]
        logging.info('Activating all blogs')
        all_blogs = Blog.objects.all()
        for b in all_blogs: 
            b.active = True
            b.save()

    blogs = Blog.objects.filter(active__exact=True)
    logging.info('%s feeds to check' % (len(blogs)))

    for blog in blogs:
        logging.info('Checking "%s"' % (blog.name,))
        if TESTING:
            logging.info('Clearing ETAG')
            blog.etag = None
        
        if blog.feed:
            rss_location = blog.feed
        else: continue
        
        try:
            d = feedparser.parse(rss_location, agent=USER_AGENT, \
                etag=blog.etag)
        except:
            logging.error('Could not process feed')
            continue
        if hasattr(d, 'status'):
            logging.info('feed status: %s' % d.status)
            if d.status == 304:
                logging.info('Feed has not changed since our last attempt.')
                continue
            if d.status >= 400:
                logging.error('HTTP error while trying to grab the feed.')
                continue
        if hasattr(d, 'bozo') and d.bozo:
            logging.warning('Bozo flag was set.')

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
                logging.info('skipping, already seen this one')
                continue
            except Post.DoesNotExist:
                logging.info('Post does not already exist in DB')
                pass
            
            date_posted = entry.get('modified_parsed', None)
            if date_posted:
                date_posted = time_to_datetime(date_posted, Central)
            else:
                logging.warning('Blog "%s" has bad dates' % (blog.name,))
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
                logging.info('Found tags: %s' % (tags,))
            
            logging.info('Checking for on-topic-ness')
            if is_about_topic([title,body,tags], TOPIC, check_related=True):
                logging.info('This post is about Django')
                appropriate_post = True

            if appropriate_post or blog.override:
                logging.info('Post looks good, creating')
                
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
                logging.info('Post not worthy. Skipping.')
                
            if created:
                logging.info("Creating the following post in the DB:")
                logging.info("Blog name  : %s" % blog.name.encode('ascii', 'xmlcharrefreplace'))
                logging.info("Post title : %s" % title)
                logging.info("Post slug  : %s" % slugify(title[:50]))
                logging.info("Post author: %s" % author)
                logging.info("Post body  : %s chars" % len(body))
                logging.info("Post link  : %s" % link)
                logging.info("Post GUID  : %s" % guid)
                logging.info("Post tags  : %s" % tags)
                logging.info("Post posted: %s" % date_posted)
                logging.info("Feed ver.  : %s" % d.version)
                logging.info("-"*50)
        
        if num_with_tags == 0:
            logging.warning('Blog "%s" has no tags' % (blog.name,))
            blog.bad_tags = True
        else:
            blog.bad_tags = False
        blog.save()
        
if __name__ == '__main__':
    usage = "usage: %prog -s SETTINGS | --settings=SETTINGS"
    parser = OptionParser(usage)
    parser.add_option('-s', '--settings', dest='settings', metavar='SETTINGS',
                      help="The Django settings module to use")
    parser.add_option('-f', '--firstrun', dest='firstrun', default=False,
                        action='store_true', help="Use this for your first run")

    (options, args) = parser.parse_args()

    if not options.settings:
        # default to local settings
        options.settings = 'djangodaily.settings'
        #parser.error("You must specify a settings module")

    os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
    main(first_run=options.firstrun)