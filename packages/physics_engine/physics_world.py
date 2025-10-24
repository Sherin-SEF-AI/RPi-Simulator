"""
Physics World - 2D/3D physics simulation for embedded systems
"""

import numpy as np
import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class CollisionShape(Enum):
    """Collision shape types"""
    SPHERE = "sphere"
    BOX = "box"
    CYLINDER = "cylinder"
    PLANE = "plane"
    MESH = "mesh"


@dataclass
class Vector3:
    """3D vector for physics calculations"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return Vector3(self.x/mag, self.y/mag, self.z/mag)
        return Vector3(0, 0, 0)
    
    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other):
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )


@dataclass
class CollisionInfo:
    """Collision detection result"""
    collided: bool
    distance: float
    normal: Vector3
    contact_point: Vector3


class PhysicsObject:
    """Base physics object with position, velocity, and forces"""
    
    def __init__(self, position: Vector3, mass: float = 1.0):
        self.position = position
        self.velocity = Vector3()
        self.acceleration = Vector3()
        self.mass = mass
        self.forces = Vector3()
        
        # Rotation (simplified quaternion as euler angles)
        self.rotation = Vector3()  # Roll, Pitch, Yaw in radians
        self.angular_velocity = Vector3()
        self.angular_acceleration = Vector3()
        self.torque = Vector3()
        
        # Physical properties
        self.friction = 0.1
        self.restitution = 0.5  # Bounciness
        self.drag = 0.01
        
        # Collision shape
        self.collision_shape = CollisionShape.SPHERE
        self.collision_radius = 0.1  # meters
        self.collision_size = Vector3(0.1, 0.1, 0.1)  # For box shapes
        
    def apply_force(self, force: Vector3) -> None:
        """Apply force to object"""
        self.forces = self.forces + force
        
    def apply_torque(self, torque: Vector3) -> None:
        """Apply torque to object"""
        self.torque = self.torque + torque
        
    def update(self, dt: float) -> None:
        """Update physics simulation step"""
        # Linear motion (F = ma)
        if self.mass > 0:
            self.acceleration = self.forces * (1.0 / self.mass)
        
        # Apply drag
        drag_force = self.velocity * (-self.drag)
        self.acceleration = self.acceleration + drag_force
        
        # Integrate velocity and position
        self.velocity = self.velocity + self.acceleration * dt
        self.position = self.position + self.velocity * dt
        
        # Angular motion (simplified)
        if self.mass > 0:
            # Moment of inertia (simplified as point mass)
            inertia = self.mass * 0.1  # Simplified
            self.angular_acceleration = self.torque * (1.0 / inertia)
            
        # Integrate angular velocity and rotation
        self.angular_velocity = self.angular_velocity + self.angular_acceleration * dt
        self.rotation = self.rotation + self.angular_velocity * dt
        
        # Clear forces for next frame
        self.forces = Vector3()
        self.torque = Vector3()


class PhysicsWorld:
    """
    Physics simulation world for embedded systems
    Handles collision detection, rigid body dynamics, and sensor simulation
    """
    
    def __init__(self, gravity: Vector3 = Vector3(0, 0, -9.81)):
        self.gravity = gravity
        self.objects: List[PhysicsObject] = []
        self.time = 0.0
        self.timestep = 1.0 / 60.0  # 60 FPS physics
        
        # Environment properties
        self.air_density = 1.225  # kg/m³ at sea level
        self.sound_speed = 343.0  # m/s at 20°C
        self.light_speed = 299792458.0  # m/s
        
        # Collision detection
        self.collision_pairs: List[Tuple[int, int]] = []
        
    def add_object(self, obj: PhysicsObject) -> int:
        """Add physics object to world"""
        self.objects.append(obj)
        return len(self.objects) - 1
        
    def remove_object(self, obj_id: int) -> bool:
        """Remove physics object from world"""
        if 0 <= obj_id < len(self.objects):
            del self.objects[obj_id]
            return True
        return False
        
    def step(self, dt: Optional[float] = None) -> None:
        """Advance physics simulation by one timestep"""
        if dt is None:
            dt = self.timestep
            
        # Apply gravity to all objects
        for obj in self.objects:
            if obj.mass > 0:
                gravity_force = self.gravity * obj.mass
                obj.apply_force(gravity_force)
                
        # Update all objects
        for obj in self.objects:
            obj.update(dt)
            
        # Collision detection and response
        self._detect_collisions()
        self._resolve_collisions()
        
        self.time += dt
        
    def _detect_collisions(self) -> None:
        """Detect collisions between objects"""
        self.collision_pairs.clear()
        
        for i in range(len(self.objects)):
            for j in range(i + 1, len(self.objects)):
                obj1 = self.objects[i]
                obj2 = self.objects[j]
                
                collision = self._check_collision(obj1, obj2)
                if collision.collided:
                    self.collision_pairs.append((i, j))
                    
    def _check_collision(self, obj1: PhysicsObject, obj2: PhysicsObject) -> CollisionInfo:
        """Check collision between two objects"""
        # Simplified sphere-sphere collision
        if (obj1.collision_shape == CollisionShape.SPHERE and 
            obj2.collision_shape == CollisionShape.SPHERE):
            
            distance_vec = obj2.position - obj1.position
            distance = distance_vec.magnitude()
            
            collision_distance = obj1.collision_radius + obj2.collision_radius
            
            if distance < collision_distance:
                normal = distance_vec.normalize()
                contact_point = obj1.position + normal * obj1.collision_radius
                
                return CollisionInfo(
                    collided=True,
                    distance=collision_distance - distance,
                    normal=normal,
                    contact_point=contact_point
                )
                
        return CollisionInfo(False, 0, Vector3(), Vector3())
        
    def _resolve_collisions(self) -> None:
        """Resolve detected collisions"""
        for i, j in self.collision_pairs:
            obj1 = self.objects[i]
            obj2 = self.objects[j]
            
            collision = self._check_collision(obj1, obj2)
            if not collision.collided:
                continue
                
            # Separate objects
            separation = collision.normal * (collision.distance / 2)
            obj1.position = obj1.position - separation
            obj2.position = obj2.position + separation
            
            # Calculate collision response
            relative_velocity = obj2.velocity - obj1.velocity
            velocity_along_normal = relative_velocity.dot(collision.normal)
            
            # Don't resolve if velocities are separating
            if velocity_along_normal > 0:
                continue
                
            # Calculate restitution
            e = min(obj1.restitution, obj2.restitution)
            
            # Calculate impulse scalar
            j = -(1 + e) * velocity_along_normal
            j /= (1/obj1.mass + 1/obj2.mass)
            
            # Apply impulse
            impulse = collision.normal * j
            obj1.velocity = obj1.velocity - impulse * (1/obj1.mass)
            obj2.velocity = obj2.velocity + impulse * (1/obj2.mass)
            
    def raycast(self, origin: Vector3, direction: Vector3, max_distance: float = 100.0) -> Optional[Dict[str, Any]]:
        """
        Cast a ray and return first intersection
        Used for ultrasonic sensors, lidar, etc.
        """
        direction = direction.normalize()
        closest_hit = None
        closest_distance = max_distance
        
        for i, obj in enumerate(self.objects):
            hit_info = self._ray_object_intersection(origin, direction, obj)
            
            if hit_info and hit_info["distance"] < closest_distance:
                closest_distance = hit_info["distance"]
                closest_hit = {
                    "object_id": i,
                    "distance": hit_info["distance"],
                    "point": hit_info["point"],
                    "normal": hit_info["normal"]
                }
                
        return closest_hit
        
    def _ray_object_intersection(self, origin: Vector3, direction: Vector3, 
                               obj: PhysicsObject) -> Optional[Dict[str, Any]]:
        """Check ray intersection with object"""
        if obj.collision_shape == CollisionShape.SPHERE:
            return self._ray_sphere_intersection(origin, direction, obj)
        elif obj.collision_shape == CollisionShape.PLANE:
            return self._ray_plane_intersection(origin, direction, obj)
        return None
        
    def _ray_sphere_intersection(self, origin: Vector3, direction: Vector3,
                               sphere: PhysicsObject) -> Optional[Dict[str, Any]]:
        """Ray-sphere intersection test"""
        oc = origin - sphere.position
        a = direction.dot(direction)
        b = 2.0 * oc.dot(direction)
        c = oc.dot(oc) - sphere.collision_radius * sphere.collision_radius
        
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None
            
        # Find closest intersection
        sqrt_discriminant = math.sqrt(discriminant)
        t1 = (-b - sqrt_discriminant) / (2 * a)
        t2 = (-b + sqrt_discriminant) / (2 * a)
        
        t = t1 if t1 > 0 else t2
        if t <= 0:
            return None
            
        hit_point = origin + direction * t
        normal = (hit_point - sphere.position).normalize()
        
        return {
            "distance": t,
            "point": hit_point,
            "normal": normal
        }
        
    def _ray_plane_intersection(self, origin: Vector3, direction: Vector3,
                              plane: PhysicsObject) -> Optional[Dict[str, Any]]:
        """Ray-plane intersection test"""
        # Assume plane normal is (0, 0, 1) and positioned at plane.position.z
        plane_normal = Vector3(0, 0, 1)
        
        denom = direction.dot(plane_normal)
        if abs(denom) < 1e-6:
            return None  # Ray parallel to plane
            
        t = (plane.position.z - origin.z) / direction.z
        if t <= 0:
            return None
            
        hit_point = origin + direction * t
        
        return {
            "distance": t,
            "point": hit_point,
            "normal": plane_normal
        }
        
    def calculate_sound_travel_time(self, distance: float, temperature: float = 20.0) -> float:
        """Calculate sound travel time for ultrasonic sensors"""
        # Speed of sound varies with temperature
        speed = 331.3 + (0.606 * temperature)  # m/s
        return distance / speed
        
    def calculate_light_intensity(self, source_pos: Vector3, target_pos: Vector3,
                                source_power: float) -> float:
        """Calculate light intensity for optical sensors"""
        distance = (target_pos - source_pos).magnitude()
        if distance == 0:
            return source_power
            
        # Inverse square law
        intensity = source_power / (4 * math.pi * distance * distance)
        return max(0, intensity)
        
    def simulate_imu_reading(self, obj: PhysicsObject) -> Dict[str, Vector3]:
        """Simulate IMU readings for an object"""
        # Accelerometer: measures proper acceleration (gravity + motion)
        accel = obj.acceleration + Vector3(0, 0, 9.81)  # Add gravity back
        
        # Apply rotation to get body-frame acceleration
        # Simplified rotation (would use proper quaternion math in production)
        
        # Gyroscope: measures angular velocity
        gyro = obj.angular_velocity
        
        # Add realistic noise
        import random
        noise_level = 0.01
        
        accel_noise = Vector3(
            random.gauss(0, noise_level),
            random.gauss(0, noise_level), 
            random.gauss(0, noise_level)
        )
        
        gyro_noise = Vector3(
            random.gauss(0, noise_level * 0.1),
            random.gauss(0, noise_level * 0.1),
            random.gauss(0, noise_level * 0.1)
        )
        
        return {
            "accelerometer": accel + accel_noise,
            "gyroscope": gyro + gyro_noise,
            "magnetometer": Vector3(0, 1, 0)  # Simplified north vector
        }
        
    def get_object_by_id(self, obj_id: int) -> Optional[PhysicsObject]:
        """Get physics object by ID"""
        if 0 <= obj_id < len(self.objects):
            return self.objects[obj_id]
        return None
        
    def create_ground_plane(self, height: float = 0.0) -> int:
        """Create a ground plane for collisions"""
        ground = PhysicsObject(Vector3(0, 0, height), mass=0)  # Infinite mass
        ground.collision_shape = CollisionShape.PLANE
        return self.add_object(ground)
        
    def create_box(self, position: Vector3, size: Vector3, mass: float = 1.0) -> int:
        """Create a box-shaped physics object"""
        box = PhysicsObject(position, mass)
        box.collision_shape = CollisionShape.BOX
        box.collision_size = size
        return self.add_object(box)
        
    def create_sphere(self, position: Vector3, radius: float, mass: float = 1.0) -> int:
        """Create a sphere-shaped physics object"""
        sphere = PhysicsObject(position, mass)
        sphere.collision_shape = CollisionShape.SPHERE
        sphere.collision_radius = radius
        return self.add_object(sphere)
        
    def get_world_state(self) -> Dict[str, Any]:
        """Get complete world state for debugging/visualization"""
        return {
            "time": self.time,
            "gravity": {"x": self.gravity.x, "y": self.gravity.y, "z": self.gravity.z},
            "object_count": len(self.objects),
            "objects": [
                {
                    "id": i,
                    "position": {"x": obj.position.x, "y": obj.position.y, "z": obj.position.z},
                    "velocity": {"x": obj.velocity.x, "y": obj.velocity.y, "z": obj.velocity.z},
                    "rotation": {"x": obj.rotation.x, "y": obj.rotation.y, "z": obj.rotation.z},
                    "mass": obj.mass,
                    "shape": obj.collision_shape.value
                }
                for i, obj in enumerate(self.objects)
            ]
        }