import http.server
import socketserver
import threading
import logging
from main import main

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WebhookServer")

PORT = 8080

class WebhookHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # We only care about the /run endpoint
        if self.path == '/run':
            # 1. Send an immediate "Success" response so your phone shortcut finishes instantly
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Scanner started in background!")
            
            logger.info("Trigger received from phone! Starting scanner in the background...")
            
            # 2. Run the actual main() function in a background thread 
            # This prevents the phone from waiting several minutes for it to finish
            thread = threading.Thread(target=main)
            thread.start()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found. Use /run to trigger the scanner.")

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), WebhookHandler) as httpd:
        logger.info(f"Server listening on port {PORT}")
        logger.info(f"--> Trigger URL: http://<YOUR_MAC_IP_ADDRESS>:8080/run")
        httpd.serve_forever()
