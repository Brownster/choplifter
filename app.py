import pygame
import random
import math
import os
from pygame.math import Vector2
from pygame.locals import *

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Display Configuration
BASE_RES = (320, 200)
SCALE_FACTOR = 3
SCREEN = pygame.display.set_mode((BASE_RES[0] * SCALE_FACTOR, BASE_RES[1] * SCALE_FACTOR))
VIRTUAL_SURFACE = pygame.Surface(BASE_RES)
pygame.display.set_caption("Choplifter Clone")
clock = pygame.time.Clock()

# C64 Color Palette
COLORS = {
    'bg': (0, 24, 88),       # Deep blue
    'heli_body': (255, 255, 255),  # White
    'heli_edge': (104, 56, 184),   # Purple
    'ground': (136, 68, 68),       # Brown
    'bunker': (170, 170, 170),     # Light gray
    'hostage': (240, 160, 160),    # Pink
    'tank': (80, 80, 80),          # Dark gray
    'explosion': (255, 127, 0),    # Orange
    'bullet': (230, 230, 0),       # Yellow
    'text': (255, 255, 255)        # White
}

# Sound Effects
class SoundManager:
    def __init__(self):
        self.sounds = {
            'rotor': self._create_sound('rotor', 0.3),
            'shot': self._create_sound('shot', 0.4),
            'explosion': self._create_sound('explosion', 0.5),
            'rescue': self._create_sound('rescue', 0.4),
            'land': self._create_sound('land', 0.3)
        }
        self.channels = {}
        for i, sound_name in enumerate(self.sounds):
            self.channels[sound_name] = pygame.mixer.Channel(i)
    
    def _create_sound(self, name, volume):
        # In a real game you would load a sound file.
        sound = pygame.mixer.Sound(self._generate_dummy_sound(name))
        sound.set_volume(volume)
        return sound
    
    def _generate_dummy_sound(self, name):
        array = bytearray()
        frequency = {
            'rotor': 80, 'shot': 230, 'explosion': 50, 
            'rescue': 180, 'land': 120
        }.get(name, 100)
        
        for i in range(4000):
            amplitude = min(255, int(100 + 100 * math.sin(i / frequency)))
            array.append(amplitude)
        
        return array
    
    def play(self, name, loop=0):
        if name in self.sounds:
            self.channels[name].play(self.sounds[name], loops=loop)
    
    def stop(self, name):
        if name in self.channels:
            self.channels[name].stop()

# Projectile System
class Projectile(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((4, 2))
        self.image.fill(COLORS['bullet'])
        self.rect = self.image.get_rect()
        self.pos = Vector2(0, 0)
        self.vel = Vector2(0, 0)
        self.active = False
        self.max_distance = 200
        self.distance_traveled = 0
        self.damage = 10
    
    def fire(self, pos, direction, speed=5):
        self.pos = Vector2(pos)
        self.vel = Vector2(direction).normalize() * speed
        self.rect.center = self.pos
        self.active = True
        self.distance_traveled = 0
    
    def update(self, dt):
        if not self.active:
            return
        movement = self.vel * dt * 60
        self.pos += movement
        self.distance_traveled += movement.length()
        self.rect.center = self.pos
        if self.distance_traveled > self.max_distance:
            self.active = False
            self.kill()

class ProjectilePool:
    def __init__(self, size=20):
        self.projectiles = pygame.sprite.Group()
        self.size = size
        self.refill_pool()
    
    def refill_pool(self):
        current_size = len(self.projectiles)
        for _ in range(self.size - current_size):
            self.projectiles.add(Projectile())
    
    def get_projectile(self):
        for proj in self.projectiles:
            if not proj.active:
                return proj
        new_proj = Projectile()
        self.projectiles.add(new_proj)
        return new_proj
    
    def update(self, dt):
        self.projectiles.update(dt)

# Explosion Effect
class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = Vector2(pos)
        self.frames = self._create_frames()
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=pos)
        self.frame_index = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 100  # milliseconds
    
    def _create_frames(self):
        frames = []
        sizes = [4, 8, 12, 16, 12, 8, 4]
        for size in sizes:
            frame = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(frame, COLORS['explosion'], (size // 2, size // 2), size // 2)
            frames.append(frame)
        return frames
    
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.kill()
                return
            self.image = self.frames[self.frame_index]
            center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = center
            self.last_update = now

# Helicopter Sprite Setup
class Helicopter(pygame.sprite.Sprite):
    DIRECTION_LEFT = -1
    DIRECTION_RIGHT = 1
    STATE_FLYING = 0
    STATE_LANDED = 1
    STATE_TURNING = 2
    
    def __init__(self, sound_manager, explosion_group):
        super().__init__()
        self.sound_manager = sound_manager
        self.explosion_group = explosion_group
        self.direction = self.DIRECTION_RIGHT
        self.state = self.STATE_FLYING
        
        # Create frames for all states
        self.frames = {
            'fly_right': self._create_fly_frames(self.DIRECTION_RIGHT),
            'fly_left': self._create_fly_frames(self.DIRECTION_LEFT),
            'turn_right_to_left': self._create_turn_frames(self.DIRECTION_RIGHT, self.DIRECTION_LEFT),
            'turn_left_to_right': self._create_turn_frames(self.DIRECTION_LEFT, self.DIRECTION_RIGHT),
            'landed_right': self._create_landed_frames(self.DIRECTION_RIGHT),
            'landed_left': self._create_landed_frames(self.DIRECTION_LEFT)
        }
        
        self.image = self.frames['fly_right'][0]
        self.rect = self.image.get_rect(center=(BASE_RES[0] // 2, BASE_RES[1] // 2))
        self.pos = Vector2(self.rect.center)
        self.vel = Vector2(0, 0)
        self.accel = Vector2(0, 0)
        self.frame_index = 0
        self.last_update = pygame.time.get_ticks()
        self.turning_frames = 0
        
        # Physics parameters
        self.lift = 0.45
        self.gravity = 0.3
        self.drag = 0.85
        self.max_speed = 4.5
        
        # Combat parameters
        self.health = 100
        self.max_health = 100
        self.fire_rate = 300  # milliseconds
        self.last_shot = 0
        
        # Hostage carrying capacity
        self.max_hostages = 16
        self.hostages_carried = 0
        
        # Start rotor sound loop
        self.sound_manager.play('rotor', loop=-1)
    
    def _create_fly_frames(self, direction):
        frames = []
        for i in range(4):  # 4-frame rotor animation
            frame = pygame.Surface((24, 24), SRCALPHA)
            frame.fill((0, 0, 0, 0))
            # Body
            pygame.draw.ellipse(frame, COLORS['heli_body'], (0, 8, 24, 8))
            # Tail
            if direction == self.DIRECTION_RIGHT:
                pygame.draw.line(frame, COLORS['heli_edge'], (4, 12), (0, 16), 2)
            else:
                pygame.draw.line(frame, COLORS['heli_edge'], (20, 12), (24, 16), 2)
            # Rotor animation (same for both directions)
            rotor_offset = i * 1.5
            pygame.draw.line(frame, COLORS['heli_edge'], (12 - rotor_offset, 8), (12 + rotor_offset, 8), 2)
            frames.append(frame)
        return frames
    
    def _create_turn_frames(self, from_dir, to_dir):
        frames = []
        frame = pygame.Surface((24, 24), SRCALPHA)
        frame.fill((0, 0, 0, 0))
        pygame.draw.ellipse(frame, COLORS['heli_body'], (0, 8, 24, 8))
        pygame.draw.line(frame, COLORS['heli_edge'], (8, 8), (16, 8), 2)
        frames.append(frame)
        return frames
    
    def _create_landed_frames(self, direction):
        frame = pygame.Surface((24, 24), SRCALPHA)
        frame.fill((0, 0, 0, 0))
        pygame.draw.ellipse(frame, COLORS['heli_body'], (0, 12, 24, 8))
        if direction == self.DIRECTION_RIGHT:
            pygame.draw.line(frame, COLORS['heli_edge'], (4, 16), (0, 20), 2)
        else:
            pygame.draw.line(frame, COLORS['heli_edge'], (20, 16), (24, 20), 2)
        pygame.draw.line(frame, COLORS['heli_edge'], (8, 12), (16, 12), 2)
        return [frame]
    
    def _get_current_frame_set(self):
        if self.state == self.STATE_TURNING:
            if self.direction == self.DIRECTION_RIGHT:
                return 'turn_left_to_right'
            else:
                return 'turn_right_to_left'
        elif self.state == self.STATE_LANDED:
            if self.direction == self.DIRECTION_RIGHT:
                return 'landed_right'
            else:
                return 'landed_left'
        else:  # FLYING
            if self.direction == self.DIRECTION_RIGHT:
                return 'fly_right'
            else:
                return 'fly_left'
    
    def shoot(self, projectile_pool):
        now = pygame.time.get_ticks()
        if now - self.last_shot < self.fire_rate:
            return None
        self.last_shot = now
        projectile = projectile_pool.get_projectile()
        if self.direction == self.DIRECTION_RIGHT:
            pos = self.rect.midright
            direction = Vector2(1, 0)
        else:
            pos = self.rect.midleft
            direction = Vector2(-1, 0)
        projectile.fire(pos, direction, 8)
        self.sound_manager.play('shot')
        return projectile
    
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.explode()
            return True
        return False
    
    def explode(self):
        self.sound_manager.stop('rotor')
        self.sound_manager.play('explosion')
        explosion = Explosion(self.rect.center)
        self.explosion_group.add(explosion)
        self.kill()
    
    def land(self, ground_y):
        if self.state != self.STATE_LANDED and abs(self.vel.y) < 1.0:
            if abs(ground_y - self.rect.bottom) < 5:
                self.sound_manager.play('land')
                self.state = self.STATE_LANDED
                self.vel = Vector2(0, 0)
                self.pos.y = ground_y - self.rect.height // 2
                self.rect.center = self.pos
                return True
        return False
    
    def take_off(self):
        if self.state == self.STATE_LANDED:
            self.state = self.STATE_FLYING
    
    def pickup_hostages(self, hostages):
        can_pickup = self.max_hostages - self.hostages_carried
        if can_pickup <= 0:
            return 0
        picked_up = min(can_pickup, len(hostages))
        self.hostages_carried += picked_up
        self.sound_manager.play('rescue')
        return picked_up
    
    def drop_hostages(self):
        hostages_dropped = self.hostages_carried
        self.hostages_carried = 0
        return hostages_dropped
    
    def update(self, dt, keys, ground_y):
        # Handle turning state
        if self.state == self.STATE_TURNING:
            self.turning_frames += 1
            if self.turning_frames >= 5:  # Finish turning animation
                self.state = self.STATE_FLYING
                self.turning_frames = 0
                self.direction *= -1
            return
        
        # Check for a change in direction (initiate turn)
        if self.state not in (self.STATE_TURNING, self.STATE_LANDED):
            if (keys[K_LEFT] and self.direction == self.DIRECTION_RIGHT) or \
               (keys[K_RIGHT] and self.direction == self.DIRECTION_LEFT):
                self.state = self.STATE_TURNING
                self.turning_frames = 0
                return
        
        # Basic physics (apply gravity, lift and horizontal acceleration)
        self.accel = Vector2(0, self.gravity)
        if self.state != self.STATE_LANDED:
            if keys[K_LEFT] and self.direction == self.DIRECTION_LEFT:
                self.accel.x = -0.8
            if keys[K_RIGHT] and self.direction == self.DIRECTION_RIGHT:
                self.accel.x = 0.8
            if keys[K_UP]:
                self.accel.y = -self.lift
            self.vel += self.accel * dt * 60
            self.vel *= self.drag
            if self.vel.length() > self.max_speed:
                self.vel.scale_to_length(self.max_speed)
            self.pos += self.vel * dt * 60
            self.rect.center = self.pos
            # Ground collision check
            if self.rect.bottom >= ground_y:
                self.land(ground_y)
        
        # Update animation frames
        current_set = self._get_current_frame_set()
        frames = self.frames[current_set]
        now = pygame.time.get_ticks()
        if now - self.last_update > 100:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            self.last_update = now

# Simple Tank Enemy
class Tank(pygame.sprite.Sprite):
    def __init__(self, x, ground_y):
        super().__init__()
        self.image = pygame.Surface((20, 10))
        self.image.fill(COLORS['tank'])
        self.rect = self.image.get_rect(midbottom=(x, ground_y))
        self.health = 50
    
    def update(self, dt):
        # For now tanks are static; AI can be added later.
        pass

# Hostage Sprite
class Hostage(pygame.sprite.Sprite):
    def __init__(self, x, ground_y):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(COLORS['hostage'])
        self.rect = self.image.get_rect(midbottom=(x, ground_y))
    
    def update(self, dt):
        # Hostage AI/pathfinding can be added here.
        pass

# Main Game Loop
def main():
    running = True
    ground_y = BASE_RES[1] - 20  # Define the ground level
    sound_manager = SoundManager()
    
    # Create sprite groups
    explosions = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    tank_group = pygame.sprite.Group()
    hostage_group = pygame.sprite.Group()
    
    # Create the helicopter (pass the explosions group so it can add explosion effects)
    helicopter = Helicopter(sound_manager, explosions)
    all_sprites.add(helicopter)
    
    # Create projectile pool
    projectile_pool = ProjectilePool(20)
    
    # Create some enemy tanks
    for i in range(3):
        x = random.randint(50, BASE_RES[0] - 50)
        tank = Tank(x, ground_y)
        tank_group.add(tank)
        all_sprites.add(tank)
    
    # Create some hostages
    for i in range(5):
        x = random.randint(50, BASE_RES[0] - 50)
        hostage = Hostage(x, ground_y)
        hostage_group.add(hostage)
        all_sprites.add(hostage)
    
    rescued_hostages = 0
    font = pygame.font.SysFont(None, 24)
    
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                if event.key == K_SPACE:
                    helicopter.shoot(projectile_pool)
                if event.key == K_d:
                    # For testing: damage the helicopter
                    helicopter.take_damage(20)
                if event.key == K_t:
                    # Take off if landed
                    helicopter.take_off()
        
        keys = pygame.key.get_pressed()
        helicopter.update(dt, keys, ground_y)
        projectile_pool.update(dt)
        explosions.update()
        tank_group.update(dt)
        hostage_group.update(dt)
        
        # Check for projectile-tank collisions
        for proj in list(projectile_pool.projectiles):
            if proj.active:
                hit_tanks = pygame.sprite.spritecollide(proj, tank_group, False)
                if hit_tanks:
                    for tank in hit_tanks:
                        tank.health -= proj.damage
                        proj.active = False
                        proj.kill()
                        if tank.health <= 0:
                            explosion = Explosion(tank.rect.center)
                            explosions.add(explosion)
                            tank.kill()
        
        # Check for helicopter-hostage collisions (pickup)
        for hostage in list(hostage_group):
            if helicopter.rect.colliderect(hostage.rect):
                if helicopter.hostages_carried < helicopter.max_hostages:
                    helicopter.pickup_hostages([hostage])
                    hostage.kill()
        
        # If the helicopter is landed in a drop zone (left side), drop hostages
        if helicopter.state == Helicopter.STATE_LANDED and helicopter.rect.left < 30:
            rescued = helicopter.drop_hostages()
            rescued_hostages += rescued
        
        # Drawing to the virtual surface
        VIRTUAL_SURFACE.fill(COLORS['bg'])
        pygame.draw.rect(VIRTUAL_SURFACE, COLORS['ground'], (0, ground_y, BASE_RES[0], BASE_RES[1] - ground_y))
        
        # Draw all sprites
        for sprite in all_sprites:
            VIRTUAL_SURFACE.blit(sprite.image, sprite.rect)
        for proj in projectile_pool.projectiles:
            if proj.active:
                VIRTUAL_SURFACE.blit(proj.image, proj.rect)
        for explosion in explosions:
            VIRTUAL_SURFACE.blit(explosion.image, explosion.rect)
        
        # Draw a simple HUD
        health_text = font.render(f'Health: {helicopter.health}', True, COLORS['text'])
        hostages_text = font.render(f'Carrying: {helicopter.hostages_carried}  Rescued: {rescued_hostages}', True, COLORS['text'])
        VIRTUAL_SURFACE.blit(health_text, (5, 5))
        VIRTUAL_SURFACE.blit(hostages_text, (5, 20))
        
        # Scale the virtual surface to the main screen and update display
        scaled_surface = pygame.transform.scale(VIRTUAL_SURFACE, (BASE_RES[0] * SCALE_FACTOR, BASE_RES[1] * SCALE_FACTOR))
        SCREEN.blit(scaled_surface, (0, 0))
        pygame.display.flip()
    
    pygame.quit()

if __name__ == '__main__':
    main()
