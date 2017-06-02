from channels.routing import route
import slack.consumers

channel_routing = [
    route('background-slack-event', slack.consumers.event),
    route('background-slack-post', slack.consumers.post),
    route('background-slack-update', slack.consumers.update),
    route('background-slack-action', slack.consumers.action),
]
