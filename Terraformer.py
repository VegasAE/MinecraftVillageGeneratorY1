from math import sqrt
from random import randint
from mcpi import block
from time import sleep
from mcpi.vec3 import Vec3
from decorator import Decorator
from mcpi_fast_query import alt_picraft_getblock_vrange, alt_picraft_getheight_vrange

class Terraformer:
    def __init__(self, c1, c2, mc):
        self.mc = mc
        self.displacementMap = []
        self.heightMap = [] # store the heights for quick retrieval, mc calculates it much slower

        # initialise corner variables
        self.c1 = c1
        self.c2 = c2

        # calculate the length and width of the area to terraform
        self.xLength = int(abs(self.c1.x - self.c2.x))
        self.zLength = int(abs(self.c1.z - self.c2.z))

        # the lower this value the smoother the terraformer will make the map, min of 0.75
        self.maxSmoothness = 1
        # IDs of blocks that are not to be smoothed over
        self.unsmoothables = [18, 8, 9, 10, 11, 39, 40, 110, 161, 79]
        # sometimes smoothing gets stuck, if smoothing iterations has passed this then just stop
        self.maxSmoothingIterations = 30
        # max times to attempt to place a house
        self.maxCandidateTrials = 500

        # houses must be allocated at least x blocks from a border to avoid issues
        # in fact they have to be this distance from anything unsmoothable
        self.distFromBorder = 3
        # dist from other houses
        self.houseSpacing = 15

        # variables related to bulldozing for houses, likely passed from main or tyler
        # in the form (length, width)
        self.houseSizes = []

        # the c1s and c2s of the houses
        self.housePositions = []

    def Terraform(self):
        # c1 is used as the origin for the grid, from which the coords of blocks are calculated
        # as such c1 needs to be the bottom left corner of the village rectangle
        self.c1 = Vec3(min(self.c1.x, self.c2.x), self.c1.y, min(self.c1.z, self.c2.z))
        self.c2 = Vec3(self.c1.x + self.xLength, self.c1.y, self.c1.z + self.zLength)

        self.GenerateMaps()
        self.mc.postToChat("Generated Maps")
        
        corners = self.AllocateHouses() # [(Vec3, Vec3), (Vec3, Vec3), ...]
        self.housePositions = [(Vec3(self.c1.x + c[0].x, self.heightMap[c[0].x][c[0].z] + 1, self.c1.z + c[0].z), Vec3(self.c1.x + c[1].x - 1, self.heightMap[c[1].x][c[1].z] + 1, self.c1.z + c[1].z -1)) for c in corners]

        # place wells and farms using the decor class
        # involves bulldozing so is done before smoothing
        self.decor = Decorator(self.mc, self)
        self.decor.BuildWell()
        self.decor.BuildFarms()
        self.decor.Buildclump()

        self.SmoothMap()

    # method that creates 2 int grids where the x,z pos in the grid corresponds to world pos of c1 + (x,0,z)
    # the value held in each cell of disMap corresponds to the difference between the blocks height and its neighbours avg height
    # the value held in each cell of the height map is simply the height, allows for faster retrieval than mc.getHeight
    def GenerateMaps(self):        
        # generate heightMap
        # alt_picraft_getheight_vrange takes an iterable of tuples representing (x,y,z)
        # and returns an iterable of Vec3s in the same order, where the y value of the vec3 is the highest block at x,z
        # generate iterable of vec3s of the area to find height map of
        vrange = []
        for x in range(self.xLength):
            for z in range(self.zLength):
                vrange.append((self.c1.x + x, 0, self.c1.z + z))
        
        heightVecs = alt_picraft_getheight_vrange(self.mc, vrange) # call function to quickly generate heights

        # transfer from heightvects to heightmap
        for i in range(self.xLength):
            xDim = []
            for j in range(self.zLength):
                xDim.append(heightVecs[(i * self.zLength) + j].y)
            self.heightMap.append(xDim)
        # self.mc.postToChat("Generated Height Map")

        # generate displacement map
        for i in range(self.xLength):
            xDim = []
            for j in range(self.zLength):
                if (i == 0 or i == self.xLength - 1 or j == 0 or j == self.zLength - 1): # if on edge its unsmoothable, save time
                    xDim.append(-1)
                else:
                    xDim.append(abs(self.heightMap[i][j] - self.AvgNeighbourHeight(i, j)))
            self.displacementMap.append(xDim)
        # self.mc.postToChat("Generated Displacement Map")

        # assign unsmoothable blocks
        # get list of blocks using fast query
        blocks = alt_picraft_getblock_vrange(self.mc, [(v[0], self.heightMap[v[0] - self.c1.x][v[2] - self.c1.z], v[2]) for v in vrange])

        # set blocks to unsmoothable in displacement map
        for i in range(self.xLength):
            for j in range(self.zLength):
                worldx = self.c1.x + i
                worldz = self.c1.z + j

                # if in unsmoothables, set unsmoothable
                if (blocks[(i * self.zLength) + j] in self.unsmoothables):
                    self.displacementMap[i][j] = -1

                    # if its a leaf then the blocks around it shld also be unsmoothable
                    if (blocks[(i * self.zLength) + j] == 18):
                        if (i == 0):
                            self.displacementMap[i+1][j] = -1
                        elif (i == len(self.heightMap) - 1):
                            self.displacementMap[i-1][j] = -1
                        else:
                            self.displacementMap[i+1][j] = -1
                            self.displacementMap[i-1][j] = -1

                        if (j == 0):
                            self.displacementMap[i][j+1] = -1
                        elif (j == len(self.heightMap[0]) - 1):
                            self.displacementMap[i][j-1] = -1
                        else:
                            self.displacementMap[i][j+1] = -1
                            self.displacementMap[i][j-1] = -1

                # if on the edge, unsmoothable and place a perimeter wall
                if (i == 0 or i == self.xLength - 1 or j == 0 or j == self.zLength - 1):
                    self.displacementMap[i][j] = -1

        # self.mc.postToChat("Identified unsmoothable blocks")

        return self.heightMap, self.displacementMap

    # takes as input the coord of a block and returns the difference between the blocks height and its neighbours avg height
    def GetDisplacement(self, x, z):
        # tiles assigned with -1 dont get smoothed
        if self.displacementMap[x][z] < 0:
            return self.displacementMap[x][z]

        thisHeight = self.heightMap[x][z]
        displacement = abs(thisHeight - self.AvgNeighbourHeight(x, z))
        return displacement

    # helper function, places wool blocks corresponding to displacement
    def VisualiseDisplacement(self):
        for x in range (self.xLength):
            for z in range(self.zLength):
                displacement = self.displacementMap[x][z]
                thisHeight = self.heightMap[x][z]
                # visualise the smoothness in game
                worldx = self.c1.x + x
                worldz = self.c1.z + z
                if (displacement == 0):
                    self.mc.setBlock(worldx,thisHeight,worldz, 35, 0)
                elif (displacement == 0.25):
                    self.mc.setBlock(worldx,thisHeight,worldz, 35, 3)
                elif (displacement == 0.5):
                    self.mc.setBlock(worldx,thisHeight,worldz, 35, 9)
                elif (displacement == 0.75):
                    self.mc.setBlock(worldx,thisHeight,worldz, 35, 11)
                elif (displacement == 1):
                    self.mc.setBlock(worldx,thisHeight,worldz, 35, 4)
                elif (displacement == 1.25):
                    self.mc.setBlock(worldx,thisHeight,worldz, 35, 1)
                elif (displacement == 1.5):
                    self.mc.setBlock(worldx,thisHeight,worldz, 35, 14)
                else:
                    self.mc.setBlock(worldx,thisHeight,worldz, 35, 15)

    # takes x and z and returns the average height of the 4 neighbours
    def AvgNeighbourHeight(self, x, z):
        neighbourHeightTotal = 0 

        # in the case of using the getHeight function, need the world coords of this block rather than the grid coords
        worldx = self.c1.x + x
        worldz = self.c1.z + z
        
        # need to check if x,z is on a wall/corner and therefore 1-2 of its neighbours are not in the heightmap
        # add height of blocks above and below on x to the total
        if (x == 0):
            neighbourHeightTotal += alt_picraft_getheight_vrange(self.mc, [(worldx-1, 0, worldz)])[0].y   
            # neighbourHeightTotal += self.mc.getHeight(worldx-1, worldz)  
            neighbourHeightTotal += self.heightMap[x+1][z]
        elif (x == len(self.heightMap) - 1):
            neighbourHeightTotal += alt_picraft_getheight_vrange(self.mc, [(worldx+1, 0, worldz)])[0].y 
            # neighbourHeightTotal += self.mc.getHeight(worldx+1, worldz)
            neighbourHeightTotal += self.heightMap[x-1][z]
        else:
            neighbourHeightTotal += self.heightMap[x+1][z]
            neighbourHeightTotal += self.heightMap[x-1][z]

        # add height of blocks left and right on z to the total
        if (z == 0):
            neighbourHeightTotal += alt_picraft_getheight_vrange(self.mc, [(worldx, 0, worldz-1)])[0].y 
            # neighbourHeightTotal += self.mc.getHeight(worldx, worldz-1)
            neighbourHeightTotal += self.heightMap[x][z+1]
        elif (z == len(self.heightMap[0]) - 1):
            neighbourHeightTotal += alt_picraft_getheight_vrange(self.mc, [(worldx, 0, worldz+1)])[0].y 
            # neighbourHeightTotal += self.mc.getHeight(worldx, worldz+1)
            neighbourHeightTotal += self.heightMap[x][z-1]
        else:
            neighbourHeightTotal += self.heightMap[x][z+1]
            neighbourHeightTotal += self.heightMap[x][z-1]

        neighbourAvg = neighbourHeightTotal / 4.0
        return neighbourAvg
        

    # take a wild guess
    def SmoothMap(self):
        self.mc.postToChat("Terraforming. . .")

        numIterations = 0
        while not self.IsSmooth() and numIterations < self.maxSmoothingIterations:
            self.Smooth()
            numIterations += 1
            # sleep(0.5)

        self.mc.postToChat(f'Finished Terraforming in {numIterations} iterations')
        print("Done")

    # Searches through all cells in displacementMap, returns false if a block exists that is NOT SMOOTH ENOUGH >:(
    def IsSmooth(self):
        for x in range (self.xLength):
            for z in range(self.zLength):
                if (self.displacementMap[x][z] >= self.maxSmoothness):
                    return False
        return True

    # searches thru dispMap and smoothes the blocks above maxSmooth
    def Smooth(self):
        print('SMOOTHING')
        # changes are put into map copy
        mapCopy = self.displacementMap.copy()
        toCorrect = [] # list of coords we are going to change the height of i.e. coords at which disp > maxSmoothness

        # find the coords that need height to be corrected
        for x in range (self.xLength):
            for z in range(self.zLength):
                if (self.displacementMap[x][z] >= self.maxSmoothness):
                    toCorrect.append(Vec3(x, -1, z))
                    
        # correct the heights: done in batch for speed
        self.SetHeights(toCorrect, [round(self.AvgNeighbourHeight(c.x, c.z)) for c in toCorrect])

        # for coords that were corrected, fix displacement and update neighbours
        for c in toCorrect:
            mapCopy[c.x][c.z] = self.GetDisplacement(c.x, c.z)
            self.UpdateNeighbourDisplacement(c.x, c.z, mapCopy)

        # copy map copy over to displacement map
        self.displacementMap = mapCopy

    # takes in a coord, and updates the displacement of all neighbours of this tile
    def UpdateNeighbourDisplacement(self, x, z, map):
        # update the displacement of neighbours, taking into account edge cells
                    if (x == 0):
                        map[x+1][z] = self.GetDisplacement(x+1, z)           
                    elif (x == len(self.heightMap) - 1):
                        map[x-1][z] = self.GetDisplacement(x-1, z)    
                    else:
                        map[x+1][z] = self.GetDisplacement(x+1, z)
                        map[x-1][z] = self.GetDisplacement(x-1, z)   
                    
                    if (z == 0):
                        map[x][z+1] = self.GetDisplacement(x, z+1)           
                    elif (z == len(self.heightMap[0]) - 1):
                        map[x][z-1] = self.GetDisplacement(x, z-1)    
                    else:
                        map[x][z+1] = self.GetDisplacement(x, z+1)
                        map[x][z-1] = self.GetDisplacement(x, z-1)

    # takes a iterable of coords (Vec3) of a cell in height/disp map and changes heights in the real world
    # done in a batch like this to save time
    # sometimes it gets in an infinite loop, idk y, so theres a max recursion depth of 20
    def SetHeights(self, coords, heights, recursDepth=1):

        # get the blocktypes such that blocks can be added to height
        blockTypes = alt_picraft_getblock_vrange(self.mc, [(self.c1.x + c.x, self.heightMap[c.x][c.z], self.c1.z + c.z) for c in coords])
        # delete and add blocks in the world
        for i in range(len(coords)):
            currHeight = self.heightMap[coords[i].x][coords[i].z]
            worldx = self.c1.x + coords[i].x
            worldz = self.c1.z + coords[i].z

            if currHeight > heights[i]: # delete all blocks above height
                self.mc.setBlocks(worldx,currHeight, worldz, worldx, heights[i] + 1, worldz, 0)
                self.heightMap[coords[i].x][coords[i].z] = heights[i]

            elif currHeight < heights[i]: # add blocks to height
                blockType = blockTypes[i]
                self.mc.setBlocks(worldx, currHeight, worldz, worldx, heights[i], worldz, blockType)
                self.heightMap[coords[i].x][coords[i].z] = heights[i]


        # returns iterable of Vec3s where y is the height at that x and z in real world
        realHeights = alt_picraft_getheight_vrange(self.mc, [(self.c1.x + c.x, -1, self.c1.z + c.z) for c in coords])
        # if a block is now air, we need to check for this and reassign the height
        blockTypes = alt_picraft_getblock_vrange(self.mc, [(self.c1.x + coords[c].x, self.heightMap[coords[c].x][coords[c].z], self.c1.z + coords[c].z) for c in range(len(coords))])

        # i shouldnt need this... because the block found at the location by realHeights should NEVER be air by definition
        # but for some reason it sometimes is, and that messes with the algorithm so i just perform another check that it isnt air
        blockTypesRealHeight = alt_picraft_getblock_vrange(self.mc, [(self.c1.x + coords[c].x, realHeights[c].y, self.c1.z + coords[c].z) for c in range(len(coords))])

        coordsToFix = []
        correspondingHeights = []
        for i in range(len(coords)):
            # when destroying blocks, the underlying block might be air, if so then fix it !!
            blockType = blockTypes[i]
            if blockType == 0: # air
                # print("AIR")
                # self.mc.postToChat("AIR")
                self.heightMap[coords[i].x][coords[i].z] = realHeights[i].y #this fucks up the displacement, cause the height isnt where it was supposed to be

                block = blockTypesRealHeight[i]
                if block != 0: #i shouldnt have to check this but for some reason i do
                    # append the details of these blocks to lists such that the heights can be batch reset
                    coordsToFix.append(Vec3(coords[i].x, -1, coords[i].z))
                    correspondingHeights.append(heights[i])               

            elif blockType in self.unsmoothables: # if u revealed something that shldnt be smoothed
                    self.displacementMap[coords[i].x][coords[i].z] = -1

        # fix the heights of coords where there was an underlying air block
        if len(coordsToFix) > 0:
            
            
            # for some reason it gets into an infinite loop when it adds something with 0, which shldnt be possible
            if recursDepth < 5:
                if (len(coordsToFix) != 1):
                    self.SetHeights(coordsToFix, correspondingHeights, recursDepth + 1)                    
                    # print(self.mc.getBlock(self.c1.x + coordsToFix[0].x, correspondingHeights[0], self.c1.z + coordsToFix[0].z))
                elif self.mc.getBlock(self.c1.x + coordsToFix[0].x, correspondingHeights[0], self.c1.z + coordsToFix[0].z) != 0:
                    self.SetHeights(coordsToFix, correspondingHeights, recursDepth + 1) 
                else:
                    # self.mc.postToChat("eliminated problem")
                    print(coordsToFix)
            else:
                # print("ERROR: MAXIMUM RECURSION DEPTH REACHED IN GETHEIGHTS FUNCTION")
                # self.mc.postToChat("! ! ! - ERROR ERROR ERROR ERROR ERROR - ! ! !")
                self.mc.postToChat("ERROR: MAXIMUM RECURSION DEPTH REACHED IN GETHEIGHTS FUNCTION")
                # self.mc.postToChat("! ! ! - ERROR ERROR ERROR ERROR ERROR - ! ! !")

    # Bulldozes land for houses and returns a list of corners for the houses to be used for construction
    def AllocateHouses(self):
        # decide locations of houses
        houseCorners = self.HouseLocations()
        
        # bulldoze space for the houses in the world
        for house in houseCorners:
            c1 = house[0]
            c2 = house[1]

            coordsList = self.CoordsInRect(c1, c2) # coords of the house
            avgHeight = self.AvgRectHeight(coordsList)
            # self.mc.player.setPos(self.c1.x + c1.x, avgHeight + 1, self.c1.z + c1.z)f
            # bufferCoords = self.CoordsInRect(Vec3(c1.x - platBuffer, -1, c1.z - platBuffer), Vec3(c2.x + platBuffer, -1, c2.z + platBuffer)) #coords around the house
            bufferCoords = self.GenerateEllipse(c1, c2) # coords in an ellipse around the house
            
            # self.mc.setBlocks(self.c1.x + c1.x, self.heightMap[c1.x][c1.z], self.c1.z + c1.z, self.c1.x + c2.x - 1, self.heightMap[c2.x][c2.z], self.c1.z + c2.z - 1, 103) # for testing purposes

            # restrict blocks to be within the bounds
            for block in bufferCoords:
                block.x = max(min(block.x, self.xLength - 1), 1) # clamp x to within allowed range
                block.z = max(min(block.z, self.zLength - 1), 1) # clamp z to within allowed range
                
            # prevent bulldozing of water and trees and stufe
            remove = []
            for i in range(len(bufferCoords)):
                # if its an unsmoothable then dont bulldoze this
                if self.displacementMap[bufferCoords[i].x][bufferCoords[i].z] < 0:
                    remove.append(bufferCoords[i])
            for coord in remove:
                bufferCoords.remove(coord)

            self.SetHeights(bufferCoords, [avgHeight] * len(bufferCoords)) # set the height of all blocks for house and around house

            # set blocks
            for block in coordsList:
                self.displacementMap[block.x][block.z] = -1

            for block in bufferCoords:
                self.UpdateNeighbourDisplacement(block.x, block.z, self.displacementMap)

        # return the location of houses for other methods
        return houseCorners

    
    # returns a [(Vec3, Vec3), (Vec3, Vec3), ...] of locations for the houses
    def HouseLocations(self):
        self.mc.postToChat(f"Attempting to place {len(self.houseSizes)} houses")
        houseCorners = []
        placementMap = self.GeneratePlacementMap(self.displacementMap)

        failedPlacements = 0
        for house in self.houseSizes:
            houseX = house[0]
            houseZ = house[1]

            # generate a potential candidate position for a house
            candidate = Vec3(randint(0, self.xLength - (houseX + self.distFromBorder)), -1, randint(0, self.zLength - (houseZ + self.distFromBorder)))
            corner2 = Vec3(candidate.x + houseX, -1, candidate.z + houseZ)

            # check and regenerate potential positions for a house until it is a valid placement
            candidates = 1
            while self.RectIntersects(candidate, corner2, placementMap) and candidates < self.maxCandidateTrials:
                candidates += 1
                candidate = Vec3(randint(0, self.xLength - (houseX + self.distFromBorder)), -1, randint(0, self.zLength - (houseZ + self.distFromBorder)))
                corner2 = Vec3(candidate.x + houseX, -1, candidate.z + houseZ)
            
            if candidates < self.maxCandidateTrials:
                # add house to list
                self.mc.postToChat(f'House allocated after {candidates} candidates')
                houseCorners.append((candidate, corner2))

                # ensure other houses cant be placed within x blocks of this
                c1 = Vec3(max(0, candidate.x - self.houseSpacing), -1, max(0, candidate.z - self.houseSpacing))
                c2 = Vec3(min(self.xLength - 1, corner2.x + self.houseSpacing), -1, min(self.zLength - 1, corner2.z + self.houseSpacing))
                borders = self.CoordsInRect(c1, c2)

                for v in borders:
                    placementMap[v.x][v.z] = -1

            else:
                # self.mc.postToChat(f'ERROR: FAILED TO ALLOCATE HOUSE!!')
                failedPlacements += 1

        self.mc.postToChat(f'Failed to allocate {failedPlacements} houses')
        return houseCorners

    # generates the map used to place houses in the world
    # a -1 indicates a place where the house cannot intersect
    # houses cannot intersect trees, water, borders, or each other, within an x block radius
    def GeneratePlacementMap(self, dispMap):
        # create map to hold valid areas for houses to be placed
        placementMap = []
        for _ in range(self.xLength):
            xDim = []
            for _ in range(self.zLength):
                xDim.append(0)
            placementMap.append(xDim)
        
        # search for tiles that cannot have houses e.g. water, trees and mark areas in x radius around them as unplaceable too
        for x in range(self.xLength):
            for z in range(self.zLength):
                if dispMap[x][z] == -1: # if something cannot have houses placed on it
                    # ensure that houses cannot be placed in a x * x radius around it
                    c1 = Vec3(max(0, x - self.distFromBorder), -1, max(0, z - self.distFromBorder))
                    c2 = Vec3(min(self.xLength - 1, x + self.distFromBorder), -1, min(self.zLength - 1, z + self.distFromBorder))
                    borders = self.CoordsInRect(c1, c2)

                    for v in borders:
                        placementMap[v.x][v.z] = -1

        return placementMap

    # returns true if the rect defined by c1:c2 intersects a -1 on the map, and therefore it cannot be placed there
    def RectIntersects(self, c1, c2, map):
        points = self.CoordsInRect(c1, c2)
        for block in points:
            if map[block.x][block.z] == -1:
                return True
        return False

    # takes in two grid coordinates and returns a list of GRID coords (used in the maps) of all blocks between those vector points
    def CoordsInRect(self, c1, c2):
        coordList = []

        xLength = abs(c1.x - c2.x)
        zLength = abs(c1.z - c2.z)

        for i in range(xLength):
            for j in range(zLength):
                coordList.append(Vec3(c1.x + i, self.heightMap[c1.x + i][c1.z + j], c1.z + j))
        
        return coordList

    # takes in a list of vec3 coordinates and returns the average y value
    def AvgRectHeight(self, coordsList):
        total = 0
        for v in coordsList:
            total += v.y
        total /= len(coordsList)
        return int(total)

    # takes in corners of a rectangle and returns an ellipse that (very) roughly fits around it
    def GenerateEllipse(self, c1, c2):
        rect = (abs(c1.x - c2.x), abs(c1.z - c2.z)) # (y, x) corresponds to (x, z)
        elipse = (rect[1]/(2**1/2), rect[0]/(2**1/2)) # (a, b)
        mid = (rect[1] / 2, rect[0] / 2) # (h, k)

        # ((x - h)^2) / a^2 + ((y - k)^2) / b^2 = 1 #formula for elipse
        # rearranged for y when h = k = 0
        # y = +/- bsqrt(1-(x/a)^2)
        # adding h and k
        # y = +/-bsqrt(1-((x-h)/a)^2) + k

        a, b = elipse[0], elipse[1]
        h, k = mid[0], mid[1]

        elipseBlocks = []
        for x in range(int(h-a), int(h+a) + 1):
            yPos = b * sqrt(abs(1-(((x-h)/a)**2))) + k

            yNeg = -b * sqrt(abs(1-(((x-h)/a)**2))) + k

            for i in range(int(yNeg), int(yPos) + 1):
                blockWPos = Vec3(c1.x + i, -1, c1.z + x)
                elipseBlocks.append(blockWPos)

        return elipseBlocks