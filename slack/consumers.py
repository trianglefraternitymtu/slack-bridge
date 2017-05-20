import logging, os, re

from functools import partial
from channels import Channel
from slacker import Slacker
from slacker import Error as SlackError
from website.models import Team, SharedChannel
from django.shortcuts import get_object_or_404

logger = logging.getLogger('basicLogger')

def action(message):
    logger.debug("Processing action response.")

def event(message):
    logger.debug("Processing event.")

    payload = message.content
    event = payload['event']

    local_team = get_object_or_404(Team, team_id=payload['team_id'])
    local_team_interface = Slacker(local_team.app_access_token)

    if event['type'] != "message":
        logger.warning('Not sure what "{}" event is...'.format(event['type']))

    elif event.get('subtype') == 'bot_message':
        logger.info("Ignoring stuff by other bots...")

    elif event.get("subtype") == "channel_join" and event.get("user") == local_team.bot_id:
        logger.info("Bot was added to channel {} on team {}".format(event['channel'], local_team.team_id))
        SharedChannel.objects.get_or_create(channel_id=event['channel'],
                                            local_team=local_team)

    elif event.get('user') == 'USLACKBOT':
        if "You have been removed from" in event['text']:
            ch_name = re.findall(r'#([^A-Z. ]+)', event['text'])[0]
            ch_id = local_team_interface.channels.get_channel_id(ch_name)
            logger.info('Bot was removed from channel "{}" ({}) on team {}'.format(ch_name, ch_id, local_team.team_id))
            left = SharedChannel.objects.get(channel_id=ch_id,
                                             local_team=local_team)
            left.delete()

        else:
            logger.info("Ignoring slackbot updates")
    else:
        user_info = local_team_interface.users.info(event['user']).body['user']

        sa_text = _sanitizeText(local_team_interface, event.get('text', ''))

        for target in SharedChannel.objects.exclude(channel_id=event['channel'], local_team=local_team):
            if target.local_team.team_id != local_team.team_id:
                event['text'] = sa_text
            Channel("background-slack-update").send({"payload":payload,
                                                     "user":user_info,
                                                     "channel_id":target.channel_id,
                                                     "team_id":target.local_team.team_id})

def update(message):
    logger.debug("Pushing update.")

    payload = message.content['payload']
    event = payload['event']
    user = message.content['user']

    team = get_object_or_404(Team, team_id=message.content['team_id'])
    team_interface = Slacker(team.app_access_token)

    if event.get('subtype') == "message_changed":
        # team_interface.chat.udpate()
        pass
    elif event.get('subtype') == "message_deleted":
        # team_interface.chat.delete()
        pass
    else:
        if event.get('subtype') in ["channel_join", "channel_leave"]:
            event['text'] = '_{}_'.format(event['text'])

        team_interface.chat.post_message(text=event['text'],
                                attachments=event.get('attachments'),
                                channel=message.content['channel_id'],
                                username=(user['profile']['real_name'] or user['profile']['name']),
                                icon_url=user['profile']['image_192'],
                                as_user=False
                                )

def _sanitizeText(slack, text):
    members = slack.users.list().body['members']
    mem_map = [('<@{}>'.format(m['id']), '@{}'.format(m['name'])) for m in members]

    channels = slack.channels.list().body['channels']
    ch_map = [('<#{}|{}>'.format(c['id'], c['name']), '#{}'.format(c['name'])) for c in channels]

    for k,v in mem_map + ch_map:
        text = text.replace(k,v)
    return text
