# chainer-slack-report

This is a [Chainer](https://chainer.org/)'s
[Trainer extension](https://docs.chainer.org/en/v6.0.0/guides/extensions.html)
that reports the same contents as the commonly-used
[PrintReport](https://docs.chainer.org/en/v6.0.0/reference/generated/chainer.training.extensions.PrintReport.html) extension to Slack.

```python
from chainer_slack_report import SlackReport
...
trainer.extend(SlackReport(access_token, channel_id, [
    'epoch', 'main/loss', 'validation/main/loss',
    'main/accuracy', 'validation/main/accuracy',
    'elapsed_time',
]), trigger=(1, 'epoch'))
...
trainer.run()
```

![screen](docs/screencast.gif)


## Install

```bash
% pip install chainer-slack-report
```

Or

```bash
% pip install git+https://github.com/belltailjp/chainer_slack_report
```


## Slack App preparation

In order to get it work, you will first need to prepare for a bot account
on your Slack workspace as explained in the following instruction.

First, access to https://api.slack.com/apps.
You might be asked for signing-in to a workspace, so follow the Slack screen.
Then you will see a window with "Create New App" button. Click it.
![Create new app](docs/01_create_new_app.png)


Fill the App Name field. Anything is fine.
The workspace should be the one that you'd like to send the report to.
Then click the "Create App" button.
![Set app name and workspace](docs/02_app_name_and_workspace.png)


The app you have created has no permission to access to Slack at all yet,
so scroll down the window and click the "Permissions" button.
![Go to permission screen](docs/03_permissions.png)


Scroll down, and add `chat:write:bot` permission.
![Set permission](docs/04_permissions_select.png)


You can now activate the app in your workspace
by going back to the upper part of the screen
and clicking the "Install..." button.
![Install app](docs/05_install_app.png)


Then you'll be redirected to a screen with Access Token.
This is what you need to tell to `SlackReport`.
![Token](docs/06_you_will_get_token.png)


Your app doesn't have an icon yet,
so let's set it by "Basic Information" screen.
![Basic Information](docs/07_basic_information.png)
![Set icon](docs/08_set_icon.png)


Here, your *app* is ready!

But you also have to identify Slack channel ID to send report to.

You can find it by looking at full URL of the target channel.

![Channel URL](docs/09_find_slack_channel_url.png)

The copied URL will be like `https://WORKSPACE.slack.com/messages/CXXXXXXXX`,
whose `CXXXXXXXX` part is the channel ID.


## How it works

`SlackReport` inherits `chainer.training.extensions.PrintReport` extension,
and hooks its print function, and just sends the content to Slack
rather than stdout.

Therefore, except for `out` argument,
you can pass anything that `PrintReport` can accept to `SlackReport` too.


## License

MIT License
