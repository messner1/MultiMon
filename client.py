
import os
os.environ["PYSDL2_DLL_PATH"] = "C:\\Users\\Craig\\Desktop\\Multimon\\"

from pyboy import PyBoy
import argparse
from PodSixNet.Connection import connection, ConnectionListener

from pkdefs import pokedexOwned, badgesOwned

from constants import *


class pokeInstance(ConnectionListener):

    def __init__(self, rom_path, name, host, port, savestate, password):
        self.pyboy = PyBoy(rom_path)

        if savestate:
            file_like_object = open(savestate, "rb")
            self.pyboy.load_state(file_like_object)

        self.host = host
        self.port = port

        self.currMap = -1
        self.x = 0
        self.y = 0

        self.rivalMap = -1
        self.rivalX = 0
        self.rivalY = 0
        self.rivalFacing = 0
        self.rivalSpriteNum = 15

        self.prevmoFlags = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.rivalSprite = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.sprite = []

        #initial dex
        self.pokedex = pokedexOwned([self.pyboy.get_memory_value(t) for t in range(POKEDEX_RANGE_START,POKEDEX_RANGE_END+1)])

        #list of wild pokemon locked out by opp
        self.lockedOutWilds = []

        #initial badges
        self.badges = badgesOwned(self.pyboy.get_memory_value(BADGES_ACQUIRED))

        #game options
        self.gameOptions = None

        #connect to server and send nickname
        self.Connect((self.host, self.port))
        connection.Send({"action": "nickname", "nickname": name})

        #reaaal basic passwording here
        connection.Send({"action": "verifyPasswordCheckCapacity", "password": password})


    #insert a sprite block into memory at the sprite location (two 16 byte chunks at C100 and C200
    def setViewSprite(self, offset, data):
        block_1_offset = 0xC100
        block_2_offset = 0xC200
        sprite_increment = 0x0010

        sprite_id = offset * sprite_increment

        for index, byte in enumerate(data[0:16]):
            self.pyboy.set_memory_value(block_1_offset+sprite_id+index, byte)

        for index, byte in enumerate(data[16:32]):
            self.pyboy.set_memory_value(block_2_offset+sprite_id+index, byte)


    #get the data of the given sprite number, so the sprite at the offset X
    def getViewSprites(self, sprite_num):
        block_1_offset = 0xC100
        block_2_offset = 0xC200
        sprite_increment = 0x0010


        sprite_id = sprite_num * sprite_increment
        if(self.pyboy.get_memory_value(block_1_offset + sprite_id) != 0):
            sprite_info = [self.pyboy.get_memory_value(block_1_offset + sprite_id + inc) for inc in range(0,16)]
            sprite_info_2 = [self.pyboy.get_memory_value(block_2_offset + sprite_id + inc) for inc in range(0,16)]

            return sprite_info+sprite_info_2

        else:
            return []

    #Dex used to track caught pokemon for wild catch lockout
    def checkPokedexUpdate(self):
        #this range contains the "owned" pokedex
        newDex = pokedexOwned([self.pyboy.get_memory_value(t) for t in range(POKEDEX_RANGE_START, POKEDEX_RANGE_END+1)])
        if self.pokedex.dex != newDex.dex:
            print("dex update")
            self.pokedex.dex = newDex.dex
            self.Send({"action": "pokedexUpdate", "lockouts":self.pokedex.createLockouts()})

    def missableObjectsFlags(self):
        #Flags for missable objects -- lockout
        mFlags = [self.pyboy.get_memory_value(rangeLoc) for rangeLoc in range(START_MISSABLE_RANGE, END_MISSABLE_RANGE+1)]
        if mFlags != self.prevmoFlags:
            self.Send({"action": "missableObjectsUpdate", "mObjs": mFlags, "map": self.currMap})
            self.prevmoFlags = mFlags

    def checkMapChange(self):
        if self.currMap != self.pyboy.get_memory_value(MAP_NUMBER): #map number memory value
            self.Send({"action": "mapChange", "newMap": self.pyboy.get_memory_value(MAP_NUMBER)})
            self.currMap = self.pyboy.get_memory_value(MAP_NUMBER)

            #if we change maps, check for an unused slot in which to put the rival sprite
            for sp in range(2,15):
                potentialSprite = self.getViewSprites(sp)
                if potentialSprite and potentialSprite[0] == 0:
                    self.rivalSpriteNum = sp
                    break

    def updatePos(self):
        newx = self.pyboy.get_memory_value(0xD362)
        newy = self.pyboy.get_memory_value(0xD361)
        if self.sprite != self.getViewSprites(0):
        #if self.y != newy or self.x != newx:
            self.y = newy
            self.x = newx
            self.sprite = self.getViewSprites(0)
            connection.Send({"action": "updatePos", "x": self.x, "y": self.y, "sprite": self.sprite})

    def checkInBattleIfLockedOut(self):
        #could also only grab new lockout when a battle triggers
        #cfe5 pokemon id in battle
        #d057 battle type -- 1 for wild
        #just make catch rate 0? (D007) Use the unidentified ghost thing?
        #ghosts use same id,
        #currently just use catch rate 0 solution, though this should not fully work due to status effects

        #testing confirms that master ball and statused pokemon can still be caught. latter should be easy to hack -- just
        #make it so they can't be statused if they are a caught wild. former is harder, as it is a subroutine run before
        #the catch calculation
        if self.pyboy.get_memory_value(BATTLE_TYPE) == WILD_POKEMON_BATTLE:
            if self.pyboy.get_memory_value(POKEMON_ID) in self.lockedOutWilds:
                self.pyboy.set_memory_value(CATCH_RATE, 0x00)
                # c3ae-c3b3 -- upper right of battle screen, use tiles to write "caught" there if locked out
                for index, adr in enumerate(range(0xC3AE, 0xC3B4)):
                    self.pyboy.set_memory_value(adr, CAUGHT_MESSAGE[index])

    def checkRivalInView(self):
        if self.rivalMap == self.currMap:
            #print('same map')
            #print(self.x, self.rivalX, self.y, self.rivalY)
            #tl 0,0 br 128, 144 (yx)
            #so if the difference in positions is zero, then the rival should be (pixelwise) at 64, 72
            adjx = (72 + (self.rivalX - self.x) * 16) - 4
            adjy = (64 + (self.rivalY - self.y) * 16) - 4   #always adjusted by 4 to appear central in tile. Not sure about X

            #48 down, 52 up, 56 left, 60 right
            #for player 0 down, 4 up, 8 left, 12 right
            self.rivalSprite[4] = adjy
            self.rivalSprite[6] = adjx

            if adjy >= 0 and adjy <= 128 and adjx >=0 and adjx < 136:
                self.setViewSprite(self.rivalSpriteNum, self.rivalSprite)
                #self.setViewSprite(self.rivalSpriteNum, [1, 2, self.rivalFacing, 0, adjy, 0, adjx, 0, 0, 12, 96, 64, 0, 0, 0, 0, 0, 0, 8, 8, self.rivalY, self.rivalX, 255, 0, 22, 0, 0, 0, 0, 0, 1, 0])
            else:
                self.setViewSprite(self.rivalSpriteNum, [0 for a in range(0,32)])

    def sendBadgesIfChanged(self):
        potential_badges = self.badges.checkBadgeUpdate(self.pyboy.get_memory_value(BADGES_ACQUIRED))
        if potential_badges is not False:
            self.Send({"action": "badgeUpdate", "badges": potential_badges})


    #NETWORK CALLBACKS

    def Network_getGameOptions(self, data):
        self.gameOptions = data["game_options"]
        print("Game Options:")
        print(self.gameOptions)

    def Network_rivalMapChange(self, data):
        self.rivalMap = data["rivalMap"]

    def Network_rivalPosChange(self, data):
        self.rivalX = data['x']
        self.rivalY = data['y']
        self.rivalSprite = data["rivalSprite"]

    def Network_objUpdate(self, data):
        print("Recieved mflags", data["objFlags"])
        if self.currMap in data["objFlags"]:
            startMissableRange = 0xD5A6
            endMissableRange = 0xD5C5
            for flag, rangeLoc in zip(data["objFlags"][self.currMap], range(startMissableRange, endMissableRange+1)):
                self.pyboy.set_memory_value(rangeLoc, flag)

    def Network_lockoutUpdate(self, data):
        self.lockedOutWilds = data["newLockouts"]
        print("lockouts: ")
        print(self.lockedOutWilds)

    def Network_connected(self, data):
        print("Connected to server at ", self.host)

    def Network_error(self, data):
        print('error:', data['error'][1])
        connection.Close()

    def Network_disconnected(self, data):
        print('Disconnected')
        exit()



    def run(self):
        while not self.pyboy.tick():
            if self.gameOptions:
                self.checkMapChange()
                if self.gameOptions["position"]:
                    self.updatePos()
                    self.checkRivalInView()
                if self.gameOptions["items"]:
                    self.missableObjectsFlags()
                if self.gameOptions["wilds"]:
                    self.checkPokedexUpdate()
                    self.checkInBattleIfLockedOut()
                if self.gameOptions["badge_win"]:
                    self.sendBadgesIfChanged()
            connection.Pump()
            self.Pump()
        connection.Close()


def main(rom_path, name, host, port, savestate, password):
    instance = pokeInstance(rom_path, name, host, port, savestate, password)
    instance.run()


if __name__ == '__main__':


    parser = argparse.ArgumentParser()
    parser.add_argument('rom_path')
    parser.add_argument('name')
    parser.add_argument('hostname')
    parser.add_argument('port', type=int)
    parser.add_argument('-savestate', default=None)
    parser.add_argument('-password', default=None)

    args = parser.parse_args()

    main(args.rom_path, args.name, args.hostname, args.port, args.savestate, args.password)