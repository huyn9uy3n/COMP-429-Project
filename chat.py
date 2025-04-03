import socket
import threading
import sys
import os

class PeerChat:
    def __init__(self, port):
        self.host = self.get_my_ip()
        self.port = port
        self.connections = []
        self.server_socket = None
        self.running = True
        self.lock = threading.Lock()
        
    def get_my_ip(self):
        """Get the actual IP address of the computer (not localhost)"""
        try:
            # Create a dummy socket to get the IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google's public DNS server
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"  # Fallback to localhost if unable to get IP
    
    def start_server(self):
        """Start the server to listen for incoming connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Server started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
                except OSError:
                    # Socket closed while waiting for connections
                    break
        except Exception as e:
            print(f"Error starting server: {e}")
            self.running = False
    
    def connect_to_peer(self, destination, port_no):
        """Establish a connection to another peer"""
        # Check for self-connection
        if destination == self.host and port_no == self.port:
            print("Error: Cannot connect to self")
            return
        
        # Check for duplicate connection
        for ip, port, _ in self.connections:
            if ip == destination and port == port_no:
                print("Error: Already connected to this peer")
                return
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((destination, port_no))
            
            # No need to add it to connections here, since it's being added in the handle_client function on peer 2 side
            
            print(f"Successfully connected to {destination}:{port_no}")
            
            # Start a thread to listen for messages from this peer
            threading.Thread(target=self.handle_client, args=(client_socket, (destination, port_no))).start()
        except Exception as e:
            print(f"Error connecting to {destination}:{port_no}: {e}")

    def handle_client(self, client_socket, addr):
        """Handle incoming messages from a connected client"""
        with self.lock:
            # Check if already in list to avoid duplicates
            if (addr[0], addr[1]) not in [(ip, port) for ip, port, _ in self.connections]:
                self.connections.append((addr[0], addr[1], client_socket))
                print(f"\nNew connection from {addr[0]}:{addr[1]}")
            self.display_prompt()
        
        try:
            while self.running:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                print(f"\nMessage received from {addr[0]}")
                print(f"Sender's Port: {addr[1]}")
                print(f"Message: \"{data}\"")
                self.display_prompt()
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            with self.lock:
                # Remove the connection when done
                for i, (ip, port, sock) in enumerate(self.connections):
                    if ip == addr[0] and port == addr[1]:
                        self.connections.pop(i)
                        break
                print(f"\nConnection with {addr[0]}:{addr[1]} terminated")
                self.display_prompt()
                client_socket.close()

    
    def list_connections(self):
        """Display all active connections"""
        if not self.connections:
            print("No active connections")
            return
        
        print("id: IP address Port No.")
        for i, (ip, port, _) in enumerate(self.connections, 1):
            print(f"{i}: {ip} {port}")
    
    def terminate_connection(self, connection_id):
        """Terminate a specific connection"""
        try:
            connection_id = int(connection_id) - 1
            if 0 <= connection_id < len(self.connections):
                ip, port, sock = self.connections[connection_id]
                sock.close()
                with self.lock:
                    self.connections.pop(connection_id)
                print(f"Connection {connection_id + 1} terminated")
            else:
                print("Error: Invalid connection ID")
        except ValueError:
            print("Error: Connection ID must be a number")
    
    def send_message(self, connection_id, message):
        """Send a message to a specific connection"""
        try:
            connection_id = int(connection_id) - 1
            if 0 <= connection_id < len(self.connections):
                ip, port, sock = self.connections[connection_id]
                if len(message) > 100:
                    print("Error: Message exceeds 100 characters")
                    return
                
                try:
                    sock.sendall(message.encode('utf-8'))
                    print(f"Message sent to {connection_id + 1}")
                except Exception as e:
                    print(f"Error sending message: {e}")
                    with self.lock:
                        self.connections.pop(connection_id)
            else:
                print("Error: Invalid connection ID")
        except ValueError:
            print("Error: Connection ID must be a number")
    
    def exit_program(self):
        """Close all connections and exit the program"""
        self.running = False
        print("Closing all connections and exiting...")
        
        # Close all client connections
        for _, _, sock in self.connections:
            try:
                sock.close()
            except:
                pass
        
        # Close the server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Clear the connections list
        with self.lock:
            self.connections.clear()
    
    def display_prompt(self):
        """Display the command prompt"""
        print("\nchat> ", end="", flush=True)
    
    def run(self):
        """Main execution loop"""
        # Start the server in a separate thread
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Main command loop
        while self.running:
            self.display_prompt()
            try:
                command = input().strip().split()
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == "help":
                    self.display_help()
                elif cmd == "myip":
                    print(f"My IP address is {self.host}")
                elif cmd == "myport":
                    print(f"My port is {self.port}")
                elif cmd == "connect":
                    if len(command) == 3:
                        self.connect_to_peer(command[1], int(command[2]))
                    else:
                        print("Error: Usage - connect <destination> <port no>")
                elif cmd == "list":
                    self.list_connections()
                elif cmd == "terminate":
                    if len(command) == 2:
                        self.terminate_connection(command[1])
                    else:
                        print("Error: Usage - terminate <connection id>")
                elif cmd == "send":
                    if len(command) >= 3:
                        connection_id = command[1]
                        message = " ".join(command[2:])
                        self.send_message(connection_id, message)
                    else:
                        print("Error: Usage - send <connection id> <message>")
                elif cmd == "exit":
                    self.exit_program()
                    break
                else:
                    print("Error: Unknown command. Type 'help' for available commands.")
            except EOFError:
                self.exit_program()
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def display_help(self):
        """Display help information"""
        print("\nAvailable commands:")
        print("help - Display this help message")
        print("myip - Display the IP address of this process")
        print("myport - Display the port on which this process is listening")
        print("connect <destination> <port no> - Establish a new TCP connection")
        print("list - Display all active connections")
        print("terminate <connection id> - Terminate a specific connection")
        print("send <connection id> <message> - Send a message to a peer")
        print("exit - Close all connections and terminate the process")

def main():
    if len(sys.argv) != 2:
        print("Usage: python chat.py <port>")
        return
    
    try:
        port = int(sys.argv[1])
        if not (0 < port <= 65535):
            raise ValueError
    except ValueError:
        print("Error: Port must be a number between 1 and 65535")
        return
    
    peer_chat = PeerChat(port)
    peer_chat.run()

if __name__ == "__main__":
    main()