
import os
os.environ["PYSDL2_DLL_PATH"] = "C:\\Users\\Craig\\Desktop\\Multimon\\"

from pyboy import PyBoy
import argparse
from PodSixNet.Connection import connection, ConnectionListener


class pokeInstance(ConnectionListener):

    def __init__(self, rom_path, name):
        self.currMap = -1
        self.x = 0
        self.y = 0

        self.rivalMap = -1
        self.rivalX = 0
        self.rivalY = 0
        self.rivalFacing = 0



        self.pyboy = PyBoy(rom_path)
        self.Connect(('localhost', 1000))
        connection.Send({"action": "nickname", "nickname": name})


    def setViewSprite(self, offset, data):
        block_1_offset = 0xC100
        block_2_offset = 0xC200
        sprite_increment = 0x0010

        sprite_id = offset * sprite_increment

        for index, byte in enumerate(data[0:16]):
            self.pyboy.set_memory_value(block_1_offset+sprite_id+index, byte)

        for index, byte in enumerate(data[16:32]):
            self.pyboy.set_memory_value(block_2_offset+sprite_id+index, byte)



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







    def checkMapChange(self):
        if self.currMap != self.pyboy.get_memory_value(0xD35E): #map number memory value
            self.Send({"action": "mapChange", "newMap": self.pyboy.get_memory_value(0xD35E)})
            self.currMap = self.pyboy.get_memory_value(0xD35E)

    def updatePos(self):
        newx = self.pyboy.get_memory_value(0xD362)
        newy = self.pyboy.get_memory_value(0xD361)
        facing = self.pyboy.get_memory_value(0xC102)
        if self.y != newy or self.x != newx:
            self.y = newy
            self.x = newx
            connection.Send({"action": "updatePos", "x": self.x, "y": self.y, "facing": facing})

    def Network_rivalMapChange(self, data):
        self.rivalMap = data["rivalMap"]

    def Network_rivalPosChange(self, data):
        self.rivalX = data['x']
        self.rivalY = data['y']
        self.rivalFacing = data['facing']

    def checkRivalInView(self):
        if self.rivalMap == self.currMap:
            print('same map')
            print(self.x, self.rivalX, self.y, self.rivalY)
            #tl 0,0 br 128, 144 (yx)
            #so if the difference in positions is zero, then the rival should be (pixelwise) at 64, 72
            adjx = 72 + (self.rivalX - self.x) * 16
            adjy = 64 + (self.rivalY - self.y) * 16
            print(self.rivalY, self.rivalX, adjy, adjx)

            #48 down, 52 up, 56 left, 60 right
            #for player 0 down, 4 up, 8 left, 12 right
            if adjy >= 0 and adjy <= 128 and adjx >=0 and adjx < 136:
                self.setViewSprite(15, [1, 2, self.rivalFacing, 0, adjy, 0, adjx, 0, 0, 12, 96, 64, 0, 0, 0, 0, 0, 0, 8, 8, self.rivalY, self.rivalX, 255, 0, 22, 0, 0, 0, 0, 0, 1, 0])
            else:
                self.setViewSprite(15, [0 for a in range(0,32)])

    def run(self):
        while not self.pyboy.tick():
            self.checkMapChange()
            self.updatePos()
            self.checkRivalInView()
            connection.Pump()
            self.Pump()


def main(rom_path, name):
    instance = pokeInstance(rom_path, name)
    instance.run()
    #pyboy = PyBoy(rom_path)
    #while not pyboy.tick():
     #   #connection.Send({"action": "mapChange", "mapNum": pyboy.get_memory_value(0xD35E)})
      #  print("seconds:", pyboy.get_memory_value(0xDA44)) #game timer
       # print("map:",pyboy.get_memory_value(0xD35E)) #map number
       # print("x",pyboy.get_memory_value(0xD361)) #x
       # print("y",pyboy.get_memory_value(0xD362)) #y


if __name__ == '__main__':


    parser = argparse.ArgumentParser()
    parser.add_argument('rom_path')
    parser.add_argument('name')
    args = parser.parse_args()

    main(args.rom_path, args.name)