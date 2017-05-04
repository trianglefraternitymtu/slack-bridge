from django.shortcuts import redirect
from django.views.decorators.http import require_GET
import logging

logger = logging.getLogger('basicLogger')

@require_GET
def info(request):
    return redirect('https://github.com/trianglefraternitymtu/slack-bridge')
