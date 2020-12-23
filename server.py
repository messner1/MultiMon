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
        self.x = data['x']
        self.y = data['y']
        self._server.sendToPlayer({"action": "rivalPosChange", "x": self.x, "y": self.y, "rivalSprite": data["sprite"], "who": self.nickname})

    def Network_nickname(self, data):
        self.nickname = data['nickname']

    def Network_verifyPasswordCheckCapacity(self, data):
        if self._server.serverOptions["password"] is not None:
            if data["password"] != self._server.serverOptions["password"]:
                self.Send({"action": "error", "error": ["","Wrong Password"]})

        if len(self._server.players) > self._server.serverOptions["max_connects"]:
            self.Send({"action": "error", "error": ["", "Server at Capacity"]})

    def Network_missableObjectsUpdate(self, data):
        mObjState[data["map"]] = data["mObjs"]
        self._server.sendToAll({"action": "objUpdate", "objFlags": mObjState})

    def Network_pokedexUpdate(self, data):
        self._server.sendToPlayer({"action": "lockoutUpdate", "newLockouts": data["lockouts"], "who":self.nickname})

    def Network_badgeUpdate(self, data):
        print("Badge Change")
        print(data["badges"])
        if self._server.serverOptions["badge_win"] in data["badges"]:
            print("Player " + self.nickname + " wins")
            self._server.sendToAll({"action": "gameWin", "player": self.nickname, "condition": self._server.serverOptions["badge_win"]})

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
        player.Send({"action": "getGameOptions", "game_options": {key: value for key, value in self.serverOptions.items() if key != "password"}})
        #a message to other players to force a gamestate update so that this new player can have initial info -- map etc.
        self.sendToPlayer({"action": "forceGamestateUpdate", "who": player.nickname})

    def delPlayer(self, player):
        print("Deleting Player: " + player.nickname)
        del self.players[player]
        print("Players:")
        print(self.players)

    def sendToPlayer(self, data):
        #print([p for p in self.players if p.nickname != data['who']])
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
    parser.add_argument('-password', default=None)
    parser.add_argument('-badge_win', default=None)

    args = parser.parse_args()

    server_options = {"items": args.items, "wilds": args.wilds, "position": args.position,
                      "max_connects": args.max_connections, "password":args.password,
                      "badge_win": args.badge_win
                      }

    pserve = PokeServer(localaddr=(args.host, args.port))
    pserve.launch(server_options)

