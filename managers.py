from django.db.models import Manager

class ManagerWithActive(Manager):
  def active(self):
    return self.get_query_set().filter(blog__active=True, active=True)