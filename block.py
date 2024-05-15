# class for blocks found during path finding
class Block():
    
    # position is the coordinates as a Vec3
    # type represents whether or not the block is an obstacle or if it's been checked (closed) or not (open)
    # neighbours is a collection of all blocks next to it in a square radius
    def __init__(self, position):
        self.position = position
        self.blockID = None
        self.neighbours = []
        self.displacement = 0

        # only releavent for path finding
        self.type = None

    # sets the height of the blocks
    def setID(self, id):
        self.blockID = id

    # sets the displacement of the block
    def setDisp(self, disp):
        self.displacement = disp




    # returns true if in closed set / already checked
    def isClosed(self):
        return self.type == "CLOSED"

    # returns true if in open set / hasn't been checked yet
    def isOpen(self):
        return self.type == "OPEN"

    # returns true if block is obstacle and cannot be checked
    def isObstacle(self):
        return self.type == "OBSTACLE"

    #returns true if block is of type path
    def isPath(self):
        return self.type == "PATH"
    





    # sets the block type to closed
    def setClosed(self):
        self.type = "CLOSED"

    # sets the block type to open
    def setOpen(self):
        self.type = "OPEN"

    #sets the block type as an obstacle
    def setObstacle(self):
        self.type = "OBSTACLE"

    #sets the block type as a path
    def setPath(self):
        self.type = "PATH"





    # resets the block type
    def resetType(self):
        self.type = None

    # sets list of neighbours
    def setNeighbours(self, neighbours):
        self.neighbours = neighbours