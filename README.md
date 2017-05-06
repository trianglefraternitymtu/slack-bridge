# Slack Team Bridge [![Build Status](https://travis-ci.org/trianglefraternitymtu/slack-bridge.svg?branch=master)](https://travis-ci.org/trianglefraternitymtu/slack-bridge) [![Coverage Status](https://coveralls.io/repos/github/trianglefraternitymtu/slack-bridge/badge.svg?branch=master)](https://coveralls.io/github/trianglefraternitymtu/slack-bridge?branch=master)
Application that allows you to create a bridge between two Slack teams, allowing them to be communicate in a common channel.

## Local Development

Requirements:
- Python 3.5
- Latest version of pip for Python 3.5
- virtualenv
- Heroku CLI
- Redis
 - You can use the one from your Heroku instance it you know what you're looking for


0. Checkout the repository
0. Make a pyton virtual environment using `virtualenv venv`
0. Install all the packages into the environment using `pip install -r requirements.txt`
0. Launch the server using `heroku local` or `heroku local -f Profile.windows`

# Installation

## Slack App Entry

## Deploy onto Heroku

Once the App has entry has been made, deploy the application onto Heroku and enter in the values from the App configuration menu from before.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/trianglefraternitymtu/slack-bridge)

## Adding it to your teams

After the server is all provisioned, head back over to the App configuration menu. Select "Manage Distribution" and click the "Add to Slack" on the right side. Do this for ever team you want the app to be installed on.

# Configuration

When are prompted to authorize the app on your team, one of the options you'll be given is for an incomming webhook. This webhook will post the content from the other teams into whichever channel you select, so choose wisely where you want that to go. It's generally a good idea to make a new public channel and select that channel instead of #random or #general. After that is all completed, head over to slack and invite the new bot over to that channel that you selected with the webhook.
