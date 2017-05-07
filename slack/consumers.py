import logging

from functools import partial
from channels import Channel
from slacker import Slacker
from slacker import Error as SlackError
from website.models import Team, SharedChannel
from django.shortcuts import get_object_or_404

logger = logging.getLogger('basicLogger')

def event(message):
    logger.debug("Processing event.")

    payload = message.content
    logger.debug(payload)

    event = payload['event']
    args = {}

    local_team = get_object_or_404(Team, team_id=payload['team_id'])
    local_team_interface = Slacker(local_team.app_access_token)

    if local_team.bot_id == (event.get("bot_id") or event.get('user')):
        logger.info("Ignoring stuff done by own bot...")
        return
    elif event.get('user') == 'USLACKBOT':
        logger.info("Ignoring slackbot updates")
        return
    elif event['type'] == "message":
        user_info = local_team_interface.users.info(event['user']).body['user']

        for target in SharedChannel.objects.exclude(channel_id=event['channel'], local_team=local_team):
            slack = Slacker(target.team.app_access_token)
            slack.chat.post_message(text=event.get('text'),
                                    attachments=event.get('attachments'),
                                    channel=target.channel_id,
                                    username=user_info['profile']['real_name'],
                                    icon_url=user_info['profile']['image_192'],
                                    as_user=False
                                    )
        # Channel("background-slack-share-msg").send({
        #                                                 'event':event,
        #                                                 'target':target.id,
        #                                                 'user_info':user_info
        #                                             })

def share_msg(message):
    logger.info("Executing slack responses")
    data = message.content
    logger.debug(data)
