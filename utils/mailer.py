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

def get_admin_emails():
    """Helper to get all admin emails from DB and Settings."""
    db = get_db()
    # 1. Get emails from users with admin role
    admins = list(db.users.find({"role": "admin"}, {"email": 1}))
    admin_emails = {admin['email'] for admin in admins if admin.get('email')}
    
    # 2. Get emails from dynamic settings
    settings = db.settings.find_one({"key": "notification_emails"})
    if settings and settings.get('value'):
        extra_emails = [e.strip() for e in settings['value'].split(',') if e.strip()]
        admin_emails.update(extra_emails)
        
    return list(admin_emails)

def notify_admin_booking(booking_data, car_data=None, conflict=False):
    """Notifies all admins about a new booking or conflict."""
    admin_emails = get_admin_emails()
    
    # Fallback only if absolutely no emails found anywhere
    if not admin_emails:
        admin_emails = ["smartmovetransportltd@gmail.com"]

    subject = "⚠️ ALERT: Double Booking on Date" if conflict else f"New Booking: {booking_data.get('client_name')}"
    
    car_name = car_data.get('name', 'N/A') if car_data else 'N/A'
    car_image = car_data.get('image', '') if car_data else ''
    
    conflict_html = f"""
    <div style="background-color: #fee2e2; border: 2px solid #ef4444; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: #991b1b; margin-top: 0;">⚠️ DATE CONFLICT DETECTED</h3>
        <p style="color: #991b1b; font-weight: bold;">NOTICE: 2 users have selected the same booking date ({booking_data.get('booking_date')}) in the system.</p>
        <p style="color: #991b1b;">Please log in to the admin dashboard and consider assigning an external car if your primary fleet is fully booked for this day.</p>
    </div>
    """ if conflict else ""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .container {{ font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; }}
            .header {{ background-color: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ padding: 20px; line-height: 1.6; color: #333; }}
            .car-box {{ background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .car-img {{ width: 100%; max-height: 250px; object-fit: cover; border-radius: 5px; }}
            .details-grid {{ display: grid; grid-template-cols: 1fr 1fr; gap: 10px; margin-top: 15px; }}
            .label {{ font-weight: bold; font-size: 12px; color: #64748b; text-transform: uppercase; }}
            .value {{ font-size: 14px; color: #1e293b; margin-bottom: 8px; }}
            .footer {{ text-align: center; font-size: 11px; color: #94a3b8; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0; font-size: 20px;">Smart Move Admin Alert</h1>
            </div>
            <div class="content">
                {conflict_html}
                <p>A new booking request has been received with the following details:</p>
                
                <div class="car-box">
                    {f'<img src="{car_image}" class="car-img" alt="Car Image" />' if car_image else ''}
                    <h2 style="margin: 10px 0;">{car_name}</h2>
                    <div class="details-grid">
                        <div>
                            <div class="label">Client Name</div>
                            <div class="value">{booking_data.get('client_name')}</div>
                            <div class="label">ID Number</div>
                            <div class="value">{booking_data.get('id_number', 'N/A')}</div>
                            <div class="label">Phone</div>
                            <div class="value">{booking_data.get('client_phone')}</div>
                        </div>
                        <div>
                            <div class="label">Booking Date</div>
                            <div class="value">{booking_data.get('booking_date')}</div>
                            <div class="label">Pickup</div>
                            <div class="value">{booking_data.get('pickup_location')}</div>
                            <div class="label">Total Price</div>
                            <div class="value">RWF {booking_data.get('total_price', 0):,}</div>
                        </div>
                    </div>
                </div>
                
                <p>Please log in to the admin dashboard to manage this booking.</p>
            </div>
            <div class="footer">
                <p>This is an automated operational notification from Smart Move Transport Ltd.</p>
            </div>
        </div>
    </body>
    </html>
    """
    for email in admin_emails:
        send_email_async(email, subject, html_content)

def notify_admin_action(event_type, booking_data):
    """General notification for admin on status updates or deletions."""
    admin_emails = get_admin_emails()
    
    if not admin_emails:
        admin_emails = ["smartmovetransportltd@gmail.com"]

    subject = f"Admin Action: {event_type.replace('_', ' ').capitalize()}"
    
    html_content = f"""
    <div style="font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        <h2 style="color: #3b82f6;">Booking {event_type.capitalize()}</h2>
        <p>A booking has been <strong>{event_type}</strong>.</p>
        <p><strong>Client:</strong> {booking_data.get('client_name')}</p>
        <p><strong>Date:</strong> {booking_data.get('booking_date')}</p>
        <p><strong>Current Status:</strong> {booking_data.get('status', 'N/A')}</p>
        <hr/>
        <p style="font-size: 11px; color: #666;">This is an automated log for administrative records.</p>
    </div>
    """
    for email in admin_emails:
        send_email_async(email, subject, html_content)

def notify_general_update(title, message):
    """General broadcast update for all subscribers."""
    subject = f"Smart Move Update: {title}"
    broadcast_notification(subject, title, message)
