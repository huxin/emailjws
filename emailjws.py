# !/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import httplib2
import os
import base64

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr

from apiclient import errors
import binascii
import time
import random


import argparse
parser = argparse.ArgumentParser(parents=[tools.argparser])
parser.add_argument("emailfile", metavar='emailfile', type=str, nargs=1)
flags = parser.parse_args()
flags.noauth_local_webserver = True
input_email_file = flags.emailfile[0]

SLEEP_BETWEEN_EMAILS = 60 # 60-120 seconds per email
#SLEEP_BETWEEN_EMAILS = 3


SCOPES = "https://mail.google.com/"
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'jwsqusi'
import getpass
user = getpass.getuser()
log_file = open(str(user) + '_sent_history.log', 'a')

def print_log(s):
    print (s)
    log_file.write(s+"\n")
    log_file.flush()


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   APPLICATION_NAME + '.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.params['access_type'] = 'offline'
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print_log('Storing credentials to ' + credential_path)
    return credentials

# def create_text_message(sender_name, sender_email, to, subject, message_text):
#     message = MIMEText(message_text)
#     message['to'] = to
#     message['from'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
#     message['subject'] = Header(subject, 'utf-8')
#     return {'raw': base64.urlsafe_b64encode(message.as_string())}
#
# def create_html_message(sender_name, sender_email, to, subject, html_message):
#     message = MIMEText(html_message, 'html')
#     message['to'] = to
#     message['from'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
#     message['subject'] = Header(subject, 'utf-8')
#     return {'raw': base64.urlsafe_b64encode(message.as_string())}


def get_email_address(serivce):
    user_profile = serivce.users().getProfile(userId='me').execute()
    return user_profile['emailAddress']

def send_email(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        return message
    except errors.HttpError, error:
        print_log ('An error occured: %s' % error)

    return "ERROR!"

def get_track_html(to_addr):
    sent_time = str(int(time.time()))
    hexlify_png = binascii.hexlify(to_addr + ',' + sent_time) + '.png'
    track_url = "http://jinwensenqusi.ddns.net/" + hexlify_png
    return "<img alt='' src='" + track_url + "'/>"


def create_message_embed_image(sender_name,
                   sender_email,
                   to_addr,
                   subject,
                   message_text,
                   message_html,
                   image_file,
                   add_tracker = True):

    if add_tracker:
        tracker_tag = '{{.TRACKER}}'
        tracker_link = get_track_html(to_addr)
        if message_html.find(tracker_tag) != -1:
            message_html = message_html.replace(tracker_tag, tracker_link)
        else:
            message_html += "\n" + message_html

    msgRoot = MIMEMultipart('related')
    msgRoot['to'] = to_addr
    msgRoot['from'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
    msgRoot['subject'] = Header(subject, 'utf-8')
    msgRoot.preamble = 'This is a multi-part message in MIME format.'

    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText(message_text)
    msgAlternative.attach(msgText)

    msgHtml = MIMEText(message_html, 'html')
    msgAlternative.attach(msgHtml)

    # open images
    fp = open(image_file, 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()

    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)

    return {'raw': base64.urlsafe_b64encode(msgRoot.as_string())}


def create_email_with_href(sender_name,
                               sender_email,
                               to_addr,
                               subject,
                               message_text,
                               message_html,
                               add_tracker = True):

    if add_tracker:
        tracker_tag = '{{.TRACKER}}'
        tracker_link = get_track_html(to_addr)
        if message_html.find(tracker_tag) != -1:
            message_html = message_html.replace(tracker_tag, tracker_link)
        else:
            message_html += "\n" + message_html

    msgHtml = MIMEText(message_html, 'html')
    msgHtml['to'] = to_addr
    msgHtml['from'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
    msgHtml['subject'] = Header(subject, 'utf-8')

    return {'raw': base64.urlsafe_b64encode(msgHtml.as_string())}



def main(embed_image=True):
    email_list = []

    if not os.path.exists(input_email_file):
        if '@' in input_email_file:
            email_list.append(input_email_file)
        else:
            print_log("Error cannot find email file: %s" % input_email_file)
            os.exit(1)
    else:
        for e in open(input_email_file, 'r'):
            if e.find('@') == -1:
                continue
            email_list.append(e.strip())

    random.shuffle(email_list)

    print_log ("Prepare to send to %d emails" % len(email_list))
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    # get user and sender
    sender_email = get_email_address(service)

    import email_content
    idx = 0

    for to_addr in email_list:
        idx += 1

        if embed_image == True:
            if to_addr.endswith('126.com') or to_addr.endswith('163.com'):
                embed_image = False
            else:
                embed_image = True

        if embed_image:
            message = create_message_embed_image(email_content.sender_name, sender_email, to_addr,
                                     email_content.subject,
                                     email_content.message_text,
                                     email_content.message_html,
                                     email_content.image_filename)
        else:
            message = create_email_with_href(email_content.sender_name, sender_email, to_addr,
                                     email_content.subject,
                                     email_content.message_text,
                                     email_content.message_html_href)



        res = send_email(service, "me", message)
        progress = "(%d/%d)" % (idx, len(email_list))
        print_log ("[%s] %s Sent from %s to %s, result: %s\n" % (time.ctime(), progress, sender_email, to_addr, str(res)))

        sleeptime = SLEEP_BETWEEN_EMAILS + random.randint(0, SLEEP_BETWEEN_EMAILS)
        print_log ("Sleep %d seconds" % sleeptime)
        time.sleep(sleeptime)

    log_file.close()


if __name__ == "__main__":
    main()









#金问森出轨