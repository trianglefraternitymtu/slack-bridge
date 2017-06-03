import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from slacker import Slacker
from website.models import Team, SharedChannel
from . import verified_token

logger = logging.getLogger('basicLogger')

@csrf_exempt
@require_POST
def list_members(request):
    logger.debug(request.POST)

    #NOTE: Slash commands are sent in x-www-form-urlencoded format, not JSON

    if not verified_token(request.POST['token']):
        logger.warning("Token verification failed. ({})".format(request.POST['token']))
        return HttpResponse(status=401)

    local_team = get_object_or_404(Team, team_id=request.POST['team_id'])
    try:
        local_channel = SharedChannel.objects.get(channel_id=request.POST['channel_id'])
    except Exception as e:
        return JsonResponse({"text":"This doesn't seem to be a shared channel managed by this application."})

    breakdown = []

    try:
        for channel in SharedChannel.objects.all():
            team_interface = Slacker(channel.local_team.app_access_token)
            team_info = team_interface.team.info().body['team']

            channel_info = team_interface.channels.info(channel.channel_id).body['channel']
            roster = team_interface.users.list().body['members']
            filtered_roster = {u['id']:u for u in roster}

            channel_info['members'] = [filtered_roster[x] for x in channel_info['members'] if not filtered_roster[x].get('is_bot')]

            fields = []
            for member in channel_info['members']:
                temp = {
                    'title':(member['profile'].get('real_name') or member['name']),
                    'short':True
                }

                if member['profile'].get('real_name'):
                    temp['value'] = '@{}'.format(member['name'])

                fields.append(temp)

            breakdown.append({
                'title':team_info['name'],
                'title_link':'https://{}.slack.com'.format(team_info['domain']),
                'thumb_url':team_info['icon']['image_88'],
                'text':'There are {} people from this team on this channel.'.format(len(channel_info['members'])),
                'fields':fields
            })

            logger.info('Breakdown built for "{}."'.format(team_info['name']))
    except Exception as e:
        logger.exception(e)

    return JsonResponse({"attachments":breakdown})
