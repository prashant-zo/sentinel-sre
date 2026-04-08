import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Sentinel App is running smoothly! 🛡️"

@app.route('/health')
def health_check():
    # The monitor will ping this endpoint to check if the app is alive
    return jsonify({"status": "healthy"}), 200

@app.route('/crash')
def crash():
    # This simulates a fatal error by forcefully exiting the Python process.
    # The monitor will detect this failure later.
    print("CRASH INITIATED! 💥")
    os._exit(1)

if __name__ == '__main__':
    # Run the app on all available IPs on port 5000
    app.run(host='0.0.0.0', port=5000)
