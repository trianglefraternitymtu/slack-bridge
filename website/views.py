import logging
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from .models import Team

logger = logging.getLogger('basicLogger')

@require_GET
def index(request):
    logger.info("Redirecting to GitHub Page...")
    return redirect('https://github.com/trianglefraternitymtu/slack-bridge')
