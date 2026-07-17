"""Pythmc - Multiplayer LAN Networking

Protocol: JSON messages over TCP sockets
Message format: {"type": "...", "data": {...}}\n

Message types:
  - join: Player joining server
  - leave: Player leaving
  - pos: Player position update
  - block: Block change
  - chat: Chat message
  - player_list: Server sends player list
  - world_info: Server sends world seed/info
"""

import socket
import threading
import json
import time
import struct
import select
from constants import *


# Network settings
DEFAULT_PORT = 25565
BUFFER_SIZE = 4096
TICK_RATE = 20  # Updates per second


def get_local_ip():
    """Get the local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def find_servers(timeout=3):
    """Broadcast to find servers on LAN."""
    servers = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        
        # Send broadcast
        msg = json.dumps({"type": "discover"}).encode()
        sock.sendto(msg, ("255.255.255.255", DEFAULT_PORT))
        
        # Collect responses
        start = time.time()
        while time.time() - start < timeout:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                msg = json.loads(data.decode())
                if msg.get("type") == "discover_response":
                    servers.append({
                        "ip": addr[0],
                        "port": msg.get("port", DEFAULT_PORT),
                        "name": msg.get("name", "Unknown"),
                        "players": msg.get("players", 0),
                        "max_players": msg.get("max_players", 8),
                    })
            except socket.timeout:
                break
        sock.close()
    except:
        pass
    return servers


class GameServer:
    """LAN game server."""
    
    def __init__(self, world_name="World", max_players=8):
        self.world_name = world_name
        self.max_players = max_players
        self.port = DEFAULT_PORT
        
        # Players: {addr: {"name": ..., "pos": ..., "socket": ...}}
        self.players = {}
        self.player_lock = threading.Lock()
        
        # Server socket
        self.server_socket = None
        self.running = False
        self.thread = None
        
        # Callbacks for game events
        self.on_block_change = None  # (x, y, z, block_type)
        self.on_player_join = None   # (name, addr)
        self.on_player_leave = None  # (name, addr)
        self.on_chat = None          # (name, message)
        
        # Block changes to broadcast
        self.pending_blocks = []
        self.blocks_lock = threading.Lock()
    
    def start(self):
        """Start the server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(self.max_players)
            self.server_socket.setblocking(False)
            self.running = True
            
            # Start broadcast listener for server discovery
            self.broadcast_thread = threading.Thread(target=self._broadcast_listener, daemon=True)
            self.broadcast_thread.start()
            
            # Start main server loop
            self.thread = threading.Thread(target=self._server_loop, daemon=True)
            self.thread.start()
            
            print(f"Server started on port {self.port}")
            print(f"Local IP: {get_local_ip()}")
            return True
        except Exception as e:
            print(f"Server start failed: {e}")
            return False
    
    def stop(self):
        """Stop the server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Notify all players
        with self.player_lock:
            for addr, player in self.players.items():
                try:
                    self._send_to(player["socket"], {"type": "server_closed"})
                    player["socket"].close()
                except:
                    pass
            self.players.clear()
    
    def _broadcast_listener(self):
        """Listen for server discovery broadcasts."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self.port))
            sock.settimeout(1.0)
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    msg = json.loads(data.decode())
                    if msg.get("type") == "discover":
                        response = json.dumps({
                            "type": "discover_response",
                            "port": self.port,
                            "name": self.world_name,
                            "players": len(self.players),
                            "max_players": self.max_players,
                        }).encode()
                        sock.sendto(response, addr)
                except socket.timeout:
                    continue
                except:
                    pass
            sock.close()
        except:
            pass
    
    def _server_loop(self):
        """Main server loop - accept connections and handle messages."""
        while self.running:
            # Accept new connections
            try:
                client_socket, addr = self.server_socket.accept()
                client_socket.setblocking(False)
                print(f"Connection from {addr}")
            except BlockingIOError:
                pass
            except:
                pass
            
            # Handle existing clients
            with self.player_lock:
                for addr, player in list(self.players.items()):
                    try:
                        ready = select.select([player["socket"]], [], [], 0)
                        if ready[0]:
                            data = player["socket"].recv(BUFFER_SIZE)
                            if data:
                                self._handle_message(addr, data)
                            else:
                                self._remove_player(addr)
                    except (ConnectionResetError, ConnectionAbortedError):
                        self._remove_player(addr)
                    except BlockingIOError:
                        pass
                    except:
                        pass
            
            # Broadcast block changes
            with self.blocks_lock:
                if self.pending_blocks:
                    for addr, player in self.players.items():
                        for block_data in self.pending_blocks:
                            self._send_to(player["socket"], block_data)
                    self.pending_blocks.clear()
            
            time.sleep(1.0 / TICK_RATE)
    
    def _handle_message(self, addr, data):
        """Handle a message from a client."""
        try:
            messages = data.decode().split("\n")
            for msg_str in messages:
                if not msg_str.strip():
                    continue
                msg = json.loads(msg_str)
                msg_type = msg.get("type")
                
                if msg_type == "join":
                    self._handle_join(addr, msg)
                elif msg_type == "pos":
                    self._handle_position(addr, msg)
                elif msg_type == "block":
                    self._handle_block(addr, msg)
                elif msg_type == "chat":
                    self._handle_chat(addr, msg)
        except:
            pass
    
    def _handle_join(self, addr, msg):
        """Handle player join."""
        name = msg.get("name", "Player")
        with self.player_lock:
            if len(self.players) >= self.max_players:
                self._send_to_addr(addr, {"type": "error", "message": "Server full"})
                return
            
            self.players[addr] = {
                "name": name,
                "pos": [0, 100, 0],
                "yaw": 0,
                "pitch": 0,
                "socket": None,  # Will be set from accept
            }
        
        # Send world info
        self._send_to_addr(addr, {
            "type": "world_info",
            "seed": 42,  # TODO: get from actual world
            "name": self.world_name,
        })
        
        # Broadcast player joined
        self._broadcast({
            "type": "player_join",
            "name": name,
            "id": str(addr),
        })
        
        if self.on_player_join:
            self.on_player_join(name, addr)
        
        print(f"{name} joined from {addr}")
    
    def _handle_position(self, addr, msg):
        """Handle player position update."""
        with self.player_lock:
            if addr in self.players:
                self.players[addr]["pos"] = msg.get("pos", [0, 0, 0])
                self.players[addr]["yaw"] = msg.get("yaw", 0)
                self.players[addr]["pitch"] = msg.get("pitch", 0)
        
        # Broadcast to other players
        self._broadcast_except(addr, msg)
    
    def _handle_block(self, addr, msg):
        """Handle block change."""
        # Broadcast to all players
        with self.blocks_lock:
            self.pending_blocks.append(msg)
        
        if self.on_block_change:
            self.on_block_change(
                msg.get("x"), msg.get("y"), msg.get("z"),
                msg.get("block_type")
            )
    
    def _handle_chat(self, addr, msg):
        """Handle chat message."""
        with self.player_lock:
            name = self.players.get(addr, {}).get("name", "Unknown")
        
        chat_msg = {
            "type": "chat",
            "name": name,
            "message": msg.get("message", ""),
        }
        self._broadcast(chat_msg)
        
        if self.on_chat:
            self.on_chat(name, msg.get("message", ""))
    
    def _remove_player(self, addr):
        """Remove a player."""
        with self.player_lock:
            if addr in self.players:
                name = self.players[addr]["name"]
                try:
                    self.players[addr]["socket"].close()
                except:
                    pass
                del self.players[addr]
                
                self._broadcast({
                    "type": "player_leave",
                    "name": name,
                    "id": str(addr),
                })
                
                if self.on_player_leave:
                    self.on_player_leave(name, addr)
                
                print(f"{name} left")
    
    def _send_to(self, sock, msg):
        """Send message to a socket."""
        try:
            data = json.dumps(msg).encode() + b"\n"
            sock.sendall(data)
        except:
            pass
    
    def _send_to_addr(self, addr, msg):
        """Send message to a player by address."""
        with self.player_lock:
            if addr in self.players:
                self._send_to(self.players[addr]["socket"], msg)
    
    def _broadcast(self, msg):
        """Broadcast to all players."""
        with self.player_lock:
            for addr, player in self.players.items():
                self._send_to(player["socket"], msg)
    
    def _broadcast_except(self, exclude_addr, msg):
        """Broadcast to all except one player."""
        with self.player_lock:
            for addr, player in self.players.items():
                if addr != exclude_addr:
                    self._send_to(player["socket"], msg)
    
    def register_client_socket(self, addr, sock):
        """Register a client socket after accept."""
        with self.player_lock:
            if addr in self.players:
                self.players[addr]["socket"] = sock
    
    def get_player_count(self):
        return len(self.players)
    
    def get_players(self):
        with self.player_lock:
            return dict(self.players)


class GameClient:
    """LAN game client."""
    
    def __init__(self, player_name="Player"):
        self.player_name = player_name
        self.socket = None
        self.connected = False
        self.running = False
        self.thread = None
        
        # Other players: {id: {"name": ..., "pos": ..., "yaw": ...}}
        self.other_players = {}
        self.players_lock = threading.Lock()
        
        # Callbacks
        self.on_player_join = None
        self.on_player_leave = None
        self.on_player_pos = None
        self.on_block_change = None
        self.on_chat = None
        self.on_world_info = None
        self.on_error = None
        
        # Message queue for received messages
        self.message_queue = []
        self.queue_lock = threading.Lock()
        
        # Position to send
        self.my_pos = [0, 100, 0]
        self.my_yaw = 0
        self.my_pitch = 0
        self.pos_lock = threading.Lock()
        
        self.send_interval = 1.0 / TICK_RATE
        self.last_send = 0
    
    def connect(self, ip, port=DEFAULT_PORT):
        """Connect to a server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, port))
            self.socket.setblocking(False)
            self.connected = True
            self.running = True
            
            # Send join message
            self._send({
                "type": "join",
                "name": self.player_name,
            })
            
            # Start receive thread
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            print(f"Connected to {ip}:{port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server."""
        self.running = False
        self.connected = False
        if self.socket:
            try:
                self._send({"type": "leave"})
                self.socket.close()
            except:
                pass
    
    def update_position(self, pos, yaw, pitch):
        """Update local player position."""
        with self.pos_lock:
            self.my_pos = list(pos)
            self.my_yaw = yaw
            self.my_pitch = pitch
    
    def send_position(self):
        """Send position to server (called from game loop)."""
        now = time.time()
        if now - self.last_send < self.send_interval:
            return
        self.last_send = now
        
        with self.pos_lock:
            self._send({
                "type": "pos",
                "pos": self.my_pos,
                "yaw": self.my_yaw,
                "pitch": self.my_pitch,
            })
    
    def send_block_change(self, x, y, z, block_type):
        """Send block change to server."""
        self._send({
            "type": "block",
            "x": x, "y": y, "z": z,
            "block_type": block_type,
        })
    
    def send_chat(self, message):
        """Send chat message."""
        self._send({
            "type": "chat",
            "message": message,
        })
    
    def get_other_players(self):
        """Get other players' data."""
        with self.players_lock:
            return dict(self.other_players)
    
    def process_messages(self):
        """Process queued messages (call from main thread)."""
        with self.queue_lock:
            messages = list(self.message_queue)
            self.message_queue.clear()
        
        for msg in messages:
            msg_type = msg.get("type")
            
            if msg_type == "world_info":
                if self.on_world_info:
                    self.on_world_info(msg)
            elif msg_type == "player_join":
                pid = msg.get("id")
                with self.players_lock:
                    self.other_players[pid] = {
                        "name": msg.get("name", "Player"),
                        "pos": [0, 0, 0],
                        "yaw": 0,
                        "pitch": 0,
                    }
                if self.on_player_join:
                    self.on_player_join(msg.get("name"))
            elif msg_type == "player_leave":
                pid = msg.get("id")
                with self.players_lock:
                    if pid in self.other_players:
                        del self.other_players[pid]
                if self.on_player_leave:
                    self.on_player_leave(msg.get("name"))
            elif msg_type == "pos":
                pid = msg.get("id")
                with self.players_lock:
                    if pid in self.other_players:
                        self.other_players[pid]["pos"] = msg.get("pos", [0, 0, 0])
                        self.other_players[pid]["yaw"] = msg.get("yaw", 0)
                        self.other_players[pid]["pitch"] = msg.get("pitch", 0)
                if self.on_player_pos:
                    self.on_player_pos(msg)
            elif msg_type == "block":
                if self.on_block_change:
                    self.on_block_change(
                        msg.get("x"), msg.get("y"), msg.get("z"),
                        msg.get("block_type")
                    )
            elif msg_type == "chat":
                if self.on_chat:
                    self.on_chat(msg.get("name"), msg.get("message"))
            elif msg_type == "error":
                if self.on_error:
                    self.on_error(msg.get("message"))
    
    def _receive_loop(self):
        """Background thread for receiving messages."""
        buffer = ""
        while self.running and self.connected:
            try:
                ready = select.select([self.socket], [], [], 0.1)
                if ready[0]:
                    data = self.socket.recv(BUFFER_SIZE)
                    if data:
                        buffer += data.decode()
                        while "\n" in buffer:
                            msg_str, buffer = buffer.split("\n", 1)
                            if msg_str.strip():
                                try:
                                    msg = json.loads(msg_str)
                                    with self.queue_lock:
                                        self.message_queue.append(msg)
                                except:
                                    pass
                    else:
                        self.connected = False
                        break
            except (ConnectionResetError, ConnectionAbortedError):
                self.connected = False
                break
            except BlockingIOError:
                pass
            except:
                pass
    
    def _send(self, msg):
        """Send message to server."""
        if self.socket and self.connected:
            try:
                data = json.dumps(msg).encode() + b"\n"
                self.socket.sendall(data)
            except:
                self.connected = False


class MultiplayerManager:
    """Manages multiplayer state."""
    
    def __init__(self):
        self.is_host = False
        self.is_client = False
        self.server = None
        self.client = None
        self.player_name = "Player"
        
        # Chat
        self.chat_messages = []
        self.max_chat_messages = 50
        self.chat_open = False
        self.chat_input = ""
    
    def host_game(self, world_name="World", player_name="Player"):
        """Host a new game."""
        self.player_name = player_name
        self.is_host = True
        self.is_client = False
        
        self.server = GameServer(world_name)
        if self.server.start():
            # Also connect as a client
            self.client = GameClient(player_name)
            if self.client.connect("127.0.0.1"):
                self.is_client = True
                return True
            else:
                self.server.stop()
                return False
        return False
    
    def join_game(self, ip, player_name="Player"):
        """Join an existing game."""
        self.player_name = player_name
        self.is_host = False
        self.is_client = True
        
        self.client = GameClient(player_name)
        return self.client.connect(ip)
    
    def stop(self):
        """Stop multiplayer."""
        if self.client:
            self.client.disconnect()
        if self.server:
            self.server.stop()
        self.is_host = False
        self.is_client = False
    
    def update(self, player_pos, player_yaw, player_pitch):
        """Update and sync player position."""
        if self.client and self.client.connected:
            self.client.update_position(player_pos, player_yaw, player_pitch)
            self.client.send_position()
            self.client.process_messages()
    
    def send_block_change(self, x, y, z, block_type):
        """Broadcast block change."""
        if self.client:
            self.client.send_block_change(x, y, z, block_type)
    
    def send_chat(self, message):
        """Send chat message."""
        if self.client:
            self.client.send_chat(message)
            self.add_chat_message(self.player_name, message)
    
    def add_chat_message(self, name, message):
        """Add message to chat history."""
        self.chat_messages.append((name, message))
        if len(self.chat_messages) > self.max_chat_messages:
            self.chat_messages.pop(0)
    
    def get_other_players(self):
        """Get other players for rendering."""
        if self.client:
            return self.client.get_other_players()
        return {}
    
    def is_connected(self):
        return self.client and self.client.connected


# Global multiplayer manager
multiplayer = MultiplayerManager()
