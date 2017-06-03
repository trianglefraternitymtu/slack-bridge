from django.conf.urls import url
import website.views
import slack.endpoints
import slack.commands
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'^$', website.views.index, name='site-index'),

    url(r'^slack/auth$', slack.endpoints.auth, name='slack-auth'),
    url(r'^slack/action$', slack.endpoints.action, name='slack-action'),
    url(r'^slack/event$', slack.endpoints.event, name='slack-event'),

    url(r'^slack/commands/list-members$', slack.commands.list_members, name='slack-command-list_members')
]
