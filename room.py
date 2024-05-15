# Import the goods
from mcpi import block
from mcpi.vec3 import Vec3
from random import randint
from random import choice
from time import sleep
from mcpi_fast_query import alt_picraft_getblock_vrange

# Class representation of room
class Room():

    # Init
    def __init__(self, c1, c2, mc, type=0) -> None:
        self.c1 = c1
        self.c2 = c2
        self.mc = mc
        self.type = type

    # Decorate room
    def decorate(self):
        self.light()    

        # Build room based on type
        if (abs(self.c1.x - self.c2.x) * abs(self.c1.z - self.c2.z)) >= 28:

            # Set some vars
            self.type = randint(0, 1)
            center_x = int((abs(self.c1.x + self.c2.x) / 2))
            center_z = int((abs(self.c1.z + self.c2.z) / 2))

            # Dining room
            if self.type == 0:
                if ((abs(self.c1.x - self.c2.x) > 5) and (abs(self.c1.z - self.c2.z) > 5)) and ((abs(self.c1.x - self.c2.x) > 7) or (abs(self.c1.z - self.c2.z) > 7)):
                    if (abs(self.c1.x - self.c2.x) >= abs(self.c1.z - self.c2.z)):
                        # Table
                        self.mc.setBlocks(center_x-1, self.c1.y, center_z, center_x+1, self.c1.y, center_z, 44, 15)

                        # Seats
                        self.mc.setBlocks(center_x+1, self.c1.y, center_z+1, center_x+1, self.c1.y, center_z+1, 156, 2)
                        self.mc.setBlocks(center_x-1, self.c1.y, center_z+1, center_x-1, self.c1.y, center_z+1, 156, 2)
                        self.mc.setBlocks(center_x+1, self.c1.y, center_z-1, center_x+1, self.c1.y, center_z-1, 156, 3)
                        self.mc.setBlocks(center_x-1, self.c1.y, center_z-1, center_x-1, self.c1.y, center_z-1, 156, 3)
                        self.mc.setBlocks(center_x-2, self.c1.y, center_z, center_x-2, self.c1.y, center_z, 156, 1)
                        self.mc.setBlocks(center_x+2, self.c1.y, center_z, center_x+2, self.c1.y, center_z, 156)
                        # Seats
                    else:
                        #Table
                        self.mc.setBlocks(center_x, self.c1.y, center_z-1, center_x, self.c1.y, center_z+1, 44, 15)

                        # Seats
                        self.mc.setBlocks(center_x+1, self.c1.y, center_z-1, center_x+1, self.c1.y, center_z-1, 156)
                        self.mc.setBlocks(center_x+1, self.c1.y, center_z+1, center_x+1, self.c1.y, center_z+1, 156)
                        self.mc.setBlocks(center_x-1, self.c1.y, center_z-1, center_x-1, self.c1.y, center_z-1, 156, 1)
                        self.mc.setBlocks(center_x-1, self.c1.y, center_z+1, center_x-1, self.c1.y, center_z+1, 156, 1)
                        self.mc.setBlocks(center_x, self.c1.y, center_z-2, center_x, self.c1.y, center_z-2, 156, 3)
                        self.mc.setBlocks(center_x, self.c1.y, center_z+2, center_x, self.c1.y, center_z+2, 156, 2)
                else:
                    self.type = randint(1, 1)
            

            # Carpet
            if self.type == 1:
                self.mc.setBlocks(self.c1.x-2, self.c1.y, self.c1.z-2, self.c2.x+2, self.c1.y, self.c2.z+2, 171, choice([0, 1, 7, 8, 15]))

            

    # Light room
    def light(self):
        
        # If the room area is less then x return
        if (abs(self.c1.x - self.c2.x) * abs(self.c1.z - self.c2.z)) <= 20:
            return

        # Try place light in each corner checking we are not blocking doors
        c1 = Vec3(self.c1.x-1, self.c1.y, self.c1.z-1)
        c2 = Vec3(self.c1.x-1, self.c1.y, self.c2.z+1)
        c3 = Vec3(self.c2.x+1, self.c1.y, self.c1.z-1)
        c4 = Vec3(self.c2.x+1, self.c1.y, self.c2.z+1)
        corners = [c1, c2, c3, c4]
        for c in corners:
            air = 0
            # Check for air blocks around
            if (self.mc.getBlock(c.x-1, c.y, c.z) == 0): air += 1
            if (self.mc.getBlock(c.x+1, c.y, c.z) == 0): air += 1
            if (self.mc.getBlock(c.x, c.y, c.z-1) == 0): air += 1
            if (self.mc.getBlock(c.x, c.y, c.z+1) == 0): air += 1
            if air > 2:
                continue

            # Check spot is free
            if (self.mc.getBlock(c) != 0):
                continue

            # Check if atleast 2 blocks around at not air
            if (self.mc.getBlock(c.x, c.y-1, c.z) != block.WOOD_PLANKS.id):
                continue    
            
            # Build light
            self.mc.setBlocks(c.x, c.y, c.z, c.x, c.y+1, c.z, 85)
            self.mc.setBlocks(c.x, c.y+2, c.z, c.x, c.y+2, c.z, 169)
