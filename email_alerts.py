import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 📧 Update these
SENDER_EMAIL = "nwhat520@gmail.com"
APP_PASSWORD = "dqwr yqdb lfyj ourm"
RECEIVER_EMAIL = "sandri080806@gmail.com"

def send_email_alert(event_type, confidence=None):
    subject = f"[Suraksha Alert] {event_type.upper()} Detected"
    body = f"""
    Alert Type: {event_type.capitalize()}
    Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Confidence: {confidence if confidence else 'N/A'}
    """

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email alert sent successfully!")
    except Exception as e:
        print("❌ Failed to send email:", str(e))
