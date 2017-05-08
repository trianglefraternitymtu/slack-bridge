from channels.routing import route
import slack.consumers

channel_routing = [
    route('background-slack-event', slack.consumers.event),
]
