# mailer.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')

def send_email_logic(to_address, job_title, match, company, url_link):
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Found a job you should consider"
    msg["From"] = SMTP_USER
    msg["To"] = to_address

    
    html = f"""
    <html>
      <body>
        <p>Hello,<br>
           We found this job to be a good fit for your resume with a <strong>{match*100:.0f}%</strong> match.<br><br>
           <strong>{job_title}</strong> at <strong>{company}</strong><br><br>
           Apply link: <a href="{url_link}">Click here to apply</a>
        </p>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

    return f"Email sent to {to_address}"