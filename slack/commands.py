import logging, json
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
    json_payload = json.loads(request.body.decode())
    logger.debug(json_payload)

    token = json_payload.get('token')

    if not verified_token(token):
        logger.warning("Token verification failed. ({})".format(token))
        return HttpResponse(status=401)

    return HttpResponse(status=200)
