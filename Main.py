from mcpi.minecraft import Minecraft
from mcpi.vec3 import Vec3
from time import sleep
from Terraformer import Terraformer
from house import House
from path_finding import Path
from random import randint

def Testing():
    mc.postToChat("Lets get crackin'")

    # Use chat commands to test algorithms
    while True:
        messages = mc.events.pollChatPosts()
        for msg in messages:
            # test terraforming algorithm
            if (msg.message.lower() == "display"):
                tf.VisualiseDisplacement()
                
            elif (msg.message.lower() == "tf"):
                # do da terraforming
                c1 = mc.player.getPos()
                c1.x = int(c1.x)
                c1.y = int(c1.y)
                c1.z = int(c1.z)
                tf = Terraformer(c1, Vec3(c1.x + 125, 0, c1.z + 100), mc)
                tf.Terraform()

            elif (msg.message.lower() == "b"):
                # do da terraforming
                c1 = mc.player.getTilePos()
                mc.setBlocks(Vec3(c1.x, mc.getHeight(c1.x, c1.z), c1.z), Vec3(c1.x + randint(3, 12), c1.y + randint(3, 12), c1.z + randint(3, 12)), 1)

            elif (msg.message.lower() == "v"):
                GenerateVillage()
                # FindVillage()
            
            # Build HOUSEEEEEEw
            elif (msg.message.lower() == "house"):

                # Tell them i guess
                mc.postToChat("BUILDING HOUSE...")
                c1 = mc.player.getTilePos()
                c2 = Vec3(c1.x + randint(8,15), c1.y, c1.z + randint(8,15))
                house = House(c1, c2, mc, dir=randint(0,3))

            # Road go brrrrr
            elif (msg.message.lower() == "path"):
                mc.postToChat("Constructing Path")
                c1 = mc.player.getPos()
                c1.x = int(c1.x)
                c1.y = int(c1.y)
                c1.z = int(c1.z)
                path = Path(c1, Vec3(c1.x + 125, 0, c1.z + 100), mc)
                path.villageMapGen()


        sleep(0.01)

# idk what this one does 
def GenerateVillage():
    mc.postToChat("BUILDING VILLAGE. . .")
    mc.postToChat("-   -   -")
    mc.postToChat("Finding suitable village location. . .")

    # find village location and teleport player to location
    c1, ubArea = FindVillage()
    if mc.player.getTilePos() != c1:
        mc.player.setPos(Vec3(c1.x, mc.getHeight(c1.x, c1.z), c1.z))

    # allocate house positions and terraform world
    freeLand = area * (1 - ubArea)
    tf = Terraformer(c1, Vec3(c1.x + villageSize[0], 0, c1.z + villageSize[1]), mc, )
    tf.houseSizes = GenerateHouseSizes(freeLand * landCoverage) #x% of land should be filled with houses
    tf.Terraform()

    # find average block of village
    avgBlock = VillageCentre(tf.housePositions, tf.displacementMap, c1)

    # construct houses
    houseList = ConstructHouses(tf, avgBlock, c1)
    mc.postToChat("Constructed Houses")

    decor = tf.decor
    decor.TopLayer()


    #generate path
    path = Path(c1, Vec3(c1.x + villageSize[0], 0, c1.z + villageSize[1]), mc, avgBlock, tf.displacementMap, houseList)
    path.generatePath()
    mc.postToChat("Constructed Path")

    # decor.Perimeter(tf.perimeterBlocks)

    mc.postToChat("VILLAGE CONSTRUCTED")
    mc.postToChat("-   -   -")

def ConstructHouses(tf, avgBlock, c1):
    # generate houses
    # find centre of houses in order to determine direction to village centre
    houseCentres = [] # finds the centre positions of houses based on their c1s and c2s
    for corners in tf.housePositions:
        houseCentres.append(Vec3(((corners[0].x + corners[1].x) / 2) - c1.x, -1, ((corners[0].z + corners[1].z) / 2) - c1.z))

    # find directions for houses to face
    dirs = []
    for position in houseCentres:
        dir = avgBlock - position
        if abs(dir.x) > abs(dir.z):
            if dir.x > 0:
                dirs.append(0)
            else:
                dirs.append(2)
        else:
            if dir.z > 0:
                dirs.append(1)
            else:
                dirs.append(3)

    # construct houses
    houseList = []
    for i in range(len(tf.housePositions)):
        houseList.append(House(tf.housePositions[i][0], tf.housePositions[i][1], mc, dirs[i]))

    return houseList

# splits an area into houses
def GenerateHouseSizes(area):
    houseSizes = []
    numHouses = 0

    while area >= sizeClamps[1] ** 2 and numHouses < maxHouses:
        newHouse = (randint(sizeClamps[0], sizeClamps[1]), randint(sizeClamps[0], sizeClamps[1]))
        houseArea = newHouse[0] * newHouse[1]
        houseSizes.append(newHouse)
        area -= houseArea
        numHouses += 1

    # mc.postToChat(f"Attempting to place {len(houseSizes)} houses")
    return houseSizes

# finds a suitable location for the village and returns the bounds, first candidate is players position
# incredibly ad hoc last minute inefficient solution
def FindVillage():
    # test right in front of the player
    c1 = mc.player.getTilePos()
    c2 = Vec3(c1.x + villageSize[0], -1, c1.z + villageSize[1])
    ubArea = CalculateUnbuildableArea(c1, c2)
    if ubArea < maxUnbuildable:
        return c1, ubArea

    # if not, then search in a radius
    c1 = mc.player.getTilePos()
    c1.x -= int(villageSearchSize / 2)
    c1.z -= int(villageSearchSize / 2)
    c2 = Vec3(c1.x + villageSearchSize, -1, c1.z + villageSearchSize)
    print(c1, c2)

    # use generateplacement to create map of how much of the land will be unbuildable
    placeholderTerraformer = Terraformer(c1, c2, mc)
    dispMap = placeholderTerraformer.GenerateMaps()[1]
    unbuildableMap = placeholderTerraformer.GeneratePlacementMap(dispMap)

    totalArea = villageSize[0] * villageSize[1]
    tilesConsidered = 0
    cheapest = 1
    cheapestLoc = Vec3(0,0,0)
    for x in range(len(unbuildableMap) - villageSize[0] - 1):
        for z in range(len(unbuildableMap[0]) - villageSize[1] - 1):
            tilesConsidered += 1
            print(tilesConsidered)
            unbuildableCount = 0
            # mc.setBlock(c1.x + x, c1.y - 5, c1.z + z, 35, 15)
            for i in range(villageSize[0]):
                for j in range(villageSize[1]):
                    if unbuildableMap[i][j] < 0:
                        unbuildableCount += 1
            
            unbuildableArea = unbuildableCount / totalArea
            if unbuildableArea < cheapest:
                cheapestLoc = Vec3(c1.x + x, -1, c1.z + z)
                cheapest = unbuildableArea
                if unbuildableArea < maxUnbuildable:
                    print(f"village found after {tilesConsidered} tiles out of {villageSearchSize ** 2} possible tiles")
                    mc.postToChat(f"village found after {tilesConsidered} tiles out of {villageSearchSize ** 2} possible tiles")
                    return (cheapestLoc, unbuildableArea)
    print("suitable village location not found")
    mc.postToChat("suitable village location not found")
    # use cheapest spot and bulldoze trees around it
    return cheapestLoc, cheapest

def CalculateUnbuildableArea(c1, c2):
    # use generateplacement to create map of how much of the land will be unbuildable
    placeholderTerraformer = Terraformer(c1, c2, mc)
    dispMap = placeholderTerraformer.GenerateMaps()[1]
    unbuildableMap = placeholderTerraformer.GeneratePlacementMap(dispMap)

    # count number of blocks that houses cant be placed on
    unbuildableCount = 0
    for i in range(len(unbuildableMap)):
        for j in range(len(unbuildableMap[0])):
            if unbuildableMap[i][j] < 0:
                unbuildableCount += 1
    
    return unbuildableCount / area

# finds the centre of all the houses, used to pathfind and make houses face towards a common location
# called right before houses are constructed, after terraforming has taken place
def VillageCentre(houseCorners, dispMap, c1):
    housePositions = [] # finds the centre positions of houses based on their c1s and c2s
    for corners in houseCorners:
        housePositions.append(Vec3(((corners[0].x + corners[1].x) / 2) - c1.x, -1, ((corners[0].z + corners[1].z) / 2) - c1.z))

    # average the position of all houses to find centrePosition
    avgPos = Vec3(0,0,0)
    for position in housePositions:
        avgPos.x += position.x
        avgPos.z += position.z
    avgPos.x /= len(housePositions)
    avgPos.z /= len(housePositions)
    avgPos.x = int(avgPos.x)
    avgPos.z = int(avgPos.z)

    # find the block closest to centre block that isnt obstacle i.e. water, leaves etc.
    shortestDist = 999
    closestBlock = Vec3(999,0,999)
    for x in range(len(dispMap)):
        for z in range(len(dispMap[0])):
            dist = abs(x - avgPos.x) + abs(z - avgPos.z)
            if dist < shortestDist and dispMap[x][z] > 0:
                shortestDist = dist
                closestBlock = Vec3(x, -1, z)
    
    return closestBlock




# overall variables not specific to any class
villageSize = (125, 100)
area = villageSize[0] * villageSize[1]
sizeClamps = (8, 18) # min and max sizes of a house
maxUnbuildable = 0.6 # must pick a candidate with at most x% of the area that cant be built on e.g. water
landCoverage = 0.2 # % of remaining free land that should be occupied by houses
exploreStep = 100 # the number of blocks the FindVillage() algo moves when trying to find a new location for a village
maxHouses = 7
houseList = [] # list the holds the house objects
villageSearchSize = 350 # search for a suitable place to locate the village in a 1000x1000 square around the player

mc = Minecraft.create()
GenerateVillage()