"""Utilities for sending email."""

import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import localtime

from wipac_dev_tools import from_environment


TEMPLATE = """{}


This message was sent via an automated system and does not accept replies.
For questions, email help@icecube.wisc.edu.

© WIPAC, University of Wisconsin-Madison
"""


HTML_TEMPLATE = """
<html>
  <head>
    <style>
      .main {{
        margin: 1em 0;
      }}
      footer {{
        font-size: .8rem;
        margin: 3em 0 1em;
      }}
      footer p {{
        margin: .5em 0 0;
      }}
    </style>
  </head>
  <body>
    <header>
      <img alt="IceCube Logo" src="https://res.cloudinary.com/icecube/images/c_scale,w_456,h_120/v1611782268/IC-webheader/IC-webheader.png" srcset="https://res.cloudinary.com/icecube/images/c_scale,w_456,h_120/v1611782268/IC-webheader/IC-webheader.png 1x, https://res.cloudinary.com/icecube/images/c_scale,w_912,h_240/v1611782268/IC-webheader/IC-webheader.png 2x" width="228" height="60" />
    </header>
    <div class="main">
      <h2>{headline}</h2>
      <p>{}</p>
    </div>
    <footer>
      <p>This message was sent via an automated system and does not accept replies.
        For questions, email <a href="mailto:help@icecube.wisc.edu">help@icecube.wisc.edu</a>.
      </p>
      <p class="copyright">© WIPAC, University of Wisconsin-Madison</p>
    </footer>
  </body>
</html>
"""


def send_email(recipient, subject, content, cc=None, headline="IceCube Identity Management", sender=None):
    """
    Send an email message.

    Args:
        recipient (dict|str): Dict with name and email, or just a string email address
        subject (str): Email subject
        content (str): Email content
        cc (str|list): Email CC address(es)
        headline (str): Message headline used in HTML email body
        sender (dict): (optional) Dict with name and email, or just a string email address
    """
    config = from_environment({
        'EMAIL_SENDER': 'no-reply@icecube.wisc.edu',
        'EMAIL_SMTP_SERVER': 'localhost',
        'EMAIL_SMTP_TIMEOUT': 5,  # email should be mostly instant
    })

    if not sender:
        sender = config['EMAIL_SENDER']

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['Date'] = localtime()

    if isinstance(sender, dict):
        if '@' in sender['email']:
            username, domain = sender['email'].split('@')
        else:
            username = sender['email']
            domain = ''
        msg['From'] = Address(sender['name'], username, domain)
    else:
        msg['From'] = sender

    if isinstance(recipient, dict):
        if '@' in recipient['email']:
            username, domain = recipient['email'].split('@')
        else:
            username = recipient['email']
            domain = ''
        msg['To'] = (Address(recipient['name'], username, domain),)
    else:
        msg['To'] = recipient

    if cc:
        msg['CC'] = cc

    msg.set_content(TEMPLATE.format(content))
    msg.add_alternative(HTML_TEMPLATE.format(content.replace('\n', '<br>'), headline=headline),
                        subtype='html')

    with smtplib.SMTP(config['EMAIL_SMTP_SERVER'], timeout=config['EMAIL_SMTP_TIMEOUT']) as s:
        s.send_message(msg)
