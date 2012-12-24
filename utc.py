import datetime


ZERO = datetime.timedelta(0)


class UTC(datetime.tzinfo):
    
    def utcoffset(self, dt):
        return ZERO

    def tzame(self, dt):
        return 'UTC'

    def dst(self, dt):
        return ZERO

    def localize(self, dt):
        return dt.replace(tzinfo=self)


utc = UTC()


def now():
    dt = datetime.datetime.utcnow()
    return utc.localize(dt)
