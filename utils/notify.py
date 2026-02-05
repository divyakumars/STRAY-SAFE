# utils/notify.py - COMPLETE FIXED VERSION

from dotenv import load_dotenv
import os
import datetime as dt
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client

# Load environment variables
load_dotenv()

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")

# SendGrid Configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")

def send_email(to, subject, body):
    """Send email via SendGrid"""

    print(f"\n📧 ========== EMAIL DEBUG ==========")
    print(f"📧 Attempting to send email to: {to}")
    print(f"📧 Subject: {subject}")

    try:
        print(f"📧 Creating email message...")
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to,
            subject=f"SafePaws AI - {subject}",
            html_content=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f8f9fa;">
                <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">🐾 SafePaws AI</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0;">Street Dog Welfare Platform</p>
                </div>
                <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px;">
                    <h2 style="color: #1e293b; margin-top: 0;">{subject}</h2>
                    <div style="color: #475569; line-height: 1.6;">
                        {body}
                    </div>
                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                    <p style="color: #94a3b8; font-size: 13px; margin: 0;">
                        This is an automated message from SafePaws AI. Please do not reply to this email.
                    </p>
                </div>
            </div>
            """
        )

        print(f"📧 Initializing SendGrid client...")
        sg = SendGridAPIClient(SENDGRID_API_KEY)

        print(f"📧 Sending email...")
        response = sg.send(message)

        print(f"📧 Response Status Code: {response.status_code}")

        if response.status_code == 202:
            print(f"✅ EMAIL SENT SUCCESSFULLY to {to}!")
            return True
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            return True

    except Exception as e:
        print(f"❌ EMAIL SENDING FAILED!")
        print(f"❌ Error: {str(e)}")
        return False


def send_sms(to, message):
    """Send SMS via Twilio"""
    print(f"📱 SMS Debug - Attempting to send to: {to}")

    if not TWILIO_SID or TWILIO_SID == "PASTE_YOUR_ACCOUNT_SID_HERE":
        print(f"📱 SMS (demo mode): {to} | {message}")
        return False

    try:
        print(f"✓ Initializing Twilio client...")
        client = Client(TWILIO_SID, TWILIO_TOKEN)

        print(f"✓ Sending SMS...")
        msg = client.messages.create(
            body=f"🐾 SafePaws AI: {message}",
            from_=TWILIO_PHONE,
            to=to
        )

        print(f"✅ SMS sent successfully!")
        print(f"   Message SID: {msg.sid}")
        return True

    except Exception as e:
        print(f"❌ SMS error: {str(e)}")
        return False


def send_inapp_message(from_user, to_user, text, convo_id=None):
    """✅ FIXED: Send in-app message"""
    from utils import storage

    messages = storage.read("messages", [])
    conversations = storage.read("conversations", [])

    # Ensure lists
    if not isinstance(messages, list):
        messages = []
    if not isinstance(conversations, list):
        conversations = []

    # Find or create conversation
    if convo_id:
        conv = next((c for c in conversations if c["id"] == convo_id), None)
    else:
        # Find existing 1:1 conversation
        conv = next((c for c in conversations
                     if not c.get("is_group")
                     and set(c.get("members", [])) == {from_user, to_user}), None)

        if not conv:
            # Create new conversation
            conv = {
                "id": f"C{int(__import__('time').time())}",
                "name": f"{from_user} & {to_user}",
                "is_group": False,
                "members": [from_user, to_user],
                "created_at": str(dt.datetime.now())
            }
            conversations.append(conv)
            storage.write("conversations", conversations)

    # Add message
    if conv and text:
        new_message = {
            "id": f"M{int(__import__('time').time())}-{__import__('uuid').uuid4().hex[:6]}",
            "convo_id": conv["id"],
            "sender": from_user,
            "text": text,
            "time": str(dt.datetime.now()),
            "receipts": {to_user: "unread"}
        }
        messages.append(new_message)
        storage.write("messages", messages)

        print(f"✅ In-app message sent: {from_user} → {to_user}")
        return True

    return False


def set_typing(user, convo_id, is_typing):
    """Set typing indicator (placeholder for future implementation)"""
    pass


def mark_read(convo_id, user):
    """Mark messages as read"""
    from utils import storage

    messages = storage.read("messages", [])
    if not isinstance(messages, list):
        return

    updated = False
    for msg in messages:
        if msg.get("convo_id") == convo_id:
            if "receipts" not in msg:
                msg["receipts"] = {}

            if user not in msg["receipts"] or msg["receipts"][user] != "read":
                msg["receipts"][user] = "read"
                updated = True

    if updated:
        storage.write("messages", messages)
        print(f"✅ Marked messages as read for {user} in conversation {convo_id}")