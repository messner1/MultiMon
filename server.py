from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
from time import sleep
import argparse



mObjState = {}

class ClientChannel(Channel):

    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)

        self.nickname = "anonymous"
        self.x = 0
        self.y = 0
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
        self._server.sendToPlayer({"action": "rivalPosChange", "x": self.x, "y": self.y, "rivalSprite": data["sprite"], "who": self.nickname})

    def Network_nickname(self, data):
        self.nickname = data['nickname']

    def Network_missableObjectsUpdate(self, data):
        mObjState[data["map"]] = data["mObjs"]
        self._server.sendToAll({"action": "objUpdate", "objFlags": mObjState})

    def Network_pokedexUpdate(self, data):
        self._server.sendToPlayer({"action": "lockoutUpdate", "newLockouts": data["lockouts"], "who":self.nickname})

    def Close(self):
        self._server.delPlayer(self)


class PokeServer(Server):

    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.players = {}
        self.serverOptions = None

    def Connected(self, channel, addr):
        print('new connection:', channel)
        self.addPlayer(channel)

    def addPlayer(self, player):
        print("New Player" + str(player.addr))
        self.players[player] = True
        print(self.players)
        player.Send({"action": "getGameOptions", "game_options": self.serverOptions})

    def delPlayer(self, player):
        print("Deleting Player: " + player.nickname)
        del self.players[player]
        print("Players:")
        print(self.players)

    def sendToPlayer(self, data):
        print([p for p in self.players if p.nickname != data['who']])
        [p.Send(data) for p in self.players if p.nickname != data['who']]

    def sendToAll(self, data):
        [p.Send(data) for p in self.players]

    def launch(self, server_options):
        print("Server Launched")
        print("Game Options:")
        print(server_options)
        self.serverOptions = server_options
        while True:
            self.Pump()
            sleep(0.001)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('port', type=int)
    parser.add_argument('-items', action='store_true', default=False)
    parser.add_argument('-wilds', action='store_true', default=False)
    parser.add_argument('-position', action='store_true', default=False)
    parser.add_argument('-max_connections', type=int, default=2)
    parser.add_argument('-password', default = None)

    args = parser.parse_args()

    server_options = {"items": args.items, "wilds": args.wilds, "position": args.position, "max_connects": args.max_connections, "password":args.password}

    pserve = PokeServer(localaddr=(args.host, args.port))
    pserve.launch(server_options)

