from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from time import sleep
import argparse

from pkdefs import pokedexOwned

mObjState = {}

class ClientChannel(Channel):

    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)

        self.nickname = "anonymous"
        self.x = -1
        self.y = -1
        self.map = -1
        self.facing = 0


    def Network(self, data):
        print(data)

    def Network_mapChange(self, data):
        print("mapChange:", data)
        self.map = data['newMap']
        self._server.sendToPlayer({"action": "rivalMapChange", "rivalMap": self.map, "who": self.nickname})

        #send missable items obj to self on mapchange
        self.Send({"action": "objUpdate", "objFlags": mObjState})

    def Network_updatePos(self, data):
        print("updatePos:", data)
        self.x = data['x']
        self.y = data['y']
        self.facing = data['facing']
        self._server.sendToPlayer({"action": "rivalPosChange", "x": self.x, "y": self.y, "facing": self.facing, "who": self.nickname})

    def Network_nickname(self, data):
        self.nickname = data['nickname']

    def Network_missableObjectsUpdate(self, data):
        mObjState[data["map"]] = data["mObjs"]
        self._server.sendToAll({"action": "objUpdate", "objFlags": mObjState})

    def Network_pokedexUpdate(self, data):
        self._server.sendToPlayer({"action": "lockoutUpdate", "newLockouts": data["lockouts"], "who":self.nickname})



class PokeServer(Server):

    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.players = {}

    def Connected(self, channel, addr):
        print('new connection:', channel)
        self.addPlayer(channel)

    def addPlayer(self, player):
        print("New Player" + str(player.addr))
        self.players[player] = True
        print(self.players)

    def sendToPlayer(self, data):
        print([p for p in self.players if p.nickname != data['who']])
        [p.Send(data) for p in self.players if p.nickname != data['who']]

    def sendToAll(self, data):
        [p.Send(data) for p in self.players]

    def launch(self):
        print("Server Launched")
        while True:
            self.Pump()
            sleep(0.001)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('port', type=int)
    args = parser.parse_args()

    pserve = PokeServer(localaddr=(args.host, args.port))
    pserve.launch()

