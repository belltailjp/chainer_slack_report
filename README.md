# chainer-slack-report

This is a [Chainer](https://chainer.org/)'s
[Trainer extension](https://docs.chainer.org/en/v6.0.0/guides/extensions.html)
that reports the same contents as the commonly-used
[PrintReport](https://docs.chainer.org/en/v6.0.0/reference/generated/chainer.training.extensions.PrintReport.html) extension to Slack.

```python
from chainer_slack_report import SlackReport
...
r = SlackReport(os.environ.get("SLACK_ACCESS_TOKEN", None),
                os.environ.get("SLACK_CHANNEL_ID", None),
                ['epoch', 'main/loss', 'validation/main/loss',
                 'main/accuracy', 'validation/main/accuracy', 'elapsed_time']) 
trainer.extend(r, trigger=(1, 'epoch'))
...
trainer.run()
```

![screen](docs/screencast.gif)


The key feature (and difference between similar tools) of SlackReport is that
it can handle multiple training streams without collapsing Slack screen.

In case you run many training processes in parallel
and each of them uses SlackReport,
the reports sent from each process are always summarized in a single message
posted by a bot, without being mixed up with other processes' ones.

Therefore you can easily track how each process is going on.


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

Access to https://api.slack.com/apps.
You may be asked for signing-in to a workspace.
Then you will see a window with the "Create New App" button
which you should click.
![Create new app](docs/01_create_new_app.png)


Fill the App Name field. Anything is fine.
The workspace should be the one that you'd like to send reports to.
Then click the "Create App" button.
![Set app name and workspace](docs/02_app_name_and_workspace.png)


The app you have created has no permission to access Slack yet
so you have to configure it.
Scroll down the window and click the "Permissions" button.
![Go to permission screen](docs/03_permissions.png)


Scroll down, and add the `chat:write:bot` permission.
![Set permission](docs/04_permissions_select.png)


You can now activate the app in your workspace
by going back to the upper part of the screen
and clicking the "Install..." button.
![Install app](docs/05_install_app.png)


Then you'll be redirected to a screen with Access Token.
This is what you need to pass to `SlackReport`.
![Token](docs/06_you_will_get_token.png)


Your app doesn't have an icon yet,
so let's set it from the "Basic Information" screen.
![Basic Information](docs/07_basic_information.png)
![Set icon](docs/08_set_icon.png)


Here, your *Slack app* is ready!

But you also have to identify Slack channel ID to send report to.

On the Slack screen, you can find the channel ID by looking at full URL
of the target channel.

![Channel URL](docs/09_find_slack_channel_url.png)

The copied URL will be like `https://WORKSPACE.slack.com/messages/CXXXXXXXX`,
whose `CXXXXXXXX` part is the channel ID.


## How it works

`SlackReport` inherits `chainer.training.extensions.PrintReport` extension,
and hooks its print function, and just sends the content to Slack
rather than stdout.

Therefore, except for `out` argument,
you can pass anything that `PrintReport` can accept to `SlackReport` too.

At the very beginning of the SlackReport object lifetime,
it "creates" a new post, and from next time it "updates" the previous post.


## License

MIT License
