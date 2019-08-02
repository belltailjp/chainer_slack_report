from setuptools import setup
import chainer_slack_report

setup(name='chainer-slack-report',
      url='https://github.com/belltailjp/chainer_slack_report',
      version=chainer_slack_report.__version__,
      description='Send PrintReport content to Slack',
      author='Daichi SUZUO',
      author_email='belltailjp@gmail.com',
      packages=['chainer_slack_report'],
      test_require=[],
      install_requires=[
          'requests>=2.21.0',
          'chainer>=5.0.0'
      ])
