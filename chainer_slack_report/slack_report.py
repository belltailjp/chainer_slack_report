import io
import json
import os
import re
import sys
import socket
import time
import traceback
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


class _IgnoreMissingDict(dict):
    def __missing__(self, k):
        if not hasattr(self, 'missings'):
            self.missings = []
        self.missings.append(k)
        return '{' + k + '}'


def _thin_out(lines, i):
    return [lines[j] for j in range(0, len(lines), i)]


def _lifo(lines, i):
    return lines[:-i]


def _fifo(lines, i):
    return lines[i:]


_len_normalizers = {'thin_out': _thin_out, 'lifo': _lifo, 'fifo': _fifo}


class SlackReport(chainer.training.extensions.PrintReport):
    def __init__(self, access_token, channel_id, entries,
                 template="{status} - {elapsed} `{hostname}:{pwdshort}$ "
                          "{cmd} {args}`\n"
                          "{content}\n"
                          "{finish_mentions}",
                 finish_mentions=[], len_normalizer='thin_out',
                 log_report='LogReport'):
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

        len_normalizer = len_normalizer.lower()
        if len_normalizer not in _len_normalizers:
            msg = "Unknown value {} is specified to len_normalizer.\n" \
                  "Available values: {}" \
                  .format(len_normalizer, ", ".join(_len_normalizers.keys()))
            raise ValueError(msg)
        self._len_norm = _len_normalizers[len_normalizer]

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

        # Use only seconds (ignore sub-seconds)
        elapsed = datetime.now() - self._start_time
        elapsed = timedelta(days=elapsed.days, seconds=elapsed.seconds)

        fmt = _IgnoreMissingDict({
            'status': status,
            'hostname': socket.gethostname(),
            'pwd': os.getcwd(),
            'pwdshort': pwdshort,
            'cmd': sys.argv[0],
            'args': " ".join(sys.argv[1:]),
            'elapsed': str(elapsed),
            'content': "```{}```".format(content) if content else "",
            'finish_mentions': mention
        })

        # Normalize the content to make the whole report fit to 4000 bytes
        s = template.format_map(fmt)

        lines = [re.sub(r' +$', '', l) for l in content.splitlines()]
        header, lines = lines[:1], lines[1:]
        i_try = 1
        while 4000 < len(s.encode('utf-8')):
            content = "\n".join(header + self._len_norm(lines, i_try))
            fmt['content'] = "```{}```".format(content)
            s = template.format_map(fmt)
            i_try += 1

        if warn and hasattr(fmt, 'missings'):
            warnings.warn("Unknown template variable(s) specified: {}"
                          .format(", ".join(fmt.missings)))
        return s

    def _print(self, observation):
        try:
            if observation:     # None case: called from finalize or __init__
                super(SlackReport, self)._print(observation)

            if not self._available:
                return

            s = self._out.getvalue().replace('\x1b[J', '')  # Remove CLS
            status = "[_Training_]" if s else "[_Started_]"

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

        except Exception as e:
            # Even if the SlackReport dies with an unknown error,
            # it should never stop the whole process!
            tb = "\n".join(traceback.format_tb(e.__traceback__))
            warnings.warn("{}\n{}".format(str(e), tb))

    def finalize(self):
        self._completed = True
        self._print(None)
