import logging, os, re

from functools import partial
from channels import Channel
from slacker import Slacker
from slacker import Error as SlackError
from website.models import Team, SharedChannel
from django.shortcuts import get_object_or_404
from . import clear_tags, revert_hyperlinks

logger = logging.getLogger('basicLogger')

def action(message):
    logger.debug("Processing action response.")

def event(message):
    logger.debug("Processing event.")

    payload = message.content
    event = payload['event']
    subtype = event.get('subtype')

    local_team = get_object_or_404(Team, team_id=payload['team_id'])
    local_team_interface = Slacker(local_team.app_access_token)

    if event['type'] != "message":
        logger.warning('Not sure what "{}" event is...'.format(event['type']))

    elif subtype == 'bot_message':
        logger.info("Ignoring stuff by other bots...")

    elif subtype == "channel_join" and event.get("user") == local_team.bot_id:
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
        if subtype in ('message_changed', 'message_deleted'):
            user_info = None
        else:
            user_info = local_team_interface.users.info(event['user']).body['user']

        sa_text = clear_tags(local_team_interface, event.get('text', ''))

        for target in SharedChannel.objects.exclude(channel_id=event['channel'], local_team=local_team):
            if target.local_team.team_id != local_team.team_id:
                event['text'] = sa_text
            Channel("background-slack-update").send({"payload":payload,
                                                     "user":user_info,
                                                     "channel_id":target.channel_id,
                                                     "team_id":target.local_team.team_id})

def update(message):
    payload = message.content['payload']
    event = payload['event']
    user = message.content['user']
    subtype = event.get('subtype')
    subsubtype = (event.get('message', {}).get('subtype') or event.get('previous_message', {}).get('subtype'))

    logger.debug("Pushing update ({}<{}>).".format(subtype, subsubtype))

    team = get_object_or_404(Team, team_id=message.content['team_id'])
    team_interface = Slacker(team.app_access_token)

    if subsubtype == 'bot_message':
        logger.info("Ignoring stuff by other bots...")

    elif subtype == "message_changed":
        msgs = team_interface.channels.history(message.content['channel_id'],
                                               count=100).body['messages']

        sa_text = revert_hyperlinks(event['message'].get('text', ''))

        for msg in msgs:
            logger.debug(msg.get('text'))
            if msg.get('text') == event['previous_message']['text']:
                logger.info("Found a matching timestamp of {}".format(msg['ts']))
                team_interface.chat.update(message.content['channel_id'],
                                           as_user=False,
                                           ts=msg['ts'],
                                           text=sa_text,
                                           attachments=event.get('attachments'))
                break

    elif subtype == "message_deleted":
        msgs = team_interface.channels.history(message.content['channel_id'],
                                               count=100).body['messages']

        for msg in msgs:
            logger.debug(msg.get('text'))
            if msg.get('text') == event['previous_message']['text']:
                logger.info("Found a matching timestamp of {}".format(msg['ts']))
                team_interface.chat.delete(message.content['channel_id'],
                                           ts=msg['ts'],
                                           as_user=False)
                break
    else:
        if event.get('subtype') in ["channel_join", "channel_leave"]:
            event['text'] = '_{}_'.format(event['text'])

        team_interface.chat.post_message(text=event['text'],
                                attachments=event.get('attachments'),
                                channel=message.content['channel_id'],
                                username=(user['profile']['real_name'] or user['profile']['name']),
                                icon_url=user['profile']['image_192'],
                                as_user=False)
