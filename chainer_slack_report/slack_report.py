import io
import json
import sys
import warnings

import requests

import chainer


def _post_or_update_message(params, update=False):
    ep = "chat.update" if update else "chat.postMessage"
    res = requests.post('https://slack.com/api/{}'.format(ep), data=params)
    body = json.loads(res.text)
    if not body['ok']:
        msg = body["error"]
        warnings.warn('SlackReport cannot connect to Slack: (error="{}")'
                      .format(msg))
        return None
    return body


class SlackReport(chainer.training.extensions.PrintReport):
    def __init__(self, access_token, channel_id, entries,
                 label=None, log_report='LogReport'):
        super(SlackReport, self).__init__(
            entries, log_report=log_report, out=io.StringIO())
        self._access_token = access_token
        self._channel_id = channel_id
        self._available = self._check_valid_token(access_token, channel_id)

        self._completed = False

        self._label = label
        if label is None:
            self._label = " ".join(sys.argv)

        self._ts = None
        self._print(None)   # Initial message

    @property
    def available(self):
        return self._available

    def _check_valid_token(self, access_token, channel_id):
        if not access_token or not channel_id:    # None or empty
            return False

        # Note: channel ID existence check won't be done, as it requires
        # an additional premission just for it

        params = {'token': access_token}
        res = requests.post('https://slack.com/api/auth.test', data=params)
        return res.status_code == 200 and json.loads(res.text)['ok']

    def _print(self, observation):
        if observation:     # None case: called from finalize or __init__
            super(SlackReport, self)._print(observation)

        if not self._available:
            return

        s = self._out.getvalue().replace('\x1b[J', '')  # Remove clear screen
        if s:
            s = "```{}```".format(s)
            status = "[_Training_]"
        else:
            status = "[_Started_]"

        if self._completed:
            status = "*[Completed]*"

        params = {
            'token': self._access_token,
            'channel': self._channel_id,
            'text': "{} {}\n{}".format(status, str(self._label), s)
        }
        if self._ts is None:
            # New post
            res = _post_or_update_message(params)
            if not res:
                self._available = False
                return
            self._ts = res['ts']
        else:
            # Update the post
            params['ts'] = self._ts
            if not _post_or_update_message(params, update=True):
                self._available = False

    def finalize(self):
        self._completed = True
        self._print(None)
