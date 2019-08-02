import os
from setuptools import setup


# Get __version__
here = os.path.abspath(os.path.dirname(__file__))
exec(open(os.path.join(here, 'chainer_slack_report', 'version.py')).read())


setup(name='chainer-slack-report',
      url='https://github.com/belltailjp/chainer_slack_report',
      version=__version__,      # NOQA
      description='Send PrintReport content to Slack',
      author='Daichi SUZUO',
      author_email='belltailjp@gmail.com',
      packages=['chainer_slack_report'],
      test_require=[],
      install_requires=[
          'requests>=2.21.0',
          'chainer>=5.0.0'
      ])
