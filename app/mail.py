from flask_mail import Mail, Message

mail = Mail()

def send_msg(subject, recipients, html):
    msg = Message(subject=subject, 
                recipients=recipients,
                html=html)
    mail.send(msg)