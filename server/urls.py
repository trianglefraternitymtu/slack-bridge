from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import website.views
import slack.endpoints

urlpatterns = [
    url(r'^$', website.views.index, name='site-index'),

    url(r'^slack/auth$', slack.endpoints.auth, name='slack-auth'),
    url(r'^slack/action$', slack.endpoints.action, name='slack-action'),
    url(r'^slack/event$', slack.endpoints.event, name='slack-event')
]
