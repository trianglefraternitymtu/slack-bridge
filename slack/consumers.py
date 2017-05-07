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
    args = {}

    local_team = get_object_or_404(Team, team_id=payload['team_id'])
    local_team_interface = Slacker(local_team.app_access_token)

    if local_team.bot_id == event['user']:
        logger.info("Ignoring stuff done by own bot...")
        return
    elif event['type'] == "message":
        user_info = local_team_interface.users.info(event['user']).body['user']

        args = {
            "text":event.get('text'),
            "attachments":event.get('attachments'),
            "channel":event['channel'],
            "username":user_info['profile']['real_name'],
            "icon_url":user_info['profile']['image_192'],
            "as_user":False
        }

    for target in Team.objects.all():#.exclude(team_id=payload['team_id']):
        Channel("background-slack-share-msg").send({
                                            'func':event['type'],
                                            'args':args,
                                            'api_token':target.app_access_token
                                        })

def share_msg(message):
    logger.info("Executing slack responses")
    slack = Slacker(message.content['api_token'])
    func = None

    if message.content['func'] == "message":
        func = slack.chat.post_message

    if not func:
        logger.debug(message.content)
        logger.debug(func)
        func(**message.content['args'])
