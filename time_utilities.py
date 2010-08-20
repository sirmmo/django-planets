from datetime import tzinfo, timedelta, datetime, date
import time

ZERO = timedelta(0)
HOUR = timedelta(hours=1)

# A UTC class.

class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

utc = UTC()


# A complete implementation of current DST rules for major US time zones.

def first_sunday_on_or_after(dt):
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        dt += timedelta(days_to_go)
    return dt

# In the US, DST starts at 2am (standard time) on the first Sunday in April.
DSTSTART = datetime(1, 4, 1, 2)
# and ends at 2am (DST time; 1am standard time) on the last Sunday of Oct.
# which is the first Sunday on or after Oct 25.
DSTEND = datetime(1, 10, 25, 1)

class USTimeZone(tzinfo):
    def __init__(self, hours, reprname, stdname, dstname):
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname

    def __repr__(self):
        return self.reprname

    def tzname(self, dt):
        if self.dst(dt):
            return self.dstname
        else:
            return self.stdname

    def utcoffset(self, dt):
        return self.stdoffset + self.dst(dt)

    def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            # An exception may be sensible here, in one or both cases.
            # It depends on how you want to treat them.  The default
            # fromutc() implementation (called by the default astimezone()
            # implementation) passes a datetime with dt.tzinfo is self.
            return ZERO
        assert dt.tzinfo is self

        # Find first Sunday in April & the last in October.
        start = first_sunday_on_or_after(DSTSTART.replace(year=dt.year))
        end = first_sunday_on_or_after(DSTEND.replace(year=dt.year))

        # Can't compare naive to aware objects, so strip the timezone from
        # dt first.
        if start <= dt.replace(tzinfo=None) < end:
            return HOUR
        else:
            return ZERO

Eastern  = USTimeZone(-5, "Eastern",  "EST", "EDT")
Central  = USTimeZone(-6, "Central",  "CST", "CDT")
Mountain = USTimeZone(-7, "Mountain", "MST", "MDT")
Pacific  = USTimeZone(-8, "Pacific",  "PST", "PDT")


def time_to_datetime(t, tzinfo=None):
    if not isinstance(t, datetime):
        year, month, day, hour, minute, second, wday, yday, isdst = t
        t = datetime(year, month, day, hour, minute, second, 0, utc)
        return t.astimezone(tzinfo)
    else:
        return t


def get_next_prev(the_date):
    now = date.today()
    if the_date.month >= 12:
        next_month = 1
        next_year = the_date.year + 1
    else:
        next_month = the_date.month + 1
        next_year = the_date.year
        
    if the_date.month <= 1:
        prev_month = 12
        prev_year = the_date.year - 1
    else:
        prev_month = the_date.month - 1
        prev_year = the_date.year
    
    if the_date.month == now.month and the_date.year == now.year:
        next_month_dt = now
    else:
        next_month_dt = date(next_year, next_month, 1)
    prev_month_dt = date(prev_year, prev_month, 1)

    return next_month_dt, prev_month_dt
    
def days_in_month(year,month):
    year = str(year)
    if isinstance(month, unicode):
       month = convert_short_month_to_int(month)
    year = int(year)
    if (month+1) >= 12:
        month = 1
        year += 1
    else:
        month += 1
    return (date(year, month+1, 1) - timedelta(days=1)).day
    
def get_now():
    now = date.today()
    current_month = now.month
    current_year = now.year
    current_day = now.day
    return now, current_year, current_month, current_day
    
def convert_short_month_to_int(month):
    if isinstance(month, unicode):
       return int(date(*time.strptime(month, '%b')[:3]).month)
