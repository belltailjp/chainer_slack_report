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

## Features

**Collision-free Slack messages**

The key feature (and difference between similar tools) of SlackReport is that
it can handle multiple training streams without collapsing Slack screen,
as shown in the above screencast.

In case you run many training processes in parallel
and each of them uses SlackReport,
the reported contents of each process are always summarized in a single message
posted by a bot, without being mixed up with other processes'.

That makes you easily track how each process is going on.


**Send a mention after the training finishes**

You can pass Slack user ID(s) that begin with '@' to
`finish_mentions` keyword argument of SlackReport initializer as
either a str or a list, in order to let SlackReport send a mention
notification after finishing the training process.



## Install

```bash
% pip install chainer-slack-report
```

Or

```bash
% pip install git+https://github.com/belltailjp/chainer_slack_report
```


## Slack App preparation

In order to get it work, you will first need to prepare for a bot user
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


Next, you have to tell Slack that you want the app to behave as a Bot.
Scroll down the window and click the "Bots" button.
![Go to bot creation screen](docs/03_bot_setting.png)


Just click the "Add a Bot User" button.
Here, Slack knows that your *app* is a *bot*.
![Create a bot](docs/04_add_bot_user.png)


You can name arbitrary display name and user name to the bot,
except that the user name has to be valid as an identifier.
![Create a bot](docs/05_fill_bot_info.png)


Next step is to activate the bot in your workspace
in order to get a credential to access to Slack API.
Go to "Install App" screen.
![Install app](docs/06_install_page.png)

![Install app](docs/07_click_bot_install.png)


Then you'll be redirected to a screen with a bot Access Token (the bottom one).
This is what you need to pass to `SlackReport`.
![Token](docs/08_got_token.png)


By the way, your bot doesn't have an icon yet,
so let's set it from the "Basic Information" screen.
![Basic Information](docs/09_basic_information.png)
![Set icon](docs/10_set_icon.png)


Here, your bot is ready!

You also have to identify Slack channel ID to send report to.

On the Slack screen, you can find the channel ID by looking at full URL
of the target channel.

![Channel URL](docs/11_find_slack_channel_url.png)

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
