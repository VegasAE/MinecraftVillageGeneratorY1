from mcpi import block
from mcpi.vec3 import Vec3
from queue import PriorityQueue
from block import Block
from mcpi_fast_query import alt_picraft_getheight_vrange
from mcpi_fast_query import alt_picraft_getblock_vrange
import math
from time import sleep
import random

class Path:

    def __init__(self, c1, c2, mc, start, displacementMap = [], houseList = []):
        self.mc = mc
        self.villageMap = [] # stores all blocks within village bounds
        self.targetBlocks = [] # stores location of target blocks for quick retrieval
        self.displacementMap = displacementMap # gets this from terraformer class, thanks Caelan
        self.houseList = houseList # gets this from house list with house classes, used for door positions, thanks Tyler
        self.start = start
        self.obstacleIDs = [53, 5, 126, 134, 164, 109, 98, 67, 135, block.TRAPDOOR.id] # building materials used in the houses

        # corners of the perimeter (bounds of village)
        self.c1 = c1
        self.c2 = c2

        # boolean value that is set to true once path is complete
        self.pathComplete = False

        # set the length and width of village bounds
        self.xLength = int(abs(self.c1.x - self.c2.x))
        self.zLength = int(abs(self.c1.z - self.c2.z))

        #path block id
        self.pathBlock = 208

    # The main method that is used to generate paths
    def generatePath(self):



        # c1 is used as the origin for the grid, from which the coords of blocks are calculated
        # as such c1 needs to be the bottom left corner of the village rectangle
        self.c1 = Vec3(min(self.c1.x, self.c2.x), self.c1.y, min(self.c1.z, self.c2.z))
        self.c2 = Vec3(self.c1.x + self.xLength, self.c1.y, self.c1.z + self.zLength)

        # Generates a map of all the blocks in the village area
        self.villageMapGen()

        # Finding the target blocks within village to path to
        self.findTargetBlocks()
        # sleep(30)

        # self.mc.player.setPos(self.start)

        # Finding the majority of obstacle blocks in the map
        self.findObstacles()

        # Goes through all the blocks in the village and finds all the valid neighbours
        for x in range(self.xLength):
            for z in range(self.zLength):
                self.findNeighbours(self.villageMap[x][z], x, z)

        # # Finds the block that correlates the the given starts x and z value
        pos = self.findStartOfPath()


        # If there are valid target blocks then the algorithm will commence
        if (len(self.targetBlocks) != 0):
            for i in range(len(self.targetBlocks)):       
                self.pathComplete = self.aStar(pos, self.targetBlocks[i], self.villageMap)
                print(self.pathComplete)

            # builds the street lights along the path
            self.streetLights()
        else:
            self.mc.postToChat("No path necessary")

    # method uses the given starting position and finds it on the village map so that we may use the height
    def findStartOfPath(self):
        x = int(abs((self.start.x + self.c1.x) - self.c1.x))
        z = int(abs((self.start.z + self.c1.z) - self.c1.z))
        start = self.villageMap[x][z]

        return start
        


    # Static Method that finds most obstacle blocks in map
    def findObstacles(self):
        for x in range(self.xLength):
            for z in range(self.zLength):
                if (self.villageMap[x][z].displacement == -1):
                    self.villageMap[x][z].setObstacle()
                
                if (self.villageMap[x][z].blockID in self.obstacleIDs):
                    self.villageMap[x][z].setObstacle()


    # static method that updates the neighbours for a block
    # I know this is ugly to look at and I apologise
    def findNeighbours(self, current, x, z):
        possibleNeighbours = []
        neighbours = []

        #checks if at top, bottom, far right, far left side of grid
        if (x == 0 and z == 0):
            possibleNeighbours.append(self.villageMap[x + 1][z])
            possibleNeighbours.append(self.villageMap[x][z + 1])

        elif ((x == (self.xLength - 1)) and (z == (self.zLength - 1))):
            possibleNeighbours.append(self.villageMap[x-1][z])
            possibleNeighbours.append(self.villageMap[x][z-1])

        elif((x == 0) and (z == (self.zLength - 1))):
            possibleNeighbours.append(self.villageMap[x+1][z])
            possibleNeighbours.append(self.villageMap[x][z-1])

        elif((x == self.xLength - 1) and (z == 0)):
            possibleNeighbours.append(self.villageMap[x][z+1])
            possibleNeighbours.append(self.villageMap[x-1][z])


        elif (x == 0):
            possibleNeighbours.append(self.villageMap[x+1][z])
            possibleNeighbours.append(self.villageMap[x][z+1])
            possibleNeighbours.append(self.villageMap[x][z-1])

        elif (z == 0):
            possibleNeighbours.append(self.villageMap[x][z+1])
            possibleNeighbours.append(self.villageMap[x+1][z])
            possibleNeighbours.append(self.villageMap[x-1][z])

        elif (x == (self.xLength - 1)):
            possibleNeighbours.append(self.villageMap[x-1][z])
            possibleNeighbours.append(self.villageMap[x][z+1])
            possibleNeighbours.append(self.villageMap[x][z-1])

        elif (z == (self.zLength - 1)):
            possibleNeighbours.append(self.villageMap[x][z-1])
            possibleNeighbours.append(self.villageMap[x+1][z])
            possibleNeighbours.append(self.villageMap[x-1][z])
        
        else:
            possibleNeighbours.append(self.villageMap[x+1][z])
            possibleNeighbours.append(self.villageMap[x][z+1])
            possibleNeighbours.append(self.villageMap[x-1][z])
            possibleNeighbours.append(self.villageMap[x][z-1])


        #checks if any possible neighbours are obstacles and appends them to actual neighbours if they are not
        for n in possibleNeighbours:
            if (n.position.y - current.position.y) > 1:
                n.setObstacle()
            
            elif (current.position.y - n.position.y) < -1:
                n.setObstacle()
            
            if (n.isObstacle() == True) and not (abs((n.position.y - current.position.y)) > 1) and (n.displacement != -1):
                n.resetType()

            # if either block are water, lava, air, or ice then avoid
            if (n.blockID == 0):
                n.setObstacle()
                
            if (n.blockID == block.WATER.id):
                n.setObstacle()

            if (n.blockID == block.LAVA.id):
                n.setObstacle()
            
            if (n.blockID == block.ICE.id):
                n.setObstacle()


            if n.isObstacle() == False:
                neighbours.append(n)
                
        current.setNeighbours(neighbours)

   
    # Static method searches area inside village perimeter for a target block to build a path to and appends location to array define earlier
    def findTargetBlocks(self):
        # USED FOR TESTING PURPOSES
        # # searches the village for the target block
        # TARGETBLOCK = block.DIAMOND_BLOCK.id
        # for x in range(self.xLength):
        #     for z in range(self.zLength):

        #         # Block object ID matches target block ID, append to list of target nodes / blocks 
        #         if (self.villageMap[x][z].blockID == TARGETBLOCK):
        #             self.targetBlocks.append(self.villageMap[x][z])

        doorList = []
        check = [-1, 1]
        for house in self.houseList:
            # print(house.door)
            doorList.append(Block(house.door))
    
        for door in doorList:
            #checks the up and down x positions
            for i in check:
                doorNeighbour = Block(Vec3(door.position.x + i, door.position.y, door.position.z ))
                x = int(abs(doorNeighbour.position.x - self.c1.x))
                z = int(abs(doorNeighbour.position.z - self.c1.z))
    
                #find a valid target block as pathfinding cannot build to door block, checks all directions because of radom house orientation
                self.findNeighbours(doorNeighbour, x, z)
                if (len(doorNeighbour.neighbours) != 0):
                    # only ever gets the block thats two blocks in front of the door
                    self.targetBlocks.append(doorNeighbour.neighbours[0])

            # check the left and right z positions
            for i in check:
                doorNeighbour = Block(Vec3(door.position.x, door.position.y, door.position.z + i ))
                x = int(abs(doorNeighbour.position.x - self.c1.x))
                z = int(abs(doorNeighbour.position.z - self.c1.z))
    
                #find a valid target block as pathfinding cannot build to door block, checks all directions because of radom house orientation
                self.findNeighbours(doorNeighbour, x, z)
                if (len(doorNeighbour.neighbours) != 0):
                    # only ever gets the block thats two blocks in front of the door
                    self.targetBlocks.append(doorNeighbour.neighbours[0])
            




    # Takes two vectors as input, one vector always being the endpoint and the other being the current block the pathfinder is on
    # Using a distance formula for a 3D point on a grid we can calculate the aproximate distance to theendpoint we are path finding to
    # TODO:Might need to check stuff with y-val and how it affects calculating the distance
    def hScore(self, curr, end):
        # hVal = math.sqrt((end.position.x - curr.position.x)**2 + (end.position.y - curr.position.y)**2 + (end.position.z - curr.position.z)**2)    # Euclidean Distance Formula
        hVal = abs(end.position.x - curr.position.x) + abs(end.position.y - curr.position.y) + abs(end.position.z - curr.position.z)   # Manhatten Distance Fomula
        return hVal


    # Finds the f-score of the current block for use in the a* algorithm
    def fScore(self, GScore, HScore):
        fScore = GScore + HScore
        return fScore
    
    # Function creates path blocks using designated path block
    def constructPath(self, cameFrom, current):
        while current in cameFrom:
            self.mc.setBlock(current.position, self.pathBlock)
            current.setID(self.pathBlock)
            for i in current.neighbours:
                if (abs(i.position.y - current.position.y) <= 1):
                    self.mc.setBlock(i.position, self.pathBlock)
                    i.setID(self.pathBlock)
            current = cameFrom[current]

    # An a* Path finding algorithm that has a starting position, currently the players current position, and uses the the targetBlocks list to find the end nodes / blocks to path to
    def aStar(self, start, end, villageMap):
        count = 0
        openSet = PriorityQueue()
        openSet.put((0, count, start))
        cameFrom = {} # keeps track of the path

        # sets all gscores and fScores to infinity initialy
        gScore = {block: math.inf for row in villageMap for block in row}
        gScore[start] = 0
        fScore = {block: math.inf for row in villageMap for block in row}
        fScore[start] = self.hScore(start, end)

        openSetHash = {start} # priority queue doesnt have way to check if theres something in the queue so this is here as a way to check

        while not openSet.empty():
            current = openSet.get()[2]
            openSetHash.remove(current) # does this to help maintain whats been popped out of the priority queue

            if (current == end): # shortest path has been found and makes the path
                self.constructPath(cameFrom, end) # TODO: Create construct path method
                end.setPath()
                return True

            # checking for neighbour direction
            for neighbour in current.neighbours:
                

                neighbourGScore = gScore[current]
                if abs(current.position.y - neighbour.position.y) > 0:
                    neighbourGScore += 1.4 # when block is horizontal or vertical and above / below in height
                elif neighbour.isPath() == True:
                    neighbourGScore += 0.25 # makes the path blocks more desireable and should connect the paths together more cohesively
                else: 
                    neighbourGScore += 1 # when block is horizontal or verticle

                if abs(current.position.y - neighbour.position.y) > 1: # too high and needs to be set as obstacle
                    neighbourGScore = math.inf

                if (neighbour.isObstacle() == True):
                    neighbourGScore = math.inf # wont be able to turn block into path so gScore is set to infinity


                if (neighbourGScore < gScore[neighbour]): # if gScore is lower than neighbour, then this is the better path
                    cameFrom[neighbour] = current # updates block pathing
                    gScore[neighbour] = neighbourGScore
                    fScore[neighbour] = self.fScore(neighbourGScore, self.hScore(neighbour, end))
                    if (neighbour not in openSetHash):
                        count += 1 # is used as a way to determine a tie between f-scores and uses the one put into the queue first
                        openSet.put((fScore[neighbour], count, neighbour))
                        openSetHash.add(neighbour)
                        neighbour.setOpen()
                        # self.mc.setBlock(neighbour.position, 35, 0)
                        # sleep(0.1)

            if (current.position != start.position):
                current.setClosed()
                # self.mc.setBlock(current.position, 35, 14)
                # sleep(0.1)
        
        #no path was found
        return False



    # Static method that generates a map of all the blocks within the village
    def villageMapGen(self):
        heightMap = []
        blockIDMap = []



        # HEIGHT 
        # uses the fast query height function to quickly generate heights for all the blocks within the village bounds
        vRange = []
        for x in range(self.xLength):
            for z in range(self.zLength):
                vRange.append((self.c1.x + x, 0, self.c1.z + z))
        
        
        heightVecs = alt_picraft_getheight_vrange(self.mc, vRange) # call function to quickly generate heights
        

        # transfers heights into a seperate height map
        for i in range(self.xLength):
            xDim = []
            for j in range(self.zLength):
                xDim.append(heightVecs[(i * self.zLength) + j].y)
            heightMap.append(xDim)
        


        # VILLAGE MAP
        # Creates all block objects / nodes in village bounds and adds them to a village map  
        for x in range(self.xLength):
            xDim = []
            for z in range (self.zLength):
                # Currently setting height to zero
                xDim.append(Block(Vec3(self.c1.x + x, heightMap[x][z], self.c1.z + z)))

            self.villageMap.append(xDim)


        # BLOCK IDS
        # uses the fast querey getblock function to quickly gather block ids of all the blocks in the village bounds using 
        bRange = []
        for x in range(self.xLength):
            for z in range(self.zLength):
                bRange.append((self.c1.x + x, heightMap[x][z], self.c1.z + z))
        
        blockIDs = alt_picraft_getblock_vrange(self.mc, bRange)
        
        # Transfers blocks into a seperate blockID map
        for i in range(self.xLength):
            xDim = []
            for j in range(self.zLength):
                xDim.append(blockIDs[(i* self.zLength) +j])
            blockIDMap.append(xDim)


        # SETTING BLOCK IDS TO BLOCK NODES
        # Uses the block.setID method so block stores what minecraft block it is
        for x in range(self.xLength):
            for z in range(self.zLength):
                self.villageMap[x][z].setID(blockIDMap[x][z])

        # SETTING DISPLACMENTS FOR BLOCKS
        for x in range(self.xLength):
            for z in range(self.zLength):
                self.villageMap[x][z].setDisp(self.displacementMap[x][z])
                

    # Method that builds street lights around the path
    def streetLights(self):
        posLightSpots = []
        count = 1

        for x in range(self.xLength):
            for z in range(self.zLength):
                # if the block is an obstacle then skip
                if (self.villageMap[x][z].isObstacle() == False):

                # checks map for blocks that have four neighbours as lightpost needs room on all sides
                    if (len(self.villageMap[x][z].neighbours) == 4) and (self.villageMap[x][z].blockID != self.pathBlock):
                        pathCount = 0
                        for i in self.villageMap[x][z].neighbours:
                            if i.blockID == self.pathBlock:
                                pathCount += 1

                        # Don't want the light posts to be in the middle of the path    
                        if pathCount == 1:
                            posLightSpots.append(self.villageMap[x][z])

        # for i in range(0, len(posLightSpots) - 2):
        #     if posLightSpots[i].position.y - posLightSpots[i+1].position.y > 2:
        #         posLightSpots.pop(i)
            

        
        # for i in posLightSpots:
        #     self.mc.setBlock(i.position, 35, 4)


        # as long as the length of possible light positions isn't zero then build the lights
        if len(posLightSpots) != 0:

            while count <= 15:
                i = random.randint(0, (len(posLightSpots) - 1))
                lightPos = posLightSpots[i]
                self.mc.setBlock(lightPos.position.x, lightPos.position.y + 1, lightPos.position.z, 98, 3)
                self.mc.setBlock(lightPos.position.x, lightPos.position.y + 2, lightPos.position.z, 139, 1)
                self.mc.setBlock(lightPos.position.x, lightPos.position.y + 3, lightPos.position.z, block.FENCE_SPRUCE.id)
                self.mc.setBlock(lightPos.position.x, lightPos.position.y + 4, lightPos.position.z, 154)
                self.mc.setBlock(lightPos.position.x, lightPos.position.y + 5, lightPos.position.z, block.GLOWSTONE_BLOCK.id)
                self.mc.setBlock(lightPos.position.x + 1, lightPos.position.y + 5, lightPos.position.z, block.TRAPDOOR.id, 7)
                self.mc.setBlock(lightPos.position.x - 1, lightPos.position.y + 5, lightPos.position.z, block.TRAPDOOR.id, 6)
                self.mc.setBlock(lightPos.position.x, lightPos.position.y + 5, lightPos.position.z + 1, block.TRAPDOOR.id, 5)
                self.mc.setBlock(lightPos.position.x, lightPos.position.y + 5, lightPos.position.z - 1, block.TRAPDOOR.id, 4)
                self.mc.setBlock(lightPos.position.x, lightPos.position.y + 6, lightPos.position.z, block.TRAPDOOR)

                # TODO: Improve way of removing surrounding light positions
                # removes positions from list and limits the chance of building a light post next to each other
                try:
                    if (i != 0 and i != len(posLightSpots) - 1):
                        posLightSpots.pop(i + 3)
                        posLightSpots.pop(i + 2)
                        posLightSpots.pop(i + 1)
                        posLightSpots.pop(i)
                        posLightSpots.pop(i - 1)
                        posLightSpots.pop(i - 2)
                        posLightSpots.pop(i - 3)

                    elif (i == 0):
                        posLightSpots.pop(i + 3)
                        posLightSpots.pop(i + 2)
                        posLightSpots.pop(i + 1)
                        posLightSpots.pop(i)

                    elif (i == len(posLightSpots) - 1):
                        posLightSpots.pop(i - 3)
                        posLightSpots.pop(i - 2)
                        posLightSpots.pop(i - 1)
                        posLightSpots.pop(i)
                    count += 1
                
                # currently in place so program doesn't break if an index error occurs
                # TODO: Improve method so it doesn't need to worry about this
                except IndexError:
                    break
            

            