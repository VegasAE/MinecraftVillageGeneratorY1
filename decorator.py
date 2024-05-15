from random import randint
from mcpi.vec3 import Vec3

from mcpi_fast_query import alt_picraft_getblock_vrange
# class that uses data and variables from the terraformer function to add decorations around the map
# called after terraforming, house construction, and pathfinding, acts as a final layer
class Decorator():
    def __init__(self, mc, terraformer):
        self.mc = mc
        self.terraformer = terraformer
        self.c1 = terraformer.c1
        self.xLength = terraformer.xLength
        self.zLength = terraformer.zLength

        self.numFarms = 5 # attempts to place this many farms
        self.farmDimensions = (5,10) #the min and max dimensions of a farm, chosen randomly
        self.farmBorders = 2 # farms cant be within x blocks of each other
        self.farmTrials = 50 # number of times it will attempt to place a farm before it gives up
        
        self.wellTrials = 30 # number of times it will attempt to place a well before it gives up
        self.wellSize = 5 # well is x * x

        self.clumpSize = 4 # x * x square of clump
        self.clumpIterations = 3 # will have a 50% change of placing a clump block every iteration
        self.numclumpBales = 5 # will try to place this many clump bales
        self.clumpIds = [4, 30, 13, 15, 16, 48, 49]

    # goes over top layer of map and swaps blocks out for more appropriate ones
    # during terraforming dirt can be brought up to the top layer, for example, when grass blocks are more appropriate
    # ID : ID 
    def TopLayer(self):
        # IDtoChange : IDtoChangeTo
        blockTranslations = {
            3  : 2,
            10 : 8,
            11 : 9,
            14 : 1,
            15 : 1,
            16 : 1
        }

        blocks = []
        for i in range(self.xLength):
            for j in range(self.zLength):
                # real world position of the block
                blocks.append((self.c1.x + i, self.terraformer.heightMap[i][j], self.c1.z + j))
        
        # get the blocks at the top layer of the village
        blockTypes = alt_picraft_getblock_vrange(self.mc, blocks)

        for i in range(len(blocks)):
            for key in blockTranslations:
                if blockTypes[i] == key:
                    self.mc.setBlock(blocks[i], blockTranslations[key])

    # finds location for well and calls function to construct it at that location
    def BuildWell(self):
        placementMap = self.terraformer.GeneratePlacementMap(self.terraformer.displacementMap)
        villageCentre = Vec3(self.xLength / 2, -1, self.zLength / 2)

        # determine location of well
        # find free position closest to centre of the village
        shortestDist = 999
        for x in range(len(self.terraformer.displacementMap) - self.wellSize):
            for z in range(len(self.terraformer.displacementMap[0]) - self.wellSize):
                dist = abs(x - villageCentre.x) + abs(z - villageCentre.z)
                if dist < shortestDist and not self.terraformer.RectIntersects(Vec3(x, -1, z), Vec3(x + self.wellSize, -1, z + self.wellSize), placementMap):
                    shortestDist = dist
                    closestBlock = Vec3(x, -1, z)

        
        if shortestDist != 999:
            # bulldoze for well
            wellBlocks = self.terraformer.CoordsInRect(closestBlock, Vec3(closestBlock.x + self.wellSize, -1, closestBlock.z + self.wellSize))
            avgHeight = self.terraformer.AvgRectHeight(wellBlocks)
            self.terraformer.SetHeights(wellBlocks, [avgHeight] * len(wellBlocks))

            # construct well
            self.WellStructure(closestBlock)

            # mark well as unsmoothable in terraformers displacement map
            for block in wellBlocks:
                self.terraformer.displacementMap[block.x][block.z] = -1
                self.terraformer.UpdateNeighbourDisplacement(block.x, block.z, self.terraformer.displacementMap)
        else:
            print("no well :(")
        

    def BuildFarms(self):
        placementMap = self.terraformer.GeneratePlacementMap(self.terraformer.displacementMap)

        farmLocations = []
        for _ in range(self.numFarms):
            farmX = randint(self.farmDimensions[0], self.farmDimensions[1])
            farmZ = randint(self.farmDimensions[0], self.farmDimensions[1])

            # generate a potential candidate position for the well
            candidate = Vec3(randint(0, self.xLength - farmX), -1, randint(0, self.zLength - farmZ))
            corner2 = Vec3(candidate.x + farmX, -1, candidate.z + farmZ)

            candidates = 1
            while self.terraformer.RectIntersects(candidate, corner2, placementMap) and candidates < self.farmTrials:
                candidate = Vec3(randint(0, self.xLength - farmX), -1, randint(0, self.zLength - farmZ))
                corner2 = Vec3(candidate.x + farmX, -1, candidate.z + farmZ)
                candidates += 1

            if candidates < self.farmTrials:
                self.mc.postToChat(f'Farm placed after {candidates} candidates')
                farmLocations.append((candidate, corner2))

                # farms cant be placed with x blocks of each other
                c1 = Vec3(max(0, candidate.x - self.farmBorders), -1, max(0, candidate.z - self.farmBorders))
                c2 = Vec3(min(self.xLength - 1, corner2.x + self.farmBorders), -1, min(self.zLength - 1, corner2.z + self.farmBorders))
                borders = self.terraformer.CoordsInRect(c1, c2)
                for v in borders:
                    placementMap[v.x][v.z] = -1

                # farms marked as unsmoothable/obstacle
                farmBlocks = self.terraformer.CoordsInRect(candidate, corner2)
                for v in farmBlocks:
                    self.terraformer.displacementMap[v.x][v.z] = -1
                    self.terraformer.UpdateNeighbourDisplacement(v.x, v.z, self.terraformer.displacementMap)

                # print(farmX, farmZ)

        for farm in farmLocations:
            self.FarmStructure(farm)


    def FarmStructure(self, farmCorners):
        # bulldoze
        farmBlocks = self.terraformer.CoordsInRect(farmCorners[0], farmCorners[1])
        avgHeight = self.terraformer.AvgRectHeight(farmBlocks)
        self.terraformer.SetHeights(farmBlocks, [avgHeight] * len(farmBlocks))

        # build farm
        c1 = Vec3(self.c1.x + farmCorners[0].x, self.terraformer.heightMap[farmCorners[0].x][farmCorners[0].z], self.c1.z + farmCorners[0].z)
        c2 = Vec3(self.c1.x + farmCorners[1].x - 1, self.terraformer.heightMap[farmCorners[1].x - 1][farmCorners[1].z - 1], self.c1.z + farmCorners[1].z - 1)

        # farm frame
        for x in range(c1.x, c2.x):
                self.mc.setBlock(Vec3(x, self.terraformer.heightMap[x - self.c1.x][c1.z - self.c1.z] + 1, c1.z), 17)
                self.mc.setBlock(Vec3(x, self.terraformer.heightMap[x - self.c1.x][c2.z - self.c1.z] + 1, c2.z), 17)
                self.mc.setBlock(Vec3(x, self.terraformer.heightMap[x - self.c1.x][c1.z - self.c1.z], c1.z), 17)
                self.mc.setBlock(Vec3(x, self.terraformer.heightMap[x - self.c1.x][c2.z - self.c1.z], c2.z), 17)
        for z in range(c1.z, c2.z):
            self.mc.setBlock(Vec3(c1.x, self.terraformer.heightMap[c1.x - self.c1.x][z - self.c1.z] + 1, z), 17)
            self.mc.setBlock(Vec3(c2.x, self.terraformer.heightMap[c2.x - self.c1.x][z - self.c1.z] + 1, z), 17)
            self.mc.setBlock(Vec3(c1.x, self.terraformer.heightMap[c1.x - self.c1.x][z - self.c1.z], z), 17)
            self.mc.setBlock(Vec3(c2.x, self.terraformer.heightMap[c2.x - self.c1.x][z - self.c1.z], z), 17)
        self.mc.setBlock(Vec3(c2.x, self.terraformer.heightMap[c2.x - self.c1.x][c2.z - self.c1.z] + 1, c2.z), 17)
        self.mc.setBlock(Vec3(c2.x, self.terraformer.heightMap[c2.x - self.c1.x][c2.z - self.c1.z] + 1, c2.z), 17)

        farmType = randint(0, 2)
        if farmType > 0: #plant farm
            # place farmland
            innerc1 = Vec3(c1.x + 1, c1.y, c1.z + 1)
            innerc2 = Vec3(c2.x - 1, c2.y, c2.z - 1)
            self.mc.setBlocks(innerc1, innerc2, 60)

            # place water
            xdim = abs(c1.x - c2.x)
            zDim = abs(c1.z - c2.z)

            if xdim > zDim:
                midP = int((c1.z + c2.z) / 2)
                self.mc.setBlocks(Vec3(c1.x + 1, innerc1.y, midP), Vec3(c2.x - 1, innerc1.y, midP), 9)
                
            else:
                midP = int((c1.x + c2.x) / 2)
                self.mc.setBlocks(Vec3(midP, innerc1.y, c1.z + 1), Vec3(midP, innerc1.y, c2.z - 1), 9)
                
        else: # animal farm: scratch that theres no animals :( just a melon farm
            for x in range(c1.x, c2.x):
                self.mc.setBlock(Vec3(x, self.terraformer.heightMap[x - self.c1.x][c1.z - self.c1.z] + 2, c1.z), 53, 2)
                self.mc.setBlock(Vec3(x, self.terraformer.heightMap[x - self.c1.x][c2.z - self.c1.z] + 2, c2.z), 53, 3)
            for z in range(c1.z, c2.z):
                self.mc.setBlock(Vec3(c1.x, self.terraformer.heightMap[c1.x - self.c1.x][z - self.c1.z] + 2, z), 53, 0)
                self.mc.setBlock(Vec3(c2.x, self.terraformer.heightMap[c2.x - self.c1.x][z - self.c1.z] + 2, z), 53, 1)
            self.mc.setBlock(Vec3(c2.x, self.terraformer.heightMap[c2.x - self.c1.x][c2.z - self.c1.z] + 2, c2.z), 53, 3)

            innerc1 = Vec3(c1.x + 1, c1.y + 1, c1.z + 1)
            innerc2 = Vec3(c2.x - 1, c2.y + 1, c2.z - 1)
            if randint(0,1) == 0:
                self.mc.setBlocks(innerc1, innerc2, 103)
            else:
                self.mc.setBlocks(innerc1, innerc2, 86)

    def WellStructure(self, wellLocation):
        worldLoc = Vec3(self.c1.x + wellLocation.x, self.terraformer.heightMap[wellLocation.x][wellLocation.z], self.c1.z + wellLocation.z)

        # build base
        self.mc.setBlocks(Vec3(worldLoc.x, worldLoc.y - 10, worldLoc.z), Vec3(worldLoc.x + self.wellSize-1, worldLoc.y + 2, worldLoc.z + self.wellSize-1), 4)
        self.mc.setBlocks(Vec3(worldLoc.x + 1, worldLoc.y - 9, worldLoc.z + 1), Vec3(worldLoc.x + self.wellSize - 2, worldLoc.y + 2, worldLoc.z + self.wellSize - 2), 9)

        # build fences
        self.mc.setBlocks(Vec3(worldLoc.x, worldLoc.y + 3, worldLoc.z), Vec3(worldLoc.x, worldLoc.y + 6, worldLoc.z), 85)
        self.mc.setBlocks(Vec3(worldLoc.x, worldLoc.y + 3, worldLoc.z + self.wellSize - 1), Vec3(worldLoc.x, worldLoc.y + 6, worldLoc.z + self.wellSize - 1), 85)
        self.mc.setBlocks(Vec3(worldLoc.x + self.wellSize - 1, worldLoc.y + 3, worldLoc.z), Vec3(worldLoc.x + self.wellSize - 1, worldLoc.y + 6, worldLoc.z), 85)
        self.mc.setBlocks(Vec3(worldLoc.x + self.wellSize - 1, worldLoc.y + 3, worldLoc.z + self.wellSize - 1), Vec3(worldLoc.x + self.wellSize - 1, worldLoc.y + 6, worldLoc.z + self.wellSize - 1), 85)

        # build roof
        self.mc.setBlocks(Vec3(worldLoc.x, worldLoc.y + 7, worldLoc.z), Vec3(worldLoc.x + self.wellSize - 1, worldLoc.y + 7, worldLoc.z + self.wellSize - 1), 44, 3)
        self.mc.setBlocks(Vec3(worldLoc.x + 1, worldLoc.y + 7, worldLoc.z + 1), Vec3(worldLoc.x + self.wellSize - 2, worldLoc.y + 7, worldLoc.z + self.wellSize - 2), 4)
        self.mc.setBlock(Vec3(worldLoc.x + (self.wellSize / 2), worldLoc.y + 8, worldLoc.z + (self.wellSize / 2)), 44, 3)

    def Buildclump(self):
        placementMap = self.terraformer.GeneratePlacementMap(self.terraformer.displacementMap)
        for _ in range(self.numclumpBales):
            # generate a potential candidate position for the clumpbale
            candidate = Vec3(randint(0, self.xLength - self.clumpSize), -1, randint(0, self.zLength - self.clumpSize))
            corner2 = Vec3(candidate.x + self.clumpSize, -1, candidate.z + self.clumpSize)

            candidates = 1
            while self.terraformer.RectIntersects(candidate, corner2, placementMap) and candidates < self.farmTrials:
                candidate = Vec3(randint(0, self.xLength - self.clumpSize), -1, randint(0, self.zLength - self.clumpSize))
                corner2 = Vec3(candidate.x + self.clumpSize, -1, candidate.z + self.clumpSize)
                candidates += 1

            clumpBlocks = self.terraformer.CoordsInRect(candidate, corner2)
            # construct clump
            for block in clumpBlocks:
                for _ in range(self.clumpIterations):
                    if randint(0, 100) > 50:
                        self.mc.setBlock(self.c1.x + block.x, self.terraformer.heightMap[block.x][block.z] + 1, self.c1.z + block.z, self.clumpIds[randint(0, len(self.clumpIds) - 1)])
                        self.mc.setBlock(self.c1.x + block.x, self.terraformer.heightMap[block.x][block.z] + 1, self.c1.z + block.z, 170)
                        self.terraformer.heightMap[block.x][block.z] += 1

            # mark blocks as obstacles/unsmoothable
            for block in clumpBlocks:
                self.terraformer.displacementMap[block.x][block.z] = -1
                for v in self.terraformer.CoordsInRect(Vec3(block.x - 5, -1, block.z - 5), Vec3(block.x + 5, -1, block.z + 5)):
                    placementMap[v.x][v.z] = -1