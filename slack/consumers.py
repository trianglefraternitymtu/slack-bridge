import logging, os, re

from functools import partial
from channels import Channel
from slacker import Slacker
from slacker import Error as SlackError
from website.models import Team, SharedChannel
from django.shortcuts import get_object_or_404
from . import clear_tags, revert_hyperlinks, get_local_timestamp

logger = logging.getLogger('basicLogger')

def action(message):
    logger.debug("Processing action response.")

def event(message):
    logger.debug("Processing event.")

    payload = message.content
    event = payload['event']
    subtype = event.get('subtype')
    subsubtype = (event.get('message', {}).get('subtype') or event.get('previous_message', {}).get('subtype'))

    local_team = get_object_or_404(Team, team_id=payload['team_id'])
    local_team_interface = Slacker(local_team.app_access_token)

    sa_text = clear_tags(local_team_interface, event.get('text', ''))

    if event['type'] not in ["message"]:
        logger.warning('Not sure what "{}" event is...'.format(event['type']))

    elif subtype == 'bot_message' or subsubtype == 'bot_message':
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

    elif subtype in ('message_changed', 'message_deleted'):
        for target in _otherChannels(event['channel'], local_team):
            if target.local_team.team_id != local_team.team_id:
                payload['event']['text'] = sa_text
            Channel("background-slack-update").send({"payload":payload,
                                                     "channel_id":target.channel_id,
                                                     "team_id":target.local_team.team_id})

    else:
        user_info = local_team_interface.users.info(event['user']).body['user']

        threaded_text = None
        if event.get('thread_ts', event['ts']) != event['ts']:
            # need to go find the original message text on the target team.
            msg = local_team_interface.channels.history(event['channel'],
                                                        inclusive=True,
                                                        oldest=event['thread_ts'],
                                                        count=1).body['messages'][0]

            threaded_text = msg['text']

        for target in _otherChannels(event['channel'], local_team):
            if target.local_team.team_id != local_team.team_id:
                payload['event']['text'] = sa_text

            Channel('background-slack-post').send({'payload':payload,
                                                   'user':user_info,
                                                   'channel_id':target.channel_id,
                                                   'team_id':target.local_team.team_id,
                                                   'threaded_text':threaded_text})

def _otherChannels(ch_id, team):
    return SharedChannel.objects.exclude(channel_id=ch_id, local_team=team)

def post(message):
    payload = message.content['payload']
    event = payload['event']
    user = message.content['user']
    subtype = event.get('subtype')
    subsubtype = (event.get('message', {}).get('subtype') or event.get('previous_message', {}).get('subtype'))

    logger.debug("Posting message ({} <{}>).".format(subtype, subsubtype))

    team = get_object_or_404(Team, team_id=message.content['team_id'])
    team_interface = Slacker(team.app_access_token)

    if subtype in ["channel_join", "channel_leave"]:
        event['text'] = '_{}_'.format(event['text'])

    thread_ts = None
    if message.content['threaded_text']:
        thread_ts = get_local_timestamp(team_interface, message.content['channel_id'], message.content['threaded_text'])

    team_interface.chat.post_message(text=event['text'],
                            attachments=event.get('attachments'),
                            channel=message.content['channel_id'],
                            username=(user['profile']['real_name'] or user['profile']['name']),
                            icon_url=user['profile']['image_192'],
                            thread_ts=thread_ts,
                            as_user=False)

def update(message):
    payload = message.content['payload']
    event = payload['event']
    user = message.content['user']
    subtype = event.get('subtype')
    subsubtype = (event.get('message', {}).get('subtype') or event.get('previous_message', {}).get('subtype'))

    logger.debug("Pushing update ({}<{}>).".format(subtype, subsubtype))

    team = get_object_or_404(Team, team_id=message.content['team_id'])
    team_interface = Slacker(team.app_access_token)

    target_ts = get_local_timestamp(team_interface, message.content['channel_id'], event.get('text'))

    if subtype == "message_changed":
        sa_text = revert_hyperlinks(event.get('text', ''))
        team_interface.chat.update(message.content['channel_id'],
                                   as_user=False, ts=target_ts, text=sa_text,
                                   attachments=event['message'].get('attachments'))

    elif subtype == "message_deleted":
        team_interface.chat.delete(message.content['channel_id'],
                                   ts=target_ts,
                                   as_user=False)
