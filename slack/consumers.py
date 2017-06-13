import logging, re

from channels import Channel
from slacker import Slacker
from website.models import Team, SharedChannel, PostedMsg
from django.shortcuts import get_object_or_404
from . import clear_tags, revert_hyperlinks, get_local_timestamp, other_channels

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
        Channel("background-slack-update").send(payload)

    else:
        Channel('background-slack-post').send(payload)

def post(message):
    payload = message.content
    event = payload['event']

    local_team = get_object_or_404(Team, team_id=payload['team_id'])
    local_team_interface = Slacker(local_team.app_access_token)

    sa_text = clear_tags(local_team_interface, event.get('text', ''))

    user_info = local_team_interface.users.info(event['user']).body['user']
    shared_ch = get_object_or_404(SharedChannel,
                                  channel_id=event['channel'],
                                  local_team=local_team)

    msg_set = [PostedMsg.objects.create(channel=shared_ch,
                                        timestamp=event['ts'])]

    for target in other_channels(event['channel'], local_team):
        temp = event
        if target.local_team.team_id != local_team.team_id:
            temp['text'] = sa_text
        ts = doPost(temp, user_info, target, shared_ch)

        msg_set.append(PostedMsg.objects.create(channel=target, timestamp=ts))

    for msg in msg_set:
        msg.satellites.add(*[m for m in msg_set if m != msg])

def doPost(event, user, channel, origin):
    subtype = event.get('subtype')
    subsubtype = (event.get('message', {}).get('subtype') or event.get('previous_message', {}).get('subtype'))

    logger.debug("Posting message ({} <{}>).".format(subtype, subsubtype))

    team_interface = Slacker(channel.local_team.app_access_token)

    if subtype in ["channel_join", "channel_leave"]:
        event['text'] = '_{}_'.format(event['text'])

    thread_ts = None
    if event.get('thread_ts', event['ts']) != event['ts']:
        # need to go find the original message text on the target team.
        thread_ts, thread_msg = get_local_timestamp(event['thread_ts'], origin, channel)
        logger.debug(thread_ts)

    return team_interface.chat.post_message(text=event['text'],
                            attachments=event.get('attachments'),
                            channel=channel.channel_id,
                            username=(user['profile'].get('real_name') or user['name']),
                            icon_url=user['profile']['image_192'],
                            thread_ts=thread_ts,
                            as_user=False).body['ts']

def update(message):
    payload = message.content
    event = payload['event']

    local_team = get_object_or_404(Team, team_id=payload['team_id'])
    shared_ch = get_object_or_404(SharedChannel,
                                  channel_id=event['channel'],
                                  local_team=local_team)

    subtype = event.get('subtype')
    subsubtype = (event.get('message', {}).get('subtype') or event.get('previous_message', {}).get('subtype'))

    logger.debug("Pushing {} ({}).".format(subtype, subsubtype))

    for target in other_channels(event['channel'], local_team):
        if subtype == "message_changed":
            doUpdate(event, target, shared_ch)
        elif subtype == "message_deleted":
            doDelete(event, target, shared_ch)

    if subtype == "message_deleted":
        target_ts = PostedMsg.objects.get(timestamp=event['ts'], channel=shared_ch)
        target_ts.delete()

def doUpdate(event, channel, origin):
    team_interface = Slacker(channel.local_team.app_access_token)

    target_ts, target = get_local_timestamp(event['previous_message']['ts'], origin, channel)

    sa_text = revert_hyperlinks(event['message'].get('text', ''))
    return team_interface.chat.update(channel.channel_id,
                                   as_user=False,
                                   ts=target_ts,
                                   text=sa_text,
                                   attachments=event['message'].get('attachments')).body['ts']

def doDelete(event, channel, origin):
    team_interface = Slacker(channel.local_team.app_access_token)

    target_ts, target = get_local_timestamp(event['previous_message']['ts'], origin, channel)

    temp =  team_interface.chat.delete(channel.channel_id,
                               ts=target_ts,
                               as_user=False).body['ts']

    target.delete()
    return temp
