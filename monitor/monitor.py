import time
import requests
import docker
import os

# Get configurations from Environment Variables
APP_URL = os.getenv("APP_URL", "http://sentinel-app:5000/health")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "sentinel-app")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 10))

# Connect to the local Docker daemon
client = docker.from_env()

def check_and_heal():
    print(f"Starting Sentinel Monitor... watching {APP_URL}")
    while True:
        try:
            # Try to ping the application
            response = requests.get(APP_URL, timeout=5)
            if response.status_code == 200:
                print("✅ App is healthy.")
            else:
                print(f"⚠️ App returned status {response.status_code}. Restarting...")
                restart_container()
                
        except requests.exceptions.RequestException as e:
            # If the connection completely fails (e.g., app is dead)
            print("❌ App is DOWN! Connection failed. Restarting...")
            restart_container()
            
        # Wait before checking again
        time.sleep(CHECK_INTERVAL)

def restart_container():
    try:
        # Find the container by name and restart it
        container = client.containers.get(CONTAINER_NAME)
        print(f"🔄 Restarting container '{CONTAINER_NAME}'...")
        container.restart()
        print("✅ Container restarted successfully!")
        # Wait a bit to let the app boot up before checking again
        time.sleep(5)
    except Exception as e:
        print(f"Failed to restart container: {e}")

if __name__ == '__main__':
    check_and_heal()
