HOW TO RUN:
python chat.py <port number>

CONTRIBUTION:

David Nguyen-----------------------------------------------------------------------
*Implement the Server Logic
start_server(port): Create and bind the server socket, listen for connections, and handle incoming client sockets.
Use server_ready_event to signal the server is up.

*Handle Client Connections and Broadcasting
handle_client(client_socket, addr): Receive messages from connected clients and invoke broadcasting.
broadcast(message, sender_socket): Relay messages to all clients except the sender.

*Manage Connections
remove_connection(client_socket): Clean up when clients disconnect.
Shared access to the connections dictionary using lock.

*Exit & Graceful Shutdown
exit logic in the command_interface(): Close all sockets, stop server, and exit the program.

Nam Vu----------------------------------------------------------------------------
*User Command Interface
command_interface(): Handle input from users and route to appropriate functions.

*Connection & Messaging
connect(destination, port): Initiate connection to a peer and handle validation.
send_message(connection_id, message): Send direct messages to peers.
terminate(connection_id): Terminate an individual connection.

*Utility Commands
my_ip() and my_port(): Display IP address and port.
list_connections(): List all active connections.
help: Provide a list of valid commands.