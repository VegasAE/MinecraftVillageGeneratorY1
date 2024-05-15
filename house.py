# Import the goods
import random
from mcpi import block
from mcpi.vec3 import Vec3
from room import Room
from floor import Floor
import time

# Representation of a basic village house
class House():

    # Takes two corners as arrays of size 2 and the minecraft client
    def __init__(self, c1, c2, mc, dir=0, type="normal"):

        # Store corners of house
        self.c1 = Vec3(max(c1.x, c2.x), c1.y, max(c1.z, c2.z))
        self.c2 = Vec3(min(c1.x, c2.x), c2.y, min(c1.z, c2.z))
        self.dir = dir

        # Generate random number of floors and height
        self.length = abs(c1.x - c2.x)
        self.width = abs(c1.z - c2.z)
        self.num_floors = random.randint(1, 2)
        self.height = max(random.randint(0, int(max(self.length, self.width)/4)), 3)
        self.floors = []
        
        # Pick blocks
        self.floor = random.choice([[[5, 0], 53, [126, 0]], [[5, 1], 134, [126, 1]], [[5, 2], 135, [126, 2]], [[5, 5], 164, [126, 5]]]) # Block, stair, slab
        self.pillar = random.choice([0, 1, 2, 3, 4])
        self.wall = random.choice([[1, 6], 98])
        self.roof_outline = random.choice([[109, 98, 5], [67, 4, 3]]) # Stair, block, slab
        self.roof = random.choice([[53, [5], [126]], [134, [5, 1], [126, 1]], [164, [5, 5], [126, 5]]]) # Stair, block, slab

        # Store vector 3 of door location
        self.door = 0

        # Minecraft client
        self.mc = mc
        
        # Build house
        self.build()
    
    
    # Function to build basics of the house
    def build(self):

        # Build floor
        self.mc.setBlocks(self.c1.x, self.c1.y-1, self.c1.z, self.c2.x, self.c2.y-1, self.c2.z, self.floor)
        self.mc.setBlocks(self.c1.x, self.c1.y, self.c1.z, self.c2.x, self.c2.y+1, self.c2.z, 0)
        #time.sleep(0.3)
        has_balcony = False

        # Create floors
        for i in range(0, self.num_floors):
            floor_c1 = Vec3(self.c1.x, self.c1.y + self.height * (i) + min(i, 1), self.c1.z)
            floor_c2 = Vec3(self.c2.x, self.c2.y + self.height * (i + 1) + min(i, 1), self.c2.z)

            # Create balcony
            if i > 0 and random.randint(0, 10) > 4:

                # Generate balcony
                has_balcony = True
                balcony_size_x = random.randint(2, 4)
                balcony_size_z = random.randint(2, 4)
                balcony_dir_x = random.randint(0, 1)
                balcony_dir_z = random.randint(0, 1)
                floor_c1.x -= balcony_size_x * balcony_dir_x
                floor_c1.z -= balcony_size_z * balcony_dir_z
                floor_c2.x += balcony_size_x * abs(balcony_dir_x - 1)
                floor_c2.z += balcony_size_z * abs(balcony_dir_z - 1)
                
                # Build outline for balcony
                self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height, self.c1.z+1, self.c1.x+1, self.c2.y+self.height, self.c2.z-1, self.roof[0], 5)
                self.mc.setBlocks(self.c2.x-1, self.c1.y+self.height, self.c1.z+1, self.c2.x-1, self.c2.y+self.height, self.c2.z-1, self.roof[0], 4)
                self.mc.setBlocks(self.c1.x, self.c1.y+self.height, self.c1.z+1, self.c2.x, self.c2.y+self.height, self.c1.z+1, self.roof[0], 7)
                self.mc.setBlocks(self.c1.x, self.c1.y+self.height, self.c2.z-1, self.c2.x, self.c2.y+self.height, self.c2.z-1, self.roof[0], 6)
                self.mc.setBlocks(self.c1.x+1, self.c1.y+self.height + 1, self.c1.z+1, self.c1.x+1, self.c2.y+self.height + 1, self.c2.z-1, self.roof[0], 1)
                self.mc.setBlocks(self.c2.x-1, self.c1.y+self.height + 1, self.c1.z+1, self.c2.x-1, self.c2.y+self.height + 1, self.c2.z-1, self.roof[0], 0)
                self.mc.setBlocks(self.c1.x, self.c1.y+self.height + 1, self.c1.z+1, self.c2.x, self.c2.y+self.height + 1, self.c1.z+1, self.roof[0], 3)
                self.mc.setBlocks(self.c1.x, self.c1.y+self.height + 1, self.c2.z-1, self.c2.x, self.c2.y+self.height + 1, self.c2.z-1, self.roof[0], 2)
                floor = Floor(floor_c1, floor_c2, self.mc, floor=self.floor, pillar=self.pillar, wall=self.wall, roof=self.roof, roof_outline=self.roof_outline)
            else:
                floor = Floor(floor_c1, floor_c2, self.mc, floor=self.floor, pillar=self.pillar, wall=self.wall, roof=self.roof, roof_outline=self.roof_outline)

            self.floors.append(floor)

        # Build roof on top floor
        self.floors[-1].build_roof()
        
        # Tell lower floors to build stairs to next level
        for num, floor in enumerate(self.floors):
            if num < len(self.floors) - 1:
                floor.build_stairs(self.floors[num + 1])
        
        # Tell floors to decorate rooms
        for floor in self.floors:
            floor.decorate()
        
        # Build balcony entrance
        if has_balcony:
            if balcony_dir_x:
                self.floors[-1].build_entrance(dir=0)
            else:
                self.floors[-1].build_entrance(dir=2)
        
        # Build entrance
        self.door = self.floors[0].build_entrance(dir=self.dir)
                
    

    
