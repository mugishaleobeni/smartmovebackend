import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    return client.get_database('smart_move_transport')

def send_email_async(to_email, subject, html_content):
    """Sends an individual email in the background."""
    def send():
        try:
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_port = int(os.getenv("SMTP_PORT", 587))
            smtp_user = os.getenv("SMTP_USER")
            smtp_pass = os.getenv("SMTP_PASS")
            sender_name = os.getenv("MAIL_DEFAULT_SENDER", "Smart Move Transport")

            if not all([smtp_server, smtp_user, smtp_pass]):
                print("Mailer Error: SMTP configuration is incomplete.")
                return

            msg = MIMEMultipart()
            msg['From'] = sender_name
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")

    thread = threading.Thread(target=send)
    thread.start()

def broadcast_notification(subject, title, message, cta_text="View Fleet", cta_url="https://smartmovetransport.pages.dev/cars"):
    """Broadcasts a notification to all newsletter subscribers."""
    db = get_db()
    subscribers = list(db.subscribers.find({}, {"email": 1}))
    
    if not subscribers:
        print("No subscribers found. Skipping broadcast.")
        return

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .container {{ font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 24px; font-weight: bold; color: #3b82f6; text-transform: uppercase; letter-spacing: 2px; }}
            .content {{ line-height: 1.6; color: #333; }}
            .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 20px; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">Smart Move Transport</div>
            </div>
            <div class="content">
                <h2 style="color: #1f2937;">{title}</h2>
                <p>{message}</p>
                <a href="{cta_url}" class="button">{cta_text}</a>
            </div>
            <div class="footer">
                <p>&copy; 2024 Smart Move Transport. All rights reserved.</p>
                <p>You are receiving this because you subscribed to our newsletter.</p>
            </div>
        </div>
    </body>
    </html>
    """

    for sub in subscribers:
        send_email_async(sub['email'], subject, html_template)

def notify_new_car(car_name, car_type):
    subject = f"New Arrival: {car_name} is now available!"
    title = "New Vehicle Added to Our Fleet"
    message = f"We are excited to announce that a new <strong>{car_name}</strong> ({car_type}) has joined our fleet. It is fully maintained and ready for your next journey in Rwanda."
    broadcast_notification(subject, title, message)

def notify_price_change(car_name, new_price):
    subject = f"Price Update: New rates for {car_name}"
    title = "Updated Rental Rates"
    message = f"We have updated our rental rates for the <strong>{car_name}</strong>. You can now book it for as low as <strong>RWF {new_price}</strong> per day. Check out the new deals on our website!"
    broadcast_notification(subject, title, message)

def notify_general_update(title, update_message):
    subject = f"Smart Move Update: {title}"
    broadcast_notification(subject, title, update_message)
