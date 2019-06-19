import io
import json
import sys

import requests

import chainer


class SlackReport(chainer.training.extensions.PrintReport):
    def __init__(self, access_token, channel_id, entries,
                 label=None, log_report='LogReport'):
        super(SlackReport, self).__init__(
            entries, log_report=log_report, out=io.StringIO())
        self.access_token = access_token
        self.channel_id = channel_id

        self.ts = None

        self.label = label
        if label is None:
            self.label = " ".join(sys.argv)

    def _print(self, observation):
        super(SlackReport, self)._print(observation)

        s = self._out.getvalue().replace('\x1b[J', '')  # Remove clear screen
        s = "```{}```".format(s)
        if self.label:
            s = "{}\n{}".format(self.label, s)

        params = {
            'token': self.access_token,
            'channel': self.channel_id,
            'text': s
        }
        if self.ts is None:
            # New post
            res = requests.post('https://slack.com/api/chat.postMessage',
                                data=params)
            res = json.loads(res.text)
            if not res['ok']:
                return
            self.ts = res['ts']
        else:
            # Update the post
            params['ts'] = self.ts
            res = requests.post('https://slack.com/api/chat.update',
                                data=params)
            res = json.loads(res.text)
            if not res['ok']:
                return
