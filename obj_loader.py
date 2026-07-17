"""Pythmc - OBJ Model Loader with Part Separation

Loads .obj files with:
- Group/object separation for animation (head, legs, body, etc.)
- MTL material loading
- Texture support
- Per-part rendering for animation

Usage:
    model = OBJModel.load("cow.obj")
    model.draw()  # Draw entire model
    model.draw_part("head")  # Draw just the head
"""

import os
import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame


class OBJMaterial:
    """MTL material definition."""
    def __init__(self, name="default"):
        self.name = name
        self.diffuse = (0.8, 0.8, 0.8)
        self.ambient = (0.2, 0.2, 0.2)
        self.specular = (0.0, 0.0, 0.0)
        self.texture = None
        self.texture_id = None


class OBJMeshPart:
    """A single part of the model (e.g., head, leg, body)."""
    def __init__(self, name="default"):
        self.name = name
        self.vertices = []    # (x, y, z)
        self.normals = []     # (nx, ny, nz)
        self.texcoords = []   # (u, v)
        self.faces = []       # List of face vertex indices
        self.material = None
        self.display_list = None
        self.center = np.array([0.0, 0.0, 0.0])
        self.bounds_min = np.array([0.0, 0.0, 0.0])
        self.bounds_max = np.array([0.0, 0.0, 0.0])
    
    def calculate_bounds(self):
        """Calculate bounding box and center."""
        if self.vertices:
            verts = np.array(self.vertices)
            self.bounds_min = verts.min(axis=0)
            self.bounds_max = verts.max(axis=0)
            self.center = (self.bounds_min + self.bounds_max) / 2


class OBJModel:
    """Full OBJ model with multiple parts."""
    
    def __init__(self):
        self.parts = {}  # name -> OBJMeshPart
        self.materials = {}  # name -> OBJMaterial
        self.textures = {}  # path -> GL texture id
        self.scale = 1.0
        self.center = np.array([0.0, 0.0, 0.0])
    
    @staticmethod
    def load(obj_path, scale=1.0):
        """Load an OBJ file and return an OBJModel."""
        model = OBJModel()
        model.scale = scale
        
        if not os.path.exists(obj_path):
            print(f"OBJ file not found: {obj_path}")
            return model
        
        obj_dir = os.path.dirname(obj_path)
        
        # Parse OBJ file
        current_part = None
        current_material = None
        
        # Global vertex/normal/tc lists (OBJ uses 1-based indexing)
        all_vertices = []
        all_normals = []
        all_texcoords = []
        
        with open(obj_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                key = parts[0]
                
                if key == 'mtllib':
                    # Load material file
                    mtl_path = os.path.join(obj_dir, parts[1])
                    model._load_mtl(mtl_path)
                
                elif key == 'v':
                    # Vertex
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    all_vertices.append((x * scale, y * scale, z * scale))
                
                elif key == 'vn':
                    # Normal
                    nx, ny, nz = float(parts[1]), float(parts[2]), float(parts[3])
                    all_normals.append((nx, ny, nz))
                
                elif key == 'vt':
                    # Texture coordinate
                    u, v = float(parts[1]), float(parts[2])
                    all_texcoords.append((u, v))
                
                elif key == 'g' or key == 'o':
                    # Group or Object - start new part
                    part_name = parts[1] if len(parts) > 1 else "default"
                    # Clean up part name
                    part_name = part_name.lower().replace(' ', '_')
                    current_part = OBJMeshPart(part_name)
                    model.parts[part_name] = current_part
                
                elif key == 'usemtl':
                    # Use material
                    mtl_name = parts[1]
                    current_material = model.materials.get(mtl_name)
                    if current_part:
                        current_part.material = current_material
                
                elif key == 'f':
                    # Face
                    if current_part is None:
                        current_part = OBJMeshPart("default")
                        model.parts["default"] = current_part
                    
                    face_verts = []
                    for vert_str in parts[1:]:
                        indices = vert_str.split('/')
                        v_idx = int(indices[0]) - 1 if indices[0] else 0
                        vt_idx = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else None
                        vn_idx = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else None
                        
                        # Get vertex
                        if 0 <= v_idx < len(all_vertices):
                            v = all_vertices[v_idx]
                        else:
                            v = (0, 0, 0)
                        
                        # Get normal
                        if vn_idx is not None and 0 <= vn_idx < len(all_normals):
                            n = all_normals[vn_idx]
                        else:
                            n = (0, 1, 0)
                        
                        # Get texcoord
                        if vt_idx is not None and 0 <= vt_idx < len(all_texcoords):
                            t = all_texcoords[vt_idx]
                        else:
                            t = (0, 0)
                        
                        # Store in part
                        vert_idx = len(current_part.vertices)
                        current_part.vertices.append(v)
                        current_part.normals.append(n)
                        current_part.texcoords.append(t)
                        face_verts.append(vert_idx)
                    
                    # Triangulate if needed (convert quads to triangles)
                    if len(face_verts) == 3:
                        current_part.faces.append(face_verts)
                    elif len(face_verts) == 4:
                        # Split quad into two triangles
                        current_part.faces.append([face_verts[0], face_verts[1], face_verts[2]])
                        current_part.faces.append([face_verts[0], face_verts[2], face_verts[3]])
                    elif len(face_verts) > 4:
                        # Fan triangulation
                        for i in range(1, len(face_verts) - 1):
                            current_part.faces.append([face_verts[0], face_verts[i], face_verts[i+1]])
        
        # Calculate bounds for each part
        for part in model.parts.values():
            part.calculate_bounds()
        
        # Build display lists
        model._build_display_lists()
        
        print(f"Loaded OBJ: {obj_path}")
        print(f"  Parts: {list(model.parts.keys())}")
        for name, part in model.parts.items():
            print(f"    {name}: {len(part.vertices)} verts, {len(part.faces)} faces")
        
        return model
    
    def _load_mtl(self, mtl_path):
        """Load materials from MTL file."""
        if not os.path.exists(mtl_path):
            return
        
        current_mtl = None
        
        with open(mtl_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                key = parts[0]
                
                if key == 'newmtl':
                    name = parts[1]
                    current_mtl = OBJMaterial(name)
                    self.materials[name] = current_mtl
                
                elif current_mtl:
                    if key == 'Kd':
                        current_mtl.diffuse = (float(parts[1]), float(parts[2]), float(parts[3]))
                    elif key == 'Ka':
                        current_mtl.ambient = (float(parts[1]), float(parts[2]), float(parts[3]))
                    elif key == 'Ks':
                        current_mtl.specular = (float(parts[1]), float(parts[2]), float(parts[3]))
                    elif key == 'map_Kd':
                        # Texture file
                        tex_path = os.path.join(os.path.dirname(mtl_path), parts[1])
                        current_mtl.texture = tex_path
    
    def _load_texture(self, tex_path):
        """Load a texture and return OpenGL texture ID."""
        if tex_path in self.textures:
            return self.textures[tex_path]
        
        if not os.path.exists(tex_path):
            return None
        
        try:
            surface = pygame.image.load(tex_path)
            data = pygame.image.tostring(surface, "RGBA", True)
            w, h = surface.get_size()
            
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
            
            self.textures[tex_path] = tex_id
            return tex_id
        except Exception as e:
            print(f"Failed to load texture {tex_path}: {e}")
            return None
    
    def _build_display_lists(self):
        """Build OpenGL display lists for each part."""
        for name, part in self.parts.items():
            part.display_list = glGenLists(1)
            glNewList(part.display_list, GL_COMPILE)
            
            # Load texture if available
            has_texture = False
            if part.material and part.material.texture:
                tex_id = self._load_texture(part.material.texture)
                if tex_id:
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, tex_id)
                    has_texture = True
            
            # Set material color
            if part.material:
                glColor3f(*part.material.diffuse)
            else:
                glColor3f(0.8, 0.8, 0.8)
            
            # Draw faces
            glBegin(GL_TRIANGLES)
            for face in part.faces:
                for vert_idx in face:
                    if vert_idx < len(part.normals):
                        n = part.normals[vert_idx]
                        glNormal3f(*n)
                    if has_texture and vert_idx < len(part.texcoords):
                        t = part.texcoords[vert_idx]
                        glTexCoord2f(t[0], t[1])
                    if vert_idx < len(part.vertices):
                        v = part.vertices[vert_idx]
                        glVertex3f(*v)
            glEnd()
            
            if has_texture:
                glDisable(GL_TEXTURE_2D)
            
            glEndList()
    
    def draw(self):
        """Draw the entire model."""
        for part in self.parts.values():
            if part.display_list:
                glCallList(part.display_list)
    
    def draw_part(self, part_name):
        """Draw a specific part by name."""
        part = self.parts.get(part_name)
        if part and part.display_list:
            glCallList(part.display_list)
    
    def get_part_names(self):
        """Get list of all part names."""
        return list(self.parts.keys())
    
    def get_part(self, part_name):
        """Get a specific part."""
        return self.parts.get(part_name)
    
    def cleanup(self):
        """Delete display lists and textures."""
        for part in self.parts.values():
            if part.display_list:
                glDeleteLists(part.display_list, 1)
        for tex_id in self.textures.values():
            glDeleteTextures([tex_id])


class MobModelRenderer:
    """Renders mob models with animation support."""
    
    def __init__(self):
        self.models = {}  # mob_type -> OBJModel
    
    def load_model(self, mob_type, obj_path, scale=1.0):
        """Load a model for a mob type."""
        model = OBJModel.load(obj_path, scale)
        self.models[mob_type] = model
        return model
    
    def draw_mob(self, mob_type, pos, rotation, walk_cycle=0, hit_flash=0):
        """Draw a mob with animation."""
        model = self.models.get(mob_type)
        if not model:
            return
        
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        glRotatef(rotation, 0, 1, 0)
        
        # Hurt flash
        if hit_flash > 0 and int(hit_flash * 20) % 2 == 0:
            glColor3f(1, 0.3, 0.3)
        
        # Walk animation for legs
        leg_angle = math.sin(walk_cycle) * 20 if walk_cycle > 0 else 0
        
        # Draw body parts
        for part_name in model.get_part_names():
            glPushMatrix()
            
            # Animate specific parts
            if 'leg' in part_name:
                if 'front' in part_name and 'left' in part_name:
                    glRotatef(leg_angle, 1, 0, 0)
                elif 'front' in part_name and 'right' in part_name:
                    glRotatef(-leg_angle, 1, 0, 0)
                elif 'back' in part_name and 'left' in part_name:
                    glRotatef(-leg_angle, 1, 0, 0)
                elif 'back' in part_name and 'right' in part_name:
                    glRotatef(leg_angle, 1, 0, 0)
            elif 'head' in part_name:
                # Slight head bob
                pass
            
            model.draw_part(part_name)
            glPopMatrix()
        
        glPopMatrix()
    
    def has_model(self, mob_type):
        """Check if a model is loaded for this mob type."""
        return mob_type in self.models


# Global model renderer
mob_renderer = MobModelRenderer()
