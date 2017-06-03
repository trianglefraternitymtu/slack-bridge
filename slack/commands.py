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
    logger.debug(request)
    logger.debug(request.POST)

    #NOTE: Slash commands are sent in x-www-form-urlencoded format, not JSON

    if not verified_token(request.POST['token']):
        logger.warning("Token verification failed. ({})".format(token))
        return HttpResponse(status=401)

    return HttpResponse(status=200)
