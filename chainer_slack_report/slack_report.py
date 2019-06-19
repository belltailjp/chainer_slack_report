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
        self._access_token = access_token
        self._channel_id = channel_id

        self._ts = None
        self._completed = False

        self._label = label
        if label is None:
            self._label = " ".join(sys.argv)

    def _print(self, observation):
        if observation:     # None case: called from finalize
            super(SlackReport, self)._print(observation)

        s = self._out.getvalue().replace('\x1b[J', '')  # Remove clear screen
        s = "```{}```".format(s)

        if self._label:
            s = "{}\n{}".format(self._label, s)
        if self._completed:
            s = "*[Completed]* " + s

        params = {
            'token': self._access_token,
            'channel': self._channel_id,
            'text': s
        }
        if self._ts is None:
            # New post
            res = requests.post('https://slack.com/api/chat.postMessage',
                                data=params)
            res = json.loads(res.text)
            if not res['ok']:
                return
            self._ts = res['ts']
        else:
            # Update the post
            params['ts'] = self._ts
            res = requests.post('https://slack.com/api/chat.update',
                                data=params)
            res = json.loads(res.text)
            if not res['ok']:
                return

    def finalize(self):
        self._completed = True
        self._print(None)
