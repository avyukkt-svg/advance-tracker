import sys
from emailer import Emailer

def test_mail():
    try:
        print("Initializing Emailer...")
        emailer = Emailer()
        
        print("Sending empty email test...")
        emailer._send_empty_email()
        
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_mail()
