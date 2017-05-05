import logging, os

from . import verified_token
from slacker import OAuth
from channels import Channel
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from website.models import Team

logger = logging.getLogger('basicLogger')

def auth(request):
    logger.info('Authentication')
    logger.debug(request.GET)

    code = request.GET.get('code')
    state = request.GET.get('state', None)
    error = request.GET.get('error', None)

    client_id = os.environ.get('SLACK_CLIENT_ID')
    client_secret = os.environ.get('SLACK_CLIENT_SECRET')

    try:
        data = OAuth().access(client_id, client_secret, code).body
        logger.debug(data)
    except Exception as e:
        logger.exception(e)
        return redirect('slack-info')

    if state == 'appAdded' or not state:

        logger.debug("Adding team \"{team_id}\" to the database.".format(data))

        # Make a new team
        try:
            team, created = Team.objects.update_or_create(
                        team_id=data['team_id'],
                        defaults = {'app_access_token':data['access_token'],
                            'webhook_url':data['incoming_webhook']['url'],
                            'bot_id':data['bot']['bot_user_id'],
                            'app_access_token':data['bot']['bot_access_token']
                        })
            logger.info("Team added to database!")
        except Exception as e:
            logger.exception(e)
            return redirect('slack-info')

@csrf_exempt
@require_POST
def action(request):
    logger.info('Event Push')
    logger.debug(request.POST)

    # TODO Push processing of the action to the worker process

@csrf_exempt
@require_POST
def event(request):
    logger.info('Event Push')
    body = request.POST.body
    logger.debug(body)

    token = body.get('token')
    event_type = body.get('type')
    challenge = body.get('challenge', None)

    if not verified_token(token):
        logger.warning("Token verification failed. ({})".format(token))
        return HttpResponse(status=401)

    if event_type == "url_verification":
        logger.info("URL verification")
        return JsonResponse({"challenge":challenge})
    else:
        # TODO: Push processing of the event to the worker process
        return HttpResponse(status=200)
