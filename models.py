# -*- coding: utf-8 -*-
import datetime
import time
from flask import url_for
from mongoengine import fields, Document
from mongoengine.queryset import QuerySet


def get_week_number(when=None):
    if not when:
        when = datetime.date.today()
    return when.isocalendar()[1]

def get_year_number(when=None):
    if not when:
        when = datetime.date.today()
    return when.isocalendar()[0]

def get_day_number(when=None):
    if not when:
        when = datetime.date.today()
    return when.isocalendar()[2]


class UserQuerySet(QuerySet):
    def total_hugs(self):
        return self.sum('hugs_received')

    def average_hugs_given(self):
        return self.filter(hugs_given__gt=0).average('hugs_given')

    def average_hugs_received(self):
        return self.filter(hugs_received__gt=0).average('hugs_received')


class User(Document):
    name = fields.StringField(unique=True, unique_with='network')
    network = fields.StringField(default='github')
    access_token = fields.StringField(required=False)
    is_admin = fields.BooleanField(default=False)
    hugs_received = fields.IntField(default=0)
    hugs_given = fields.IntField(default=0)
    avatar_url = fields.StringField(required=False)

    meta = {'queryset_class': UserQuerySet}

    def __unicode__(self):
        return self.name

    @property
    def url(self):
        return url_for('user', username=self.name, network=self.network)

    @property
    def network_url(self):
        return getattr(self, '%s_url' % self.network)

    @property
    def github_url(self):
        return 'https://github.com/%s' % self.name

    def can_hug(self):
        return self.get_today_hugged() is None

    def hug(self, receiver):
        hug = Hug.objects.create(hugger=self, hugged=receiver)
        self.hugs_given += 1
        self.save()
        receiver.hugs_received += 1
        receiver.save()
        return hug

    def get_today_hugged(self):
        try:
            return Hug.objects.get(hugger=self, week=get_week_number(), year=get_year_number(), day=get_day_number())
        except Hug.DoesNotExist:
            return None

    def get_this_week_hugged(self):
        try:
            return Hug.objects.get(hugger=self, week=get_week_number(), year=get_year_number())
        except Hug.DoesNotExist:
            return None

    def get_this_week_hugged_by(self):
        return Hug.objects.filter(hugged=self, week=get_week_number(), year=get_year_number())

    def to_dict(self, follow=False):
        data = {
            'name': self.name,
            'network': self.network,
            'hugs_received': self.hugs_received,
            'hugs_given': self.hugs_given,
            'avatar_url': self.avatar_url,
            'url': self.url,
        }
        if follow:
            data['hugs'] = [hug.to_dict(False) for hug in Hug.objects.filter(hugger=self).select_related()]
        return data


class HugQuerySet(QuerySet):
    def hugs_this_week(self):
        return self.filter(week=get_week_number(), year=get_year_number()).count()

    def hugs_last_week(self):
        last_week = datetime.date.today() - datetime.timedelta(days=7)
        return self.filter(week=get_week_number(last_week), year=get_year_number(last_week)).count()


class Hug(Document):
    hugger = fields.ReferenceField(User, unique_with=['year', 'week', 'day'])
    hugged = fields.ReferenceField(User)
    created = fields.DateTimeField(default=datetime.datetime.now)
    week = fields.IntField(default=get_week_number)
    year = fields.IntField(default=get_year_number)
    day = fields.IntField(default=get_day_number)

    meta = {'queryset_class': HugQuerySet}

    def __unicode__(self):
        return u'%s -> %s' % (self.hugger, self.hugged)

    def to_dict(self, follow=False):
        data = {
            'created': time.mktime(self.created.timetuple()),
            'week': self.week,
            'year': self.year,
        }
        if follow:
            data['hugger'] = self.hugger.to_dict()
            data['hugged'] = self.hugged.to_dict()
        else:
            data['hugger'] = self.hugger.name
            data['hugged'] = self.hugged.name
        return data
