import logging
from django.apps import AppConfig
from slacker import Slacker
from slacker import Error as SlackError
from .models import SharedChannel

logger = logging.getLogger('basicLogger')

class WebsiteConfig(AppConfig):
    def ready(self):
        for ch in SharedChannel.objects.all():
            slack = Slacker(ch.local_team.app_access_token)

            try:
                local_channels = slack.channels.list().body['channels']
            except SlackError as e:
                logger.info('Deleting team "{}": {}'.format(ch.local_team.team_id, e))
                ch.local_team.delete()
                continue

            local_channels = [x['id'] for x in local_channels]

            if ch.channel_id not in local_channels:
                logger.info('Team {} does not have channel "{}"'.format(ch.local_team.team_id, ch.channel_id))
                ch.delete()
