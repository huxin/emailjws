import argparse
from oauth2client import tools

parser = argparse.ArgumentParser(parents=[tools.argparser])
parser.add_argument("emailfile", metavar='emailfile', type=str, nargs=1)
flags = parser.parse_args()
flags.noauth_local_webserver = True
print flags.emailfile
print flags