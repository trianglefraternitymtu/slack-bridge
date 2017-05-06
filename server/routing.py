from channels.routing import route
import slack.consumers

channel_routing = [
    route('background-slack-event', slack.consumers.event),
    route('background-slack-share-msg', slack.consumers.share_msg),
]
