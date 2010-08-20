from django.db import models
from tagging.fields import TagField
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink
import datetime
from galaxy.debugging import *
from django.template.defaultfilters import slugify
import feedparser, feedfinder
from galaxy.managers import *

class Blog(models.Model):
    """A blog or blog-like website run by an individual or corporation"""
    name        = models.CharField(_('name'), blank=True, max_length=255)
    slug        = models.SlugField(_('slug'), prepopulate_from=("name",), blank=True)
    link        = models.URLField(blank=True, verify_exists=False)
    feed        = models.URLField(_('feed'), verify_exists=False, blank=True)
    owner       = models.CharField(_('owner'), blank=True, max_length=100)
    active      = models.BooleanField(_('active'), default=True)
    bad_dates   = models.BooleanField(_('bad dates'), default=False)
    bad_tags    = models.BooleanField(_('no tags'), default=False)
    override    = models.BooleanField(_('override bad'), default=False)
    etag        = models.CharField(_('etag'), blank=True, max_length=50)
    
    class Meta:
        verbose_name        = _('blog')
        verbose_name_plural = _('blogs')
        ordering            = ('name',)

    class Admin:
        list_display    = (
            'name',
            'owner',
            'etag',
            'active',
            'bad_dates',
            'bad_tags',
            'override',
        )
        search_fields   = ('name', 'owner', 'feed',)

    def save(self):
        if self.feed == '' or self.link == '' or self.name == '':
            if self.feed:
                logging.info('Feed was specified')
                feed_location = self.feed
            elif self.link:
                logging.info('Link to site was specified')
                feed_location = feedfinder.feed(self.link)
            else:
                logging.info('Nothing useful was specified')
        
            if feed_location:
                logging.info('Parsing feed')
                try:
                    d = feedparser.parse(feed_location)
                except:
                    logging.error('Could not process feed')
                    return
                feed_title = d.feed.title
                feed_link = d.feed.link
                logging.info('Feed has %s entries' % (len(d.entries)))
                # Update as many blank fields from feed
                if self.name == '': 
                    logging.info('Updating blog title')
                    self.name = feed_title
                if self.feed == '': 
                    logging.info('Updating blog feed')
                    self.feed = feed_location            
                logging.info('Updating blog link')
                self.link = feed_link
                owner = None 
                owner = d.entries[0].get('author_detail', None)
                if not owner:
                    owner = d.entries[0].get('author', None)
                else:
                    owner = owner.name
                if owner:
                    self.owner = owner
            
            if self.slug == '':
                self.slug = slugify(self.name[:50])
        # Call real save function
        logging.info('Saving blog instance')
        super(Blog,self).save()

    @permalink
    def get_absolute_url(self):
        return ('blog_detail', None, { 'slug':self.slug })

    def __unicode__(self):
        return u"%s" % (self.name,)
        
class Post(models.Model):
    """A post or article from a blog"""
    blog    = models.ForeignKey(Blog)
    title   = models.CharField(_('title'), blank=True, max_length=255)
    slug    = models.SlugField(_('slug'), prepopulate_from=("title",))
    link    = models.URLField(_('link'), blank=True, verify_exists=False)
    body    = models.TextField(_('body'), blank=True)
    posted  = models.DateTimeField(_('posted'), blank=True, default=datetime.datetime.now)
    guid    = models.CharField(_('guid'), blank=True, max_length=255)
    author  = models.CharField(_('author'), blank=True, max_length=255)
    active  = models.BooleanField(default=True)
    tags    = TagField()
    objects = ManagerWithActive()
    
    class Meta:
        verbose_name        = _('post')
        verbose_name_plural = _('posts')
        ordering            = ('-posted',)
        get_latest_by       = 'posted'

    class Admin:
        list_display    = ('title', 'author', 'blog', 'posted', 'active')
        list_filter     = ('blog', 'posted','tags')
        search_fields   = ('blog', 'title', 'body', 'tags')

    def __unicode__(self):
        return u"%s" % (self.title,)

    def get_absolute_url(self):
        return self.link
		
class Planet(models.Model):
	"""A planet with a given set of blogs"""
	name = models.CharField(_('name'), blank=True, max_length=255)
	blogs = models.ManyToManyField(Blog, related_name="planets")
	
	def __unicode__(self):
		return u"%s" % (self.name,)
	