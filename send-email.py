#!/usr/bin/python
"""
Gist: https://gist.github.com/L-fours-gists/3837637
send an email through gmail

Save this script to send-gmail.py,
place the body of the email in email_message.txt,
and then run:

    python send-gmail.py \
            --wait 5 \
            --user me@gmail.com \
            --pass 'my password' \
            --to 'random person <recipient1@example.com>' \
            --to 'other random person <recipient2@example.com>' \
            --subject 'this is the email subject' \
            --body email_message.txt


which means:
    wait 5 minutes
    then send an email from me@gmail.com
    to recipient1@example.com and recipient2@example.com
    with the subject "this is the email subject"
    and the message from email_message.tx


"""

import os
import sys
import optparse
import smtplib
import time

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


def create_message(user, recipients, subject, body):
    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body))
    return msg


def send_mail(user, password, recipients, subject, body):
    msg = create_message(user, recipients, subject, body)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(user, password)
    server.sendmail(user, recipients, msg.as_string())
    server.close()
    print('Sent email to %s' % (', '.join(recipients)))


def parse_args():
    parser = optparse.OptionParser()

    parser.add_option('-u', '--user', dest='user',
                      default=None, help='gmail account')

    parser.add_option('-p', '--pass', dest='password',
                      default=None, help='gmail password')

    parser.add_option('-b', '--body', dest='body',
                      default=None, help='email message txt file')

    parser.add_option('-s', '--subject', dest='subject',
                      default=None, help='email subject')

    parser.add_option('-t', '--to', dest='recipients',
                      action='append', default=[],
                      help='specify a recipient')

    parser.add_option('-w', '--wait', dest='wait',
                      default=None, help='seconds to wait before sending')

    opts, args = parser.parse_args()

    if not opts.user:
        parser.error("specify sender address with --user 'me@gmail.com'")

    if not opts.password:
        parser.error("specify sender's password with --pass 'my password'")

    if not opts.body:
        parser.error('specify a text file with the message text as --body')

    if not opts.subject:
        parser.error("specify a subject with --subject 'my subject'")

    if not opts.recipients:
        parser.error('specify at least one recipient with --to')

    if not opts.body:
        parser.error('specify a message body --body [body.txt|\'Inline message\']')

    return opts

# import friendly
if __name__ == '__main__':
    opts = parse_args()

    if (os.path.exists(opts.body)):
        fp = open(opts.body)
        body = fp.read()
        fp.close()
    else:
        body = opts.body

    if opts.wait is not None:
        now = time.time()
        future = now + (float(opts.wait) * 60.)
        print 'waiting %.2f minutes...' % (float(opts.wait))
        while now < future:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.)
            now = time.time()
        sys.stdout.write('\ndone waiting...\n')

    send_mail(opts.user, opts.password,
              opts.recipients,
              opts.subject, body)
