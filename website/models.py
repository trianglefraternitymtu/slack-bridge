from django.db import models

class Team(models.Model):
    team_id = models.CharField(max_length=10, primary_key=True)
    bot_id  = models.CharField(max_length=12)
    webhook_url = models.URLField()
    app_access_token = models.CharField(max_length=28)
    bot_access_token = models.CharField(max_length=28)
