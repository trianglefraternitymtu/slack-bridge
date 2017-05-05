from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import website.views

urlpatterns = [
    url(r'^$', website.views.index, name='site-index'),

    url(r'^slack/auth$', website.views.slack_auth, name='slack-auth'),
    url(r'^slack/action$', website.views.slack_action, name='slack-action'),
    url(r'^slack/event$', website.views.slack_event, name='slack-event')
]
