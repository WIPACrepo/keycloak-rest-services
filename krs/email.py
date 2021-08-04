"""Utilities for sending email."""

import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid


TEMPLATE = """
IceCube Identity Management

{}


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
      <img alt="IceCube" src="https://res.cloudinary.com/icecube/images/c_scale,w_456,h_120/v1611782268/IC-webheader/IC-webheader.png" srcset="https://res.cloudinary.com/icecube/images/c_scale,w_456,h_120/v1611782268/IC-webheader/IC-webheader.png 1x, https://res.cloudinary.com/icecube/images/c_scale,w_912,h_240/v1611782268/IC-webheader/IC-webheader.png 2x" width="228" height="60" />
    </header>
    <div class="main">
      <h2>IceCube Identity Management</h2>
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


def send_email(recipient, subject, content, sender='no-reply@icecube.wisc.edu'):
    msg = EmailMessage()
    msg['Subject'] = subject

    if isinstance(sender, dict):
        username, domain = sender['email'].split('@')
        msg['From'] = Address(sender['name'], username, domain)
    else:
        msg['From'] = sender

    if isinstance(recipient, dict):
        username, domain = recipient['email'].split('@')
        msg['To'] = (Address(recipient['name'], username, domain),)
    else:
        msg['To'] = recipient

    msg.set_content(TEMPLATE.format(content))
    msg.add_alternative(HTML_TEMPLATE.format(content.replace('\n','<br>')),
                        subtype='html')

    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)
