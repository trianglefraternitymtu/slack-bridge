import logging

from channels import Channel
from slacker import Slacker
from slacker import Error as SlackError
from website.models import Team
from django.shortcuts import get_object_or_404

logger = logging.getLogger('basicLogger')

def event(message):
    logger.debug("Processing event.")

    payload = message.content
    logger.debug(payload)

    event = payload['event']

    local_team = get_object_or_404(Team, team_id=payload['team_id'])
    local_team_interface = Slacker(local_team.app_access_token)

    if local_team.bot_id == event['user']:
        logger.info("Ignoring stuff done by own bot...")
        return
    elif event['type'] == "message":
        user_info = local_team_interface.users.info(event['user']).body['user']
        for target in Team.objects.all():#.exclude(team_id=payload['team_id']):
            slack = Slacker(target.app_access_token)
            logger.debug(target)

            func = slack.chat.post_message

            args = {
                "text":event.get('text'),
                "attachments":event.get('attachments'),
                "channel":event['channel'],
                "username":user_info['profile']['real_name'],
                "icon_url":user_info['profile']['image_192'],
                "as_user":False
            }

            Channel("background-slack-share-msg").send({'func':func, 'args':args})

def share_msg(message):
    payload = message.content
    payload['func'](**payload['args'])
