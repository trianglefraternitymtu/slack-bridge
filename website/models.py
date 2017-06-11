from django.db import models

class Team(models.Model):
    team_id = models.CharField(max_length=10, primary_key=True)
    bot_id  = models.CharField(max_length=12)
    app_access_token = models.CharField(max_length=128)
    bot_access_token = models.CharField(max_length=128)

class SharedChannel(models.Model):
    local_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    channel_id = models.CharField(max_length=12)

class PostedMsg(models.Model):
    channel = models.ForeignKey(SharedChannel, on_delete=models.CASCADE)
    timestamp = models.CharField(max_length=18)
    satellites = models.ManyToManyField('self')
