import re
from BeautifulSoup import BeautifulSoup

RELATED_TOPICS = {
    'django' : [
        'pownce',
        'everyblock',
        'holovaty',
        'ellington',
        'jellyroll',
        'appengine',
        'byteflow',
        'formwizard',
        'newforms',
        'feedclowd',
        'modelforms',
        'multipleinheritance',
        'queryset',
        'qsrf',
        
    ]
}


def clean_body(body):
    headings_start = re.compile(r'(<[h|H]\d{1}>)')
    headings_end = re.compile(r'(</?[h|H]\d{1}>)')
    divs = re.compile(r'(<[/]?div.*?>)')
    comments = re.compile(r'(<!--.*?-->)')
    body = divs.sub('', body)
    body = headings_start.sub('<p class="heading">', body)
    body = headings_end.sub('</p>', body)
    body = comments.sub('', body)
    
    # Remove junky feedburner links:  
    # Note, we don't remove all links that reference feedburner,
    #  only those which contain image elements that reference
    #  feedburner.
    
    # You cannot simply remove all links that point to feedburner
    #  because some publishers use a feature that rewrites all links
    #  in the content to proxy through FB for tracking purposes.
    if 'feedburner' in body:
        soup = BeautifulSoup(body)
        images = soup.findAll('img', src=re.compile('feedburner'))
        for i in images:
            # Remove the parent link (and by association, the image)
            i.parent.extract()
        body = unicode(soup) # Using unicode to be nice, I guess. str() 
                             #  might work just as well.
    return body.strip()
    
def clean_title(title):
    bracketed_text = re.compile(r'\[(.*?)\]')
    title = bracketed_text.sub('', title)
    return title.strip()
    
def is_about_topic(data, topic, check_related=False):
    """This function will eventually seek to 
       determine if a post is about a topic.
    
       For now the most simplistic method is
       to simply check for a string matching
       the topic in the provided data.
    
       In the future, we might maintain a table
       of strings related to a topic and look
       for those too.
       
       Additionally, we might return a confidence
       value.  As we find more blogs that mention
       the word 'django' we might want to check
       if they're more programmy than music'y,
       for example.  We'd look for terms that are
       mostly found in posts that are about
       genuine django posts.
       
       Also, we might weight stories higher that
       have a higher density of django to non-django
       keywords.
       """
    for item in data:
        if topic in item.lower():
            return True
        if check_related:
            for related_term in RELATED_TOPICS[topic]:
                if related_term in item.lower():
                    return True