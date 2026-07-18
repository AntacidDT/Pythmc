"""Pythmc - Multiplayer Menu Screens (V2.7)"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
import time
from constants import *
from text_renderer import text_renderer
from network import multiplayer, find_servers, get_local_ip
from ui import Button, draw_panel, draw_separator, draw_title


class HostGameScreen:
    """Screen to host a new multiplayer game."""
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.time = 0
        self.result = None
        self.world_name = "Pythmc World"
        self.player_name = "Player"
        self.typing = None  # "world" or "player"
        self.status = ""
        
        cx = screen_w // 2
        self.host_btn = Button(cx - 150, 50, 140, 45, "Host Game", (0.2, 0.55, 0.2), (0.3, 0.75, 0.3))
        self.back_btn = Button(cx + 10, 50, 140, 45, "Back", (0.4, 0.2, 0.2), (0.6, 0.3, 0.3))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            my = self.screen_h - my
            cx = self.screen_w // 2
            
            # Text fields
            if cx - 150 <= mx <= cx + 150:
                if 200 <= my <= 230:
                    self.typing = "world"
                    return None
                elif 280 <= my <= 310:
                    self.typing = "player"
                    return None
            
            self.typing = None
            
            if self.host_btn.contains(mx, my):
                if self.world_name.strip() and self.player_name.strip():
                    return {"action": "host", "world_name": self.world_name, "player_name": self.player_name}
            elif self.back_btn.contains(mx, my):
                return "back"
        
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return "back"
            elif event.key == K_RETURN:
                self.typing = None
            elif event.key == K_BACKSPACE:
                if self.typing == "world":
                    self.world_name = self.world_name[:-1]
                elif self.typing == "player":
                    self.player_name = self.player_name[:-1]
            elif event.unicode and self.typing:
                if self.typing == "world" and len(self.world_name) < 30:
                    self.world_name += event.unicode
                elif self.typing == "player" and len(self.player_name) < 20:
                    self.player_name += event.unicode
        return None

    def update(self, dt, mouse_pos):
        self.time += dt
        mx, my = mouse_pos
        my = self.screen_h - my
        self.host_btn.hovered = self.host_btn.contains(mx, my)
        self.back_btn.hovered = self.back_btn.contains(mx, my)

    def draw(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_w, 0, self.screen_h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Background
        glBegin(GL_QUADS)
        glColor3f(0.05, 0.05, 0.1)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glColor3f(0.08, 0.1, 0.15)
        glVertex2f(self.screen_w, self.screen_h)
        glVertex2f(0, self.screen_h)
        glEnd()

        cx = self.screen_w // 2

        # Title
        text_renderer.draw_text_centered_shadow(cx, self.screen_h - 80, "HOST GAME", 
                                                "title", (0.3, 0.9, 0.3), (0.0, 0.2, 0.0))
        
        # Local IP
        ip = get_local_ip()
        text_renderer.draw_text_centered(cx, self.screen_h - 120, 
                                        f"Your IP: {ip}", "medium", (0.7, 0.7, 0.8))

        # World name field
        text_renderer.draw_text(cx - 150, 235, "World Name:", "small", (0.7, 0.7, 0.7))
        glColor4f(0.1, 0.1, 0.15, 0.9)
        self._draw_rect(cx - 150, 200, 300, 30)
        if self.typing == "world":
            glColor4f(0.3, 0.5, 0.7, 0.8)
        else:
            glColor4f(0.2, 0.2, 0.3, 0.6)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx - 150, 200)
        glVertex2f(cx + 150, 200)
        glVertex2f(cx + 150, 230)
        glVertex2f(cx - 150, 230)
        glEnd()
        name_display = self.world_name + ("_" if self.typing == "world" and int(self.time * 2) % 2 == 0 else "")
        text_renderer.draw_text(cx - 145, 205, name_display, "medium", (1, 1, 1))

        # Player name field
        text_renderer.draw_text(cx - 150, 315, "Your Name:", "small", (0.7, 0.7, 0.7))
        glColor4f(0.1, 0.1, 0.15, 0.9)
        self._draw_rect(cx - 150, 280, 300, 30)
        if self.typing == "player":
            glColor4f(0.3, 0.5, 0.7, 0.8)
        else:
            glColor4f(0.2, 0.2, 0.3, 0.6)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx - 150, 280)
        glVertex2f(cx + 150, 280)
        glVertex2f(cx + 150, 310)
        glVertex2f(cx - 150, 310)
        glEnd()
        player_display = self.player_name + ("_" if self.typing == "player" and int(self.time * 2) % 2 == 0 else "")
        text_renderer.draw_text(cx - 145, 285, player_display, "medium", (1, 1, 1))

        # Status
        if self.status:
            text_renderer.draw_text_centered(cx, 150, self.status, "medium", (1, 0.8, 0.3))

        glDisable(GL_BLEND)

        # Buttons
        self.host_btn.draw()
        self.back_btn.draw()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

    def _draw_rect(self, x, y, w, h):
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()


class JoinGameScreen:
    """Screen to join an existing game."""
    
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.time = 0
        self.result = None
        self.ip_address = ""
        self.player_name = "Player"
        self.typing = None
        self.servers = []
        self.scanning = False
        self.scan_timer = 0
        
        cx = screen_w // 2
        self.join_btn = Button(cx - 150, 50, 140, 45, "Join Game", (0.2, 0.55, 0.2), (0.3, 0.75, 0.3))
        self.scan_btn = Button(cx + 10, 50, 140, 45, "Scan LAN", (0.25, 0.35, 0.55), (0.35, 0.5, 0.7))
        self.back_btn = Button(cx - 75, 0, 150, 40, "Back", (0.4, 0.2, 0.2), (0.6, 0.3, 0.3))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            my = self.screen_h - my
            cx = self.screen_w // 2
            
            # Text fields
            if cx - 150 <= mx <= cx + 150:
                if 260 <= my <= 290:
                    self.typing = "ip"
                    return None
                elif 340 <= my <= 370:
                    self.typing = "name"
                    return None
            
            # Server list click
            server_y = 400
            for i, server in enumerate(self.servers):
                if server_y <= my <= server_y + 40 and cx - 200 <= mx <= cx + 200:
                    self.ip_address = server["ip"]
                    return None
                server_y += 45
            
            self.typing = None
            
            if self.join_btn.contains(mx, my):
                if self.ip_address.strip() and self.player_name.strip():
                    return {"action": "join", "ip": self.ip_address, "player_name": self.player_name}
            elif self.scan_btn.contains(mx, my):
                self.scanning = True
                self.scan_timer = 0
                self.servers = []
            elif self.back_btn.contains(mx, my):
                return "back"
        
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return "back"
            elif event.key == K_RETURN:
                self.typing = None
            elif event.key == K_BACKSPACE:
                if self.typing == "ip":
                    self.ip_address = self.ip_address[:-1]
                elif self.typing == "name":
                    self.player_name = self.player_name[:-1]
            elif event.unicode and self.typing:
                if self.typing == "ip" and len(self.ip_address) < 30:
                    self.ip_address += event.unicode
                elif self.typing == "name" and len(self.player_name) < 20:
                    self.player_name += event.unicode
        return None

    def update(self, dt, mouse_pos):
        self.time += dt
        mx, my = mouse_pos
        my = self.screen_h - my
        self.join_btn.hovered = self.join_btn.contains(mx, my)
        self.scan_btn.hovered = self.scan_btn.contains(mx, my)
        self.back_btn.hovered = self.back_btn.contains(mx, my)
        
        # Scan for servers
        if self.scanning:
            self.scan_timer += dt
            if self.scan_timer >= 3.5:
                self.scanning = False

    def draw(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_w, 0, self.screen_h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Background
        glBegin(GL_QUADS)
        glColor3f(0.05, 0.05, 0.1)
        glVertex2f(0, 0)
        glVertex2f(self.screen_w, 0)
        glColor3f(0.08, 0.1, 0.15)
        glVertex2f(self.screen_w, self.screen_h)
        glVertex2f(0, self.screen_h)
        glEnd()

        cx = self.screen_w // 2

        # Title
        text_renderer.draw_text_centered_shadow(cx, self.screen_h - 80, "JOIN GAME", 
                                                "title", (0.3, 0.7, 0.9), (0.0, 0.2, 0.3))

        # IP field
        text_renderer.draw_text(cx - 150, 295, "Server IP:", "small", (0.7, 0.7, 0.7))
        glColor4f(0.1, 0.1, 0.15, 0.9)
        self._draw_rect(cx - 150, 260, 300, 30)
        if self.typing == "ip":
            glColor4f(0.3, 0.5, 0.7, 0.8)
        else:
            glColor4f(0.2, 0.2, 0.3, 0.6)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx - 150, 260)
        glVertex2f(cx + 150, 260)
        glVertex2f(cx + 150, 290)
        glVertex2f(cx - 150, 290)
        glEnd()
        ip_display = self.ip_address + ("_" if self.typing == "ip" and int(self.time * 2) % 2 == 0 else "")
        text_renderer.draw_text(cx - 145, 265, ip_display, "medium", (1, 1, 1))

        # Player name field
        text_renderer.draw_text(cx - 150, 375, "Your Name:", "small", (0.7, 0.7, 0.7))
        glColor4f(0.1, 0.1, 0.15, 0.9)
        self._draw_rect(cx - 150, 340, 300, 30)
        if self.typing == "name":
            glColor4f(0.3, 0.5, 0.7, 0.8)
        else:
            glColor4f(0.2, 0.2, 0.3, 0.6)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx - 150, 340)
        glVertex2f(cx + 150, 340)
        glVertex2f(cx + 150, 370)
        glVertex2f(cx - 150, 370)
        glEnd()
        name_display = self.player_name + ("_" if self.typing == "name" and int(self.time * 2) % 2 == 0 else "")
        text_renderer.draw_text(cx - 145, 345, name_display, "medium", (1, 1, 1))

        # Server list
        text_renderer.draw_text(cx - 200, 430, "Servers on LAN:", "small", (0.6, 0.6, 0.6))
        
        if self.scanning:
            text_renderer.draw_text_centered(cx, 460, "Scanning...", "medium", (1, 1, 0.5))
        elif self.servers:
            sy = 460
            for server in self.servers:
                glColor4f(0.12, 0.12, 0.16, 0.8)
                self._draw_rect(cx - 200, sy, 400, 35)
                text_renderer.draw_text(cx - 190, sy + 10, server["name"], "medium", (1, 1, 1))
                text_renderer.draw_text(cx + 50, sy + 10, f"{server['ip']} ({server['players']}/{server['max_players']})", 
                                       "small", (0.6, 0.6, 0.6))
                sy += 45
        else:
            text_renderer.draw_text_centered(cx, 460, "Click 'Scan LAN' to find servers", "small", (0.5, 0.5, 0.5))

        glDisable(GL_BLEND)

        # Buttons
        self.join_btn.draw()
        self.scan_btn.draw()
        self.back_btn.draw()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

    def _draw_rect(self, x, y, w, h):
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()
