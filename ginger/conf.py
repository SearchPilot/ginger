import argparse

import yaml


parser = argparse.ArgumentParser(
    description='Script to build a static file website')
parser.add_argument('--settings',
                    dest='settings',
                    default='ginger.yml',
                    help="Settings file to use")
parser.add_argument('--watch', '-w',
                    dest='watch',
                    default=False,
                    nargs='?',
                    const=True,
                    help="Should we watch the input file for changes and trigger a rebuild?")
parser.add_argument('--dev', '-d',
                    dest='dev',
                    default=False,
                    nargs='?',
                    const=True,
                    help="Dev mode. Skip minification to speed and ease development?")
args = parser.parse_args()


class Settings(object):
    """ A wrapper around a settings module """

    def __init__(self, settings_file):

        with open(settings_file) as file:
            self.settings = yaml.load(file)

    def __getattr__(self, key):

        return self.settings.get(key)

settings = Settings(args.settings)
