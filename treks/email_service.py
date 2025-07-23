from django.core.mail import send_mail
from django.conf import settings

class EmailService:
    @staticmethod
    def send_sos_alert(user_name, user_lat, user_lon, selected_types, description, alert_id, recipient_emails):
        """Send SOS alert emails to emergency contacts"""
        try:
            subject = f"Trek help application test {user_name}"
            message = (
                f"Test SOS Alert\n\n"
                f"User: {user_name}\n"
                f"Location: https://maps.google.com/?q={user_lat},{user_lon}\n"
                f"Coordinates: {user_lat}, {user_lon}\n"
                f"Emergency Types: {', '.join(selected_types)}\n\n"
                f"{description}\n\n"
                f"⚠️ PLEASE RESPOND IMMEDIATELY ⚠️\n\n"
                f"This is an automated emergency alert from Trek Nepal App.\n"
                f"Alert ID: {alert_id}"
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_emails,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send SOS email: {e}")
            return False