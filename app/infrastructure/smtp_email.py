import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..domain.interfaces import EmailSender
from ..services.logger import get_logger
from ..config.settings import settings

logger = get_logger("infrastructure.smtp")

class SmtpEmailSender(EmailSender):
    """Infrastructure implementation of EmailSender using SMTP."""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD

    def send_overview_email(self, recipient_email: str, subject: str, body: str) -> bool:
        if not all([self.smtp_server, self.smtp_user, self.smtp_password]):
            logger.error("SMTP credentials not fully configured in environment variables.")
            return False

        msg = MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
