"""
Author: Shelley Pham

Script parses Gmail inbox for emails from noreply@collegiatelink.com (TitanLink)
and looks for individuals who signed up for the student organization today. Then,
it sends a message to the individual with their first name in the Subject and
the body.

References: Gmail API documentation
"""

from __future__ import print_function
import httplib2
import os
import re
import time
import base64

from apiclient import discovery
from apiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def ListThreadsMatchingQuery(service, user_id, query=''):
  """List all Threads of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
           Eg.- 'label:UNREAD' for unread messages only.

  Returns:
    List of threads that match the criteria of the query. Note that the returned
    list contains Thread IDs, you must use get with the appropriate
    ID to get the details for a Thread.
  """
  try:
    response = service.users().threads().list(userId=user_id, q=query).execute()
    threads = []
    if 'threads' in response:
      threads.extend(response['threads'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().threads().list(userId=user_id, q=query,
                                        pageToken=page_token).execute()
      threads.extend(response['threads'])

    return threads
  except errors.HttpError, error:
    print ('An error occurred: %s' % error)

def create_message(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEText(message_text, 'html')
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_string())}

def send_message(service, user_id, message):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print ('Message Id: %s' % message['id'])
    return message
  except errors.HttpError, error:
    print ('An error occurred: %s' % error)


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    # Replace this with a txt or html file that includes '%s' to address the receiver
    # e.g. Hello %s! Shows as Hello Bob!
    email_template = open('message_to_send.txt', 'r').read()
    email_collegiatelink = 'noreply@collegiatelink.net'
    date_today = time.strftime("%Y/%m/%d")

    messages = ListThreadsMatchingQuery(service, 'me', 'from:%s newer:%s'%(email_collegiatelink, date_today))
    print("Current date: ", date_today)
    for message in messages:
        first_name = re.compile("(?<=u')(\w+ )")
        first_name = first_name.search(str(message)).group()
        first_name = first_name[:-1]

        csu_email = re.compile("(\w+@csu\.fullerton\.edu)")
        csu_email = csu_email.search(str(message)).group()
        
        """
        Replace this with your email list
        """
        
        email_list = "OSS at CSU Fullerton <csuf.oss@gmail.com>, Shelley Pham <phamshelley@csu.fullerton.edu>, " + csu_email

        email_subject = "[OSS] %s, Thank you for your interest!" % first_name

        email_contents = email_template % first_name
        encoded_message = create_message('Shelley Pham <phamshelley@gmail.com>', email_list, email_subject, email_contents)
        send_message(service, 'me', encoded_message)

        print ("Email sent to ", first_name, csu_email)


if __name__ == '__main__':
    main()
