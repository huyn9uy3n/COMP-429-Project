import socket
import threading
import sys
import ipaddress

# Global variables
connections = {}
lock = threading.Lock()
client_sockets = {}
server_socket = None
server_ready_event = threading.Event()  # Event to signal when the server is ready

# Handles incoming messages from a client
def handle_client(client_socket, addr):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"\nMessage received from {addr[0]}")
                print(f"Sender’s Port: {addr[1]}")
                print(f"Message: “{message}”")
                print("Enter command: ", end="", flush=True)
                broadcast(message, client_socket)
            else:
                break
        except:
            break

    client_socket.close()
    remove_connection(client_socket)

# Sends a message to all connected clients except the sender
def broadcast(message, sender_socket):
    with lock:
        for client in connections:
            if client != sender_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    client.close()
                    remove_connection(client)

# Removes a client from the connections list
def remove_connection(client_socket):
    with lock:
        if client_socket in connections:
            del connections[client_socket]

# Starts the server to listen for incoming connections
def start_server(port):
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen(5)
    print(f"Server listening on port {port}")
    server_ready_event.set()  # Signal that the server is ready

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection established with {addr}")
        connections[client_socket] = addr
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()

# Returns the IP address of the machine
def my_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

# Returns the port on which the server is listening
def my_port():
    return server_socket.getsockname()[1]

# Establishes a new TCP connection to the specified destination
def connect(destination, port):
    try:
        ipaddress.ip_address(destination)  # Validate IP address
        port = int(port)

        # Check if trying to connect to self
        if destination == my_ip() and port == my_port():
            print("Error: Cannot connect to yourself.")
            return

        if (destination, port) in client_sockets.values():
            print("Error: Duplicate connection.")
            return

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((destination, port))
        connections[client_socket] = (destination, port)
        client_sockets[client_socket] = (destination, port)
        print(f"Connected to {destination}:{port}")
        threading.Thread(target=handle_client, args=(client_socket, (destination, port))).start()
    except ValueError:
        print("Error: Invalid IP address.")
    except Exception as e:
        print(f"Error: {e}")

# Displays a list of all active connections
def list_connections():
    if not connections:
        print("No active connections.")
    else:
        print("Active connections:")
        for idx, (sock, addr) in enumerate(connections.items()):
            print(f"{idx + 1}: {addr[0]} {addr[1]}")

# Terminates the specified connection
def terminate(connection_id):
    try:
        connection_id = int(connection_id) - 1
        sock = list(connections.keys())[connection_id]
        sock.close()
        remove_connection(sock)
        print(f"Connection {connection_id + 1} terminated.")
    except (IndexError, ValueError):
        print("Error: Invalid connection ID.")

# Sends a message to the specified connection
def send_message(connection_id, message):
    try:
        connection_id = int(connection_id) - 1
        sock = list(connections.keys())[connection_id]
        sock.send(message.encode('utf-8'))
        print(f"Message sent to connection {connection_id + 1}.")
    except (IndexError, ValueError):
        print("Error: Invalid connection ID.")

# Handles user commands
def command_interface():
    # Wait until the server is ready
    server_ready_event.wait()

    while True:
        command = input("\nEnter command: ").strip().split()
        if not command:
            continue

        cmd = command[0].lower()

        if cmd == "help":
            print("\nAvailable commands:")
            print("help - Display this help message")
            print("myip - Display the IP address of this process")
            print("myport - Display the port on which this process is listening")
            print("connect <destination> <port> - Connect to a peer")
            print("list - List all active connections")
            print("terminate <connection_id> - Terminate a connection")
            print("send <connection_id> <message> - Send a message to a connection")
            print("exit - Close all connections and terminate this process")
        
        elif cmd == "myip":
            print(f"My IP address: {my_ip()}")
        
        elif cmd == "myport":
            print(f"My listening port: {my_port()}")
        
        elif cmd == "connect":
            if len(command) != 3:
                print("Usage: connect <destination> <port>")
            else:
                connect(command[1], command[2])
        
        elif cmd == "list":
            list_connections()
        
        elif cmd == "terminate":
            if len(command) != 2:
                print("Usage: terminate <connection_id>")
            else:
                terminate(command[1])
        
        elif cmd == "send":
            if len(command) < 3:
                print("Usage: send <connection_id> <message>")
            else:
                connection_id = command[1]
                message = ' '.join(command[2:])
                send_message(connection_id, message)
        
        elif cmd == "exit":
            print("Closing all connections...")
            for sock in list(connections.keys()):
                sock.close()
            print("Exiting the chat application.")
            break
        
        else:
            print("Unknown command. Type 'help' for a list of commands.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python chat.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server, args=(port,))
    server_thread.start()
    
    # Start the command interface in the main thread
    command_interface()

if __name__ == "__main__":
    main()