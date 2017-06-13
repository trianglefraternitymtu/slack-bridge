import os, re
from django.shortcuts import get_object_or_404
from website.models import SharedChannel, PostedMsg

def error_msg(msg):
    return {
        'icon_emoji' : ':warning:',
        'response_type' : 'ephemeral',
        'text' : msg
    }

def verified_token(token):
    app_verification_token = os.environ.get('SLACK_VERIFICATION_TOKEN')
    return app_verification_token == token or not app_verification_token

def clear_tags(slack, text):
    members = slack.users.list().body['members']
    mem_map = [('<@{}>'.format(m['id']), '@{}'.format(m['name'])) for m in members]

    channels = slack.channels.list().body['channels']
    ch_map = [('<#{}|{}>'.format(c['id'], c['name']), '#{}'.format(c['name'])) for c in channels]

    for k,v in mem_map + ch_map:
        text = text.replace(k,v)
    return text

def revert_hyperlinks(text):
    sa_items = re.findall(r'<([^!#]{1}.*?)>', text)
    sa_re = [("<{}>".format(x), x) for x in sa_items]

    for k,v in sa_re:
        text = text.replace(k,v)

    return text

def other_channels(ch_id, team):
    return SharedChannel.objects.exclude(channel_id=ch_id, local_team=team)

def get_local_timestamp(timestamp, origin, context=None):
    root_msg = get_object_or_404(PostedMsg, timestamp=timestamp, channel=origin)

    if context:
        root_msg = root_msg.satellites.get(channel=context)

    return root_msg.timestamp, root_msg
