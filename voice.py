"""Pythmc - Voice Chat System

Proximity-based voice chat using UDP:
- Players hear each other based on distance
- Closer = louder, further = quieter
- Mute/unmute support
- Push-to-talk or voice activation
"""

import socket
import threading
import struct
import time
import numpy as np
import pygame.locals
from pygame.locals import *
from network import get_local_ip

# Audio settings
SAMPLE_RATE = 16000  # Lower for network efficiency
CHANNELS = 1
CHUNK_SIZE = 1024  # Samples per chunk
VOICE_PORT = 25566  # Different from game port
MAX_VOICE_DIST = 30.0  # Max distance to hear someone
MIN_VOICE_DIST = 2.0   # Distance for full volume


class VoiceChat:
    """Voice chat system for multiplayer."""
    
    def __init__(self):
        self.enabled = False
        self.muted = False
        self.push_to_talk = True
        self.ptt_key = K_v  # V for push-to-talk
        
        # Network
        self.socket = None
        self.running = False
        self.server_ip = None
        
        # Audio
        self.audio = None
        self.capture_stream = None
        self.playback_stream = None
        
        # Players: {player_id: {"buffer": [], "volume": 0.5}}
        self.other_players = {}
        self.player_lock = threading.Lock()
        
        # My info
        self.player_id = None
        self.player_pos = [0, 0, 0]
        
        # Audio buffers
        self.send_buffer = []
        self.recv_buffers = {}  # player_id -> buffer
        
        self.init_success = False
    
    def init(self, player_id, server_ip=None):
        """Initialize voice chat."""
        self.player_id = player_id
        self.server_ip = server_ip
        
        try:
            import pyaudio
            self.audio = pyaudio.PyAudio()
            
            # Capture stream (microphone)
            self.capture_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            
            # Playback stream (speakers)
            self.playback_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE
            )
            
            # UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)
            
            if server_ip:
                # Client mode - bind to any port
                self.socket.bind(('0.0.0.0', 0))
            else:
                # Server mode - bind to voice port
                self.socket.bind(('0.0.0.0', VOICE_PORT))
            
            self.enabled = True
            self.running = True
            
            # Start threads
            self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
            self.send_thread.start()
            
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()
            
            self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self.playback_thread.start()
            
            self.init_success = True
            print("Voice chat initialized")
            return True
            
        except ImportError:
            print("PyAudio not installed - voice chat disabled")
            return False
        except Exception as e:
            print(f"Voice chat init failed: {e}")
            return False
    
    def stop(self):
        """Stop voice chat."""
        self.running = False
        self.enabled = False
        
        if self.capture_stream:
            try:
                self.capture_stream.stop_stream()
                self.capture_stream.close()
            except:
                pass
        
        if self.playback_stream:
            try:
                self.playback_stream.stop_stream()
                self.playback_stream.close()
            except:
                pass
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
    
    def update_position(self, pos):
        """Update player position for proximity."""
        self.player_pos = list(pos)
    
    def update_other_players(self, players):
        """Update other players' positions."""
        with self.player_lock:
            self.other_players = players
    
    def set_muted(self, muted):
        """Set mute state."""
        self.muted = muted
    
    def is_ptt_pressed(self):
        """Check if push-to-talk key is pressed."""
        if not self.push_to_talk:
            return True
        import pygame
        keys = pygame.key.get_pressed()
        return keys.get(self.ptt_key, False)
    
    def _send_loop(self):
        """Capture and send audio."""
        while self.running and self.enabled:
            try:
                if not self.muted and self.is_ptt_pressed():
                    # Capture audio
                    data = self.capture_stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    
                    # Add header: player_id + position
                    header = struct.pack('3f', *self.player_pos)
                    packet = header + data
                    
                    # Send to server or broadcast
                    if self.server_ip:
                        self.socket.sendto(packet, (self.server_ip, VOICE_PORT))
                    else:
                        # Server - broadcast to all clients
                        with self.player_lock:
                            for player_id, pdata in self.other_players.items():
                                addr = pdata.get("addr")
                                if addr:
                                    self.socket.sendto(packet, addr)
                else:
                    # Still read to prevent buffer buildup
                    try:
                        self.capture_stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    except:
                        pass
                
                time.sleep(CHUNK_SIZE / SAMPLE_RATE * 0.5)
                
            except Exception as e:
                time.sleep(0.1)
    
    def _recv_loop(self):
        """Receive audio from other players."""
        while self.running and self.enabled:
            try:
                ready = select.select([self.socket], [], [], 0.1)
                if ready[0]:
                    data, addr = self.socket.recvfrom(4096)
                    
                    if len(data) > 12:
                        # Parse header
                        pos = struct.unpack('3f', data[:12])
                        audio_data = data[12:]
                        
                        # Calculate volume based on distance
                        dist = self._distance(self.player_pos, pos)
                        volume = self._calc_volume(dist)
                        
                        if volume > 0.01:
                            # Find or create player buffer
                            player_key = addr[0]  # Use IP as key
                            with self.player_lock:
                                if player_key not in self.recv_buffers:
                                    self.recv_buffers[player_key] = []
                                self.recv_buffers[player_key].append((audio_data, volume))
                                
                                # Limit buffer size
                                if len(self.recv_buffers[player_key]) > 10:
                                    self.recv_buffers[player_key].pop(0)
                                    
            except BlockingIOError:
                pass
            except Exception as e:
                time.sleep(0.1)
    
    def _playback_loop(self):
        """Play received audio."""
        while self.running and self.enabled:
            try:
                with self.player_lock:
                    for player_key in list(self.recv_buffers.keys()):
                        if self.recv_buffers[player_key]:
                            audio_data, volume = self.recv_buffers[player_key].pop(0)
                            
                            # Apply volume
                            samples = np.frombuffer(audio_data, dtype=np.int16)
                            samples = (samples * volume).astype(np.int16)
                            
                            # Play
                            self.playback_stream.write(samples.tobytes())
                
                time.sleep(0.01)
                
            except Exception as e:
                time.sleep(0.1)
    
    def _distance(self, pos1, pos2):
        """Calculate distance between two positions."""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        dz = pos1[2] - pos2[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def _calc_volume(self, dist):
        """Calculate volume based on distance."""
        if dist >= MAX_VOICE_DIST:
            return 0.0
        if dist <= MIN_VOICE_DIST:
            return 1.0
        # Linear falloff
        return 1.0 - (dist - MIN_VOICE_DIST) / (MAX_VOICE_DIST - MIN_VOICE_DIST)


# Need import for select
import select
import math

# Global voice chat instance
voice_chat = VoiceChat()
