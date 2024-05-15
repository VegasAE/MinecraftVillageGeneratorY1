from room import Room
from mcpi.vec3 import Vec3
from mcpi import block
import time
import random

# Represents a floor in a house
class Floor():

    # Takes two 3D vectors and the minecraft client
    def __init__(self, c1, c2, mc, floor=[0, 53, [126, 0]], pillar=0, wall=[1,6], roof=[53, [5], [126]], roof_outline=[109, 98, 5]):

        # Store corners of house
        self.c1 = Vec3(max(c1.x, c2.x), c1.y, max(c1.z, c2.z))
        self.c2 = Vec3(min(c1.x, c2.x), c1.y, min(c1.z, c2.z))

        # Store dimensions
        self.length = abs(c1.x - c2.x)
        self.width = abs(c1.z - c2.z)
        self.min_dimension = 4
        self.height = abs(c1.y - c2.y)

        # Store blocks
        self.floor = floor
        self.pillar = pillar
        self.wall = wall
        self.roof = roof
        self.roof_outline = roof_outline

        # Store floors rooms
        self.rooms = []
        
        # Minecraft client
        self.mc = mc
        
        # Build house
        self.build()
    

    # Function to build a wall with a door
    def build_wall(self, c1, c2):

        # Build base wall
        self.mc.setBlocks(c1.x, c1.y, c1.z, c2.x, c2.y+self.height-1, c2.z, self.wall)

        # Place door
        if c1.x == c2.x:
            door = random.randint(c2.z+1, c2.z+self.min_dimension-1)
            self.mc.setBlocks(c1.x, c1.y, door, c2.x, c2.y+1, door, block.AIR.id)
        else:
            door = random.randint(c2.x+1, c2.x+self.min_dimension-1)
            self.mc.setBlocks(door, c1.y, c1.z, door, c2.y+1, c2.z, block.AIR.id)
    
    # Create the rooms for the houses
    def create_rooms(self, c1, c2):

        ##time.sleep(0.3)

        # Set some vars
        room_length = abs(c1.x - c2.x)
        room_width = abs(c1.z - c2.z)

        # Base case if the room bounds are too small
        if (room_length <= self.min_dimension*2+1) and (room_width <= self.min_dimension*2+1): 
            
            # Create room object
            room = Room(c1, c2, self.mc)
            
            # Build windows for room and windowsill
            if c1.x == self.c1.x:
                self.mc.setBlocks(c1.x, c1.y+1, c1.z-2, c1.x, self.c1.y + self.height-2, c2.z + 2, 95, 8, 10)
                self.build_windowsill(c1.x+1, c1.z-2, c1.x+1, c2.z+2, c1.y, 1, 0)
            if c2.x == self.c2.x:
                self.mc.setBlocks(c2.x, c1.y+1, c1.z-2, c2.x, self.c1.y + self.height-2, c2.z + 2, 95, 8, 10)
                self.build_windowsill(c2.x-1, c1.z-2, c2.x-1, c2.z+2, c1.y, -1, 0)
            if c1.z == self.c1.z:
                self.mc.setBlocks(c1.x-2, c1.y+1, c1.z, c2.x+2, self.c1.y + self.height-2, c1.z, 95, 8, 10)
                self.build_windowsill(c1.x-2, c1.z+1, c2.x+2, c1.z+1, c1.y, 0, 1)
            if c2.z == self.c2.z:
                self.mc.setBlocks(c1.x-2, c1.y+1, c2.z, c2.x+2, self.c1.y + self.height-2, c2.z, 95, 8, 10)
                self.build_windowsill(c1.x-2, c2.z-1, c2.x+2, c2.z-1, c1.y, 0, -1)
            return self.rooms.append(room)

        # Split the room along the longest dimension (length, width)
        if room_length > room_width:

            # Split room
            line = random.randint(c2.x+self.min_dimension, c1.x-self.min_dimension)
            self.build_wall(Vec3(line, c1.y, c1.z), Vec3(line, c2.y, c2.z))

            # Create new rooms
            self.create_rooms(c1, Vec3(line, c2.y, c2.z))
            self.create_rooms(Vec3(line, c1.y, c1.z), c2)
        else:
            # Split room
            line = random.randint(c2.z+self.min_dimension, c1.z-self.min_dimension)
            self.build_wall(Vec3(c1.x, c1.y, line), Vec3(c2.x, c2.y, line))

            # Create new rooms
            self.create_rooms(c1, Vec3(c2.x, c2.y, line))
            self.create_rooms(Vec3(c1.x, c1.y, line), c2)

    # Builds random window sill
    def build_windowsill(self, x1, z1, x2, z2, y, dir_x, dir_z):
        trapdoors = [4,5,6,7]

        if dir_x == -1:
            trapdoor = 2
        if dir_x == 1:
            trapdoor = 3
        if dir_z == -1:
            trapdoor = 0
        if dir_z == 1:
            trapdoor = 1
        windowsill = random.randint(0, 7)
        if windowsill == 0:
            self.mc.setBlocks(x1, y, z1, x2, y, z2, 96, trapdoors[trapdoor])
        elif windowsill == 1:
            self.mc.setBlocks(x1, y, z1, x2, y, z2, block.GRASS)
            self.mc.setBlock(int((x1+x2)/2), y+1, int((z1+z2)/2), 38, random.randint(0, 5))
            self.mc.setBlocks(x1+dir_x, y, z1+dir_z, x2+dir_x, y, z2+dir_z, 96, trapdoors[trapdoor])
            if dir_x + dir_z == -1:
                self.mc.setBlock(x1+abs(dir_z), y, z1+abs(dir_x), 96, trapdoors[trapdoor-1])
                self.mc.setBlock(x2-abs(dir_z), y, z2-abs(dir_x), 96, trapdoors[trapdoor-2])
            else:
                self.mc.setBlock(x1+abs(dir_z), y, z1+abs(dir_x), 96, trapdoors[trapdoor-2])
                self.mc.setBlock(x2-abs(dir_z), y, z2-abs(dir_x), 96, trapdoors[trapdoor-3])
        elif windowsill == 2:
            self.mc.setBlocks(x1, y, z1, x2, y, z2, 67, trapdoors[trapdoor-2])


    # Function to build roof
    def build_roof(self):

        # Generate roof type
        roof_type = random.randint(0,1)

        # Create flat roof
        if roof_type == 0:

            # Build house outline
            self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height, self.c1.z+1, self.c1.x+1, self.c2.y+self.height, self.c2.z-1, self.roof[0], 5)
            self.mc.setBlocks(self.c2.x-1, self.c1.y+self.height, self.c1.z+1, self.c2.x-1, self.c2.y+self.height, self.c2.z-1, self.roof[0], 4)
            self.mc.setBlocks(self.c1.x, self.c1.y+self.height, self.c1.z+1, self.c2.x, self.c2.y+self.height, self.c1.z+1, self.roof[0], 7)
            self.mc.setBlocks(self.c1.x, self.c1.y+self.height, self.c2.z-1, self.c2.x, self.c2.y+self.height, self.c2.z-1, self.roof[0], 6)

            # Flat part
            self.mc.setBlocks(self.c1.x, self.c1.y+self.height+1, self.c1.z, self.c2.x, self.c2.y+self.height+1, self.c2.z, self.roof[2])
            return

        # Build triangle roof along the smallest sides
        if (self.width > self.length):

            # Lowest outline
            self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height, self.c1.z+1, self.c1.x+1, self.c2.y+self.height, self.c2.z-1, self.roof_outline[0], 1)
            self.mc.setBlocks(self.c2.x-1, self.c1.y+self.height, self.c1.z+1, self.c2.x-1, self.c2.y+self.height, self.c2.z-1, self.roof_outline[0])

            for i in range(0, int(abs(self.length)/2)):

                ##time.sleep(0.3)
                
                # Outline
                self.mc.setBlocks(self.c1.x-i, self.c1.y+self.height+i, self.c1.z+1, self.c1.x-i, self.c2.y+self.height+1+i, self.c1.z+1, self.roof_outline[0], 1)
                self.mc.setBlocks(self.c2.x+i, self.c1.y+self.height+i, self.c1.z+1, self.c2.x+i, self.c2.y+self.height+1+i, self.c1.z+1, self.roof_outline[0])
                self.mc.setBlocks(self.c1.x-i, self.c1.y+self.height+i, self.c1.z+1, self.c1.x-i, self.c2.y+self.height+i, self.c1.z+1, self.roof_outline[0], 4)
                self.mc.setBlocks(self.c2.x+i, self.c1.y+self.height+i, self.c1.z+1, self.c2.x+i, self.c2.y+self.height+i, self.c1.z+1, self.roof_outline[0], 5)

                # Outline 2
                self.mc.setBlocks(self.c1.x-i, self.c1.y+self.height+i+1, self.c2.z-1, self.c1.x-i, self.c2.y+self.height+i+1, self.c2.z-1, self.roof_outline[0], 1)
                self.mc.setBlocks(self.c2.x+i, self.c1.y+self.height+i+1, self.c2.z-1, self.c2.x+i, self.c2.y+self.height+i+1, self.c2.z-1, self.roof_outline[0])
                self.mc.setBlocks(self.c1.x-i, self.c1.y+self.height+i, self.c2.z-1, self.c1.x-i, self.c2.y+self.height+i, self.c2.z-1, self.roof_outline[0], 4)
                self.mc.setBlocks(self.c2.x+i, self.c1.y+self.height+i, self.c2.z-1, self.c2.x+i, self.c2.y+self.height+i, self.c2.z-1, self.roof_outline[0], 5)

                # Wall
                if i:
                    self.mc.setBlocks(self.c1.x-i, self.c1.y+self.height+1, self.c1.z, self.c1.x-i, self.c2.y+self.height+i, self.c1.z, self.wall)
                    self.mc.setBlocks(self.c2.x+i, self.c1.y+self.height+1, self.c1.z, self.c2.x+i, self.c2.y+self.height+i, self.c1.z, self.wall)
                    self.mc.setBlocks(self.c1.x-i, self.c1.y+self.height+1, self.c2.z, self.c1.x-i, self.c2.y+self.height+i, self.c2.z, self.wall)
                    self.mc.setBlocks(self.c2.x+i, self.c1.y+self.height+1, self.c2.z, self.c2.x+i, self.c2.y+self.height+i, self.c2.z, self.wall)

                # Main part
                self.mc.setBlocks(self.c1.x-i, self.c1.y+self.height+i+1, self.c1.z, self.c1.x-i, self.c2.y+self.height+i+1, self.c2.z, self.roof[0], 1)
                self.mc.setBlocks(self.c2.x+i, self.c1.y+self.height+i+1, self.c1.z, self.c2.x+i, self.c2.y+self.height+i+1, self.c2.z, self.roof[0])
        
            # Tip of roof
            self.mc.setBlocks(self.c1.x-i-1, self.c1.y+self.height+1, self.c1.z, self.c2.x+i+1, self.c2.y+self.height+i, self.c1.z, self.wall)
            self.mc.setBlocks(self.c1.x-i-1, self.c1.y+self.height+1, self.c2.z, self.c2.x+i+1, self.c2.y+self.height+i, self.c2.z, self.wall)
            self.mc.setBlocks(self.c1.x-i-1, self.c1.y+self.height+i+1, self.c1.z+1, self.c2.x+i+1, self.c2.y+self.height+i+1, self.c2.z-1, self.roof_outline[1])
            self.mc.setBlocks(self.c1.x-i-1, self.c1.y+self.height+i+2, self.c1.z+1, self.c2.x+i+1, self.c2.y+self.height+i+2, self.c2.z-1, 44, self.roof_outline[2])
            return
        else:
            # Lowest outline
            self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height, self.c1.z+1, self.c2.x-1, self.c2.y+self.height, self.c1.z+1, self.roof_outline[0], 3)
            self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height, self.c2.z-1, self.c2.x-1, self.c2.y+self.height, self.c2.z-1, self.roof_outline[0], 2)
            for i in range(0, int(abs(self.width)/2)):

                ##time.sleep(0.3)
                
                # Outline
                self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height+i+1, self.c1.z-i, self.c1.x+1, self.c2.y+self.height+i+1, self.c1.z-i, self.roof_outline[0], 3)
                self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height+i+1, self.c2.z+i, self.c1.x+1, self.c2.y+self.height+i+1, self.c2.z+i, self.roof_outline[0], 2)
                self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height+i, self.c1.z-i, self.c1.x+1, self.c2.y+self.height+i, self.c1.z-i, self.roof_outline[0], 6)
                self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height+i, self.c2.z+i, self.c1.x+1, self.c2.y+self.height+i, self.c2.z+i, self.roof_outline[0], 7)

                # Outline 2
                self.mc.setBlocks(self.c2.x-1, self.c1.y+self.height+i+1, self.c1.z-i, self.c2.x-1, self.c2.y+self.height+i+1, self.c1.z-i, self.roof_outline[0], 3)
                self.mc.setBlocks(self.c2.x-1, self.c1.y+self.height+i+1, self.c2.z+i, self.c2.x-1, self.c2.y+self.height+i+1, self.c2.z+i, self.roof_outline[0], 2)
                self.mc.setBlocks(self.c2.x-1, self.c1.y+self.height+i, self.c1.z-i, self.c2.x-1, self.c2.y+self.height+i, self.c1.z-i, self.roof_outline[0], 6)
                self.mc.setBlocks(self.c2.x-1, self.c1.y+self.height+i, self.c2.z+i, self.c2.x-1, self.c2.y+self.height+i, self.c2.z+i, self.roof_outline[0], 7)

                # Build wall
                if i:
                    self.mc.setBlocks(self.c1.x, self.c1.y+self.height+1, self.c1.z-i, self.c1.x, self.c2.y+self.height+i, self.c1.z-i, self.wall)
                    self.mc.setBlocks(self.c1.x, self.c1.y+self.height+1, self.c2.z+i, self.c1.x, self.c2.y+self.height+i, self.c2.z+i, self.wall)
                    self.mc.setBlocks(self.c2.x, self.c1.y+self.height+1, self.c1.z-i, self.c2.x, self.c2.y+self.height+i, self.c1.z-i, self.wall)
                    self.mc.setBlocks(self.c2.x, self.c1.y+self.height+1, self.c2.z+i, self.c2.x, self.c2.y+self.height+i, self.c2.z+i, self.wall)

                # Main part
                self.mc.setBlocks(self.c1.x, self.c1.y+self.height+i+1, self.c1.z-i, self.c2.x, self.c2.y+self.height+i+1, self.c1.z-i, self.roof[0], 3)
                self.mc.setBlocks(self.c1.x, self.c1.y+self.height+i+1, self.c2.z+i, self.c2.x, self.c2.y+self.height+i+1, self.c2.z+i, self.roof[0], 2)
        
            # Top of roof
            self.mc.setBlocks(self.c1.x, self.c1.y+self.height+1, self.c1.z-i-1, self.c1.x, self.c2.y+self.height+i, self.c2.z+i+1, self.wall)
            self.mc.setBlocks(self.c2.x, self.c1.y+self.height+1, self.c1.z-i-1, self.c2.x, self.c2.y+self.height+i, self.c2.z+i+1, self.wall)
            self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height+i+1, self.c1.z-i-1, self.c2.x-1, self.c2.y+self.height+i+1, self.c2.z+i+1, self.roof_outline[1])
            self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height+i+2, self.c1.z-i-1, self.c2.x-1, self.c2.y+self.height+i+2, self.c2.z+i+1, 44, self.roof_outline[2])
            return
        
    # Builds the floor
    def build(self):

        # Build pillars
        self.mc.setBlocks(self.c1.x, self.c1.y, self.c1.z, self.c1.x, self.c1.y+self.height, self.c1.z, block.WOOD, self.pillar)
        ##time.sleep(0.3)
        self.mc.setBlocks(self.c2.x, self.c2.y, self.c2.z, self.c2.x, self.c2.y+self.height, self.c2.z, block.WOOD, self.pillar)
        ##time.sleep(0.3)
        self.mc.setBlocks(self.c2.x, self.c1.y, self.c1.z, self.c2.x, self.c1.y+self.height, self.c1.z, block.WOOD, self.pillar)
        ##time.sleep(0.3)
        self.mc.setBlocks(self.c1.x, self.c1.y, self.c2.z, self.c1.x, self.c1.y+self.height, self.c2.z, block.WOOD, self.pillar)
        ##time.sleep(0.3)

        # Build walls
        self.mc.setBlocks(self.c1.x-1, self.c1.y, self.c1.z, self.c2.x+1, self.c2.y+self.height, self.c1.z, self.wall)
        ##time.sleep(0.3)
        self.mc.setBlocks(self.c1.x, self.c1.y, self.c1.z-1, self.c1.x, self.c2.y+self.height, self.c2.z+1, self.wall)
        ##time.sleep(0.3)
        self.mc.setBlocks(self.c2.x, self.c2.y, self.c2.z+1, self.c2.x, self.c1.y+self.height, self.c1.z-1, self.wall)
        ##time.sleep(0.3)
        self.mc.setBlocks(self.c2.x+1, self.c2.y, self.c2.z, self.c1.x-1, self.c2.y+self.height, self.c2.z, self.wall)

        # Create rooms
        self.create_rooms(self.c1, self.c2)
        ##time.sleep(0.3)

        # Build flat roof
        self.mc.setBlocks(self.c1.x-1, self.c1.y+self.height, self.c1.z-1, self.c2.x+1, self.c2.y+self.height, self.c2.z+1, self.floor[0])
        ##time.sleep(0.3)

    # Function to build stairs
    def build_stairs(self, floor_above):

        # Check if the room is in a corner
        for room in self.rooms:

            # Check which corner
            h = self.height
            y = room.c1.y
            x = room.c1.x
            z = room.c1.z
            stair_bottom = 2
            stair_top = 1

            # Determine stair direction
            if (room.c1.x == floor_above.c1.x) and (room.c1.z == floor_above.c1.z):
                dir_x = -1
                dir_z = -1
            elif (room.c2.x == floor_above.c2.x) and (room.c1.z == floor_above.c1.z):
                dir_x = 1
                dir_z = -1
                stair_top = 0
                x = room.c2.x
            elif (room.c1.x == floor_above.c1.x) and (room.c2.z == floor_above.c2.z):
                dir_x = -1
                dir_z = 1
                stair_bottom = 3
                z = room.c2.z
            elif (room.c2.x == floor_above.c2.x) and (room.c2.z == floor_above.c2.z):
                dir_x = 1
                dir_z = 1
                stair_bottom = 3
                stair_top = 0
                x = room.c2.x
                z = room.c2.z
            else:
                continue
            step = 0 # Keep track of stair height

            # Build bottom stairs
            for i in range(h-1, 0, -1):
                self.mc.setBlocks(x+(1*dir_x), y+h, z+(i*dir_z), x+(1*dir_x), y+h, z+(i*dir_z), block.AIR)
                self.mc.setBlocks(x+(1*dir_x), y+step, z+(i*dir_z), x+(1*dir_x), y+step, z+(i*dir_z), self.floor[1], stair_bottom)
                if step > 0:
                    self.mc.setBlocks(x+(1*dir_x), y, z+(i*dir_z), x+(1*dir_x), y+step-1, z+(i*dir_z), self.floor[0])
                step += 1

            # Build upper stairs
            for i in range(2, min(h+2, 4)):
                self.mc.setBlocks(x+(i*dir_x), y+h, z+(1*dir_z), x+(i*dir_x), y+h+2, z+(1*dir_z), block.AIR)
                self.mc.setBlocks(x+(i*dir_x), y+step, z+(1*dir_z), x+(i*dir_x), y+step, z+(1*dir_z), self.floor[1], stair_top)
                if step > 0:
                    self.mc.setBlocks(x+(i*dir_x), y, z+(1*dir_z), x+(i*dir_x), y+step-1, z+(1*dir_z), self.floor[0])
                step += 1
            break
    
    # Build front door
    def build_entrance(self, dir=0):

        # Store possible door locations
        doors = []

        # Get dir
        x_dir = 0
        z_dir = 0
        if dir == 0:
            c1 = self.c1
            c2 = Vec3(self.c1.x, self.c1.y, self.c2.z)
            x_dir = 1
        elif dir == 1:
            c1 = self.c1
            c2 = Vec3(self.c2.x, self.c1.y, self.c1.z)
            z_dir = 1
        elif dir == 2:
            c1 = Vec3(self.c2.x, self.c1.y, self.c1.z)
            c2 = Vec3(self.c2.x, self.c1.y, self.c2.z)
            x_dir = -1
        elif dir == 3:
            c1 = Vec3(self.c1.x, self.c1.y, self.c2.z)
            c2 = Vec3(self.c2.x, self.c1.y, self.c2.z)
            z_dir = -1
        
        # Go along the wall and look for a door pos
        for i in range(c2.z, c1.z):
            time.sleep(0.02)
            if (self.mc.getBlock(c1.x-x_dir, c1.y+1, i) == 0) and (self.mc.getBlock(c1.x-x_dir, c1.y, i) == 0) and (self.mc.getBlock(c1.x-x_dir, c1.y-1, i) != 0):
                doors.append(Vec3(c1.x, c1.y, i))
        
        for i in range(c2.x, c1.x):
            time.sleep(0.02)
            if (self.mc.getBlock(i, c1.y+1, c1.z-z_dir) == 0) and (self.mc.getBlock(i, c1.y, c1.z-z_dir) == 0) and (self.mc.getBlock(i, c1.y-1, c1.z-z_dir) != 0):
                doors.append(Vec3(i, c1.y, c1.z))
        
        # Choose door location
        door = random.choice(doors)

        # Find room and clear wall
        for r in self.rooms:
            if (r.c1.x > door.x) and (door.x > r.c2.x):
                if door.z == r.c1.z:
                    self.mc.setBlocks(r.c1.x, door.y, door.z+1, r.c2.x, door.y+1, door.z+2, 0)
                    break
                elif door.z == r.c2.z:
                    self.mc.setBlocks(r.c1.x, door.y, door.z-1, r.c2.x, door.y+1, door.z-2, 0)
                    break
            elif (r.c1.z > door.z) and (door.z > r.c2.z):
                if door.x == r.c1.x:
                    self.mc.setBlocks(door.x+1, door.y, r.c1.z, door.x+2, door.y+1, r.c2.z, 0)
                    break
                elif door.x == r.c2.x:
                    self.mc.setBlocks(door.x-1, door.y, r.c1.z, door.x-2, door.y+1, r.c2.z, 0)
                    break
        if x_dir:
            # Put air in front of door
            self.mc.setBlocks(door.x+x_dir, door.y, door.z, door.x+x_dir*2, door.y+1, door.z, 0)
            if dir == 0:
                self.mc.setBlock(door.x, door.y+1, door.z, 64, 10)
                self.mc.setBlock(door.x, door.y, door.z, 64, 2)
            elif dir == 2:
                self.mc.setBlock(door.x, door.y+1, door.z, 64, 8)
                self.mc.setBlock(door.x, door.y, door.z, 64, 0)
        else:
            # Put air in front of door
            self.mc.setBlocks(door.x, door.y, door.z+z_dir, door.x, door.y+1, door.z+z_dir*2, 0)
            if dir == 1:
                self.mc.setBlock(door.x, door.y+1, door.z, 64, 11)
                self.mc.setBlock(door.x, door.y, door.z, 64, 3)
            elif dir == 3:
                self.mc.setBlock(door.x, door.y+1, door.z, 64, 9)
                self.mc.setBlock(door.x, door.y, door.z, 64, 1)

        return door
    
    # Tell rooms to decorate themselves
    def decorate(self):
        for room in self.rooms:
            time.sleep(0.2)
            room.decorate()