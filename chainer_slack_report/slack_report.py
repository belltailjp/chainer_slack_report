import io
import json
import os
import re
import sys
import socket
import time
import warnings

from datetime import datetime
from datetime import timedelta

import requests

import chainer


def _slack_request(ep, method, params):
    ep = 'https://slack.com/api/{}'.format(ep)
    if method == 'get':
        r = requests.get(ep, params=params)
    elif method == 'post':
        r = requests.post(ep, data=params)
    body = json.loads(r.text)
    if not body['ok']:
        msg = body["error"]
        warnings.warn('SlackReport cannot connect to Slack: (error="{}")'
                      .format(msg))
        return None
    return body


def _check_valid_token(access_token, channel_id):
    if not access_token or not channel_id:    # None or empty
        return False

    params = {'token': access_token}
    if not _slack_request('auth.test', 'get', params):
        return False

    params['channel'] = channel_id
    if not _slack_request('channels.info', 'get', params):
        return False
    return True


def _name_to_mention(access_token, names):
    user_ids = dict()
    cursor = None
    while True:
        params = {'token': access_token, 'cursor': cursor}
        r = _slack_request('users.list', 'get', params)
        if not r:
            return []
        user_ids = {**user_ids, **{m['name']: m['id'] for m in r['members']}}
        cursor = r['response_metadata']['next_cursor']
        if not cursor:
            break
        time.sleep(3)     # users.list is a Tier-2 API; 20+ requests/min

    if isinstance(names, str):
        names = [names]

    ret = []
    for name in names:
        name = name.replace('@', '')
        if name not in user_ids:
            warnings.warn("The specified user @{} not found in the workspace"
                          .format(name))
            continue
        ret.append("<@{}>".format(user_ids[name]))
    return " ".join(ret)


class SlackReport(chainer.training.extensions.PrintReport):
    def __init__(self, access_token, channel_id, entries,
                 template="${status} - ${elapsed} `${hostname}:${pwdshort}$ "
                          "${cmd} ${args}`\n"
                          "${content}\n"
                          "${finish_mentions}",
                 finish_mentions=[], log_report='LogReport'):
        super(SlackReport, self).__init__(
            entries, log_report=log_report, out=io.StringIO())
        self._access_token = access_token
        self._channel_id = channel_id
        self._available = _check_valid_token(access_token, channel_id)

        self._completed = False
        self._mention = ""
        if self._available and len(finish_mentions):
            self._mention = _name_to_mention(access_token, finish_mentions)

        self._start_time = datetime.now()

        # Check template format
        self._template = template
        self._make_content(self._template, "content", "status", "mention",
                           warn=True)

        self._ts = None
        self._print(None)   # Initial message

    @property
    def available(self):
        return self._available

    def _make_content(self, template, content, status, mention, warn=True):
        template = str(template)

        pwd = os.getcwd()
        pwdshort = pwd.replace(os.path.expanduser('~'), '~')

        # Use only seconds
        elapsed = datetime.now() - self._start_time
        elapsed = timedelta(days=elapsed.days, seconds=elapsed.seconds)

        template = re.sub(r'\${status}', status, template)
        template = re.sub(r'\${hostname}', socket.gethostname(), template)
        template = re.sub(r'\${pwd}', os.getcwd(), template)
        template = re.sub(r'\${pwdshort}', pwdshort, template)
        template = re.sub(r'\${cmd}', sys.argv[0], template)
        template = re.sub(r'\${args}', " ".join(sys.argv[1:]), template)
        template = re.sub(r'\${elapsed}', str(elapsed), template)
        template = re.sub(r'\${content}', content, template)
        template = re.sub(r'\${finish_mentions}', mention, template)
        if warn:
            rest = re.findall(r'\${\w+}', template)
            if rest:
                warnings.warn("Unknown template variable(s) specified: {}"
                              .format(", ".join(rest)))
        return template

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

        mention = ""
        if self._completed:
            status = "*[Completed]*"
            mention = self._mention

        params = {
            'token': self._access_token,
            'channel': self._channel_id,
            'text': self._make_content(self._template, s, status, mention)
        }
        if not self._ts:    # New post
            res = _slack_request('chat.postMessage', 'post', params)
            if not res:
                self._available = False
                return
            self._ts = res['ts']
        else:               # Update the post
            params['ts'] = self._ts
            if not _slack_request('chat.update', 'post', params):
                self._available = False
            # TODO: deal with the case where the post no longer exists

    def finalize(self):
        self._completed = True
        self._print(None)
