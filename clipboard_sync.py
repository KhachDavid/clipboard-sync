import socket
import threading
import pyperclip
import time
import argparse


last_clipboard_content = None


def main(local_ip, remote_ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # create a bi-directional connection
    try:
        sock.bind((local_ip, port))
        sock.listen(1)
        print(f"Listening on {local_ip}:{port} for incoming connections...")
        conn, _ = sock.accept()
        print("Connection established with remote.")

        # threads to receive the clipboard updates
        threading.Thread(target=monitor_clipboard, args=(conn,)).start()
        threading.Thread(target=listen_for_updates, args=(conn,)).start()

    except Exception as e:
        print(f"Failed to bind or connect: {e}")

    while True:
        try:
            print(f"Attempting to connect to {remote_ip}:{port}...")
            sock.connect((remote_ip, port))
            print("Connected to remote computer.")

            # Start threads for sending and receiving clipboard updates
            threading.Thread(target=monitor_clipboard, args=(sock,)).start()
            threading.Thread(target=listen_for_updates, args=(sock,)).start()
            break
        except (ConnectionRefusedError, OSError):
            print("Failed to connect, retrying in 3 seconds...")
            time.sleep(3)
            continue


def listen_for_updates(sock):
    global last_clipboard_content
    while True:
        try:
            # Receive data from the remote computer
            data = sock.recv(4096).decode("utf-8")
            if data and data != last_clipboard_content:
                last_clipboard_content = data
                pyperclip.copy(data)
                print(f"Clipboard updated from remote: {data}")
        except (ConnectionResetError, BrokenPipeError):
            print("Connection lost. Attempting to reconnect...")
            break


def monitor_clipboard(sock):
    global last_clipboard_content
    while True:
        current_content = pyperclip.paste()

        # if the clipboard content has changed, send the new content
        if current_content != last_clipboard_content:
            last_clipboard_content = current_content
            try:
                sock.sendall(current_content.encode("utf-8"))
                print(f"Sent update to remote: {current_content}")
            except (ConnectionResetError, BrokenPipeError):
                print("Connection lost. Attempting to reconnect...")
                break

        time.sleep(0.5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync clipboard between two computers.")
    parser.add_argument("local_ip", help="IP address of this computer.")
    parser.add_argument("remote_ip", help="IP address of the other computer.")
    parser.add_argument("--port", type=int, default=65432, help="Port to use for connection (default: 65432).") # noqa E501
    args = parser.parse_args()

    main(args.local_ip, args.remote_ip, args.port)