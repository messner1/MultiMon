from dataclasses import dataclass
from constants import *

@dataclass(order=True)
class sprite:
    pic_id: int = 0
    movement_status: int = 0
    image_index: int = 0
    ystepv: int = 0
    ypixels: int = 0
    xstepv: int = 0
    xpixels: int = 0
    intraframecount: int = 0
    animframecount: int = 0
    facing: int = 0
    yadj: int = 0
    xadj: int = 0
    collision: int = 0
    un0d: int = 0
    un0e: int = 0
    un0f: int = 0

    # second block
    walkanimcount: int = 0
    un01: int = 0
    ydis: int = 0
    xdis: int = 0
    mapy: int = 0
    mapx: int = 0
    movebyte1: int = 0
    grass: int = 0
    movementdelay: int = 0
    origfacing: int = 0
    un0a: int = 0
    un0b: int = 0
    un0c: int = 0
    picid2: int = 0
    imagebaseoffset: int = 0
    un0f2: int = 0


#table to convert pokedex number to pokemon id number (used by wild encounter tables). index is dex number, value is id number

dexIdTable = [
    0x99,   #bulbasaur
    0x09,
    0x9A,
    0xB0,   #charmander
    0xB2,
    0xB4,
    0xB1,   #squirtle
    0xB3,
    0x1C,
    0x7B,   #caterpie
    0x7C,
    0x7D,
    0x70,   #weedle
    0x71,
    0x72,
    0x24,   #pidgey
    0x96,
    0x97,
    0xA5,   #rat
    0xA6,
    0x05,
    0x23,
    0x6C,
    0x2D,
    0x54,   #chu
    0x55,
    0x60,
    0x61,
    0x0F,   #nidoran
    0xA8,
    0x10,
    0x03,
    0xA7,
    0x07,
    0x04,   #clefairy
    0x8E,
    0x52,
    0x53,
    0x64,
    0x65,
    0x6B,   #zubat
    0x82,
    0xB9,
    0xBA,
    0xBB,
    0x6D,   #paras
    0x2E,
    0x41,
    0x77,
    0x3B,
    0x76,
    0x4D,   #meowth
    0x90,
    0x2F,
    0x80,
    0x39,
    0x75,
    0x21,
    0x14,
    0x47,   #poliwag
    0x6E,
    0x6F,
    0x94,
    0x26,
    0x95,
    0x6A,   #machop
    0x29,
    0x7E,
    0xBC,
    0xBD,
    0xBE,
    0x18,
    0x9B,
    0xA9,   #geodude
    0x27,
    0x31,
    0xA3,
    0xA4,
    0x25,
    0x08,
    0xAD,   #magnemite
    0x36,
    0x40,
    0x46,
    0x74,
    0x3A,
    0x78,
    0x0D,   #grimer
    0x88,
    0x17,
    0x8B,
    0x19,   #gastly
    0x93,
    0x0E,
    0x22,
    0x30,
    0x81,
    0x4E,
    0x8A,
    0x06,   #voltorb
    0x8D,
    0x0C,
    0x0A,
    0x11,
    0x91,
    0x2B,
    0x2C,
    0x0B,
    0x37,   #koffing
    0x8F,
    0x12,
    0x01,
    0x28,
    0x1E,
    0x02,
    0x5C,   #horsea
    0x5D,
    0x9D,
    0x9E,
    0x1B,
    0x98,
    0x2A,
    0x1A,   #scyther
    0x48,
    0x35,
    0x33,
    0x1D,
    0x3C,
    0x85,   #magikarp
    0x16,
    0x13,
    0x4C,
    0x66,
    0x69,
    0x68,
    0x67,
    0xAA,
    0x62,   #omanyte
    0x63,
    0x5A,
    0x5B,
    0xAB,
    0x84,
    0x4A,   #articuno
    0x4B,
    0x49,
    0x58,
    0x59,
    0x42,
    0x83,
    0x15
]



class pokedexOwned:
    #memory range D2F7-D309, bitmasked in blocks of 7

    #in hex:
    #00 = Non, 01 = 1st only, 02 = 2nd only, 03 = 1st + 2nd, 04 = 3rd only, 05 = 1 + 3, 06 = 2 +3
    #07 = first 3, 08 = 4th only, 09 = 1st + 4th, 10 = 5th only, 11 = 1 + 5, 12 = 2+5, 13 = 1+2+5

    #so turn to bin, flip, count position of the on bits

    def __init__(self, initial_block):

        self.dex = self.decodePokedex(initial_block)

    #pokedex in ram -> unrolled python list bitfield
    def decodePokedex(self, pokedexFlagBlock):
        newDex = []
        for pkBlock in pokedexFlagBlock:
            decodedBlock = [int(t) for t in bin(pkBlock)[2:]]
            decodedBlock.reverse()
            paddedBlock = decodedBlock + [0 for t in range(0,8-len(decodedBlock))] #pad with zeroes if not correct length
            newDex += paddedBlock

        return newDex

    #generate list of wild ids that should be locked out based on the dex
    def createLockouts(self):
        return [dexIdTable[index] for index, isCaught in enumerate(self.dex) if isCaught == 1]

#Index into bitfield stored at memory location. If bit is 1, badge has been obtained. Little endian.
badges = [
    "BoulderBadge",
    "CascadeBadge",
    "ThunderBadge",
    "RainbowBadge",
    "SoulBadge",
    "MarshBadge",
    "VolcanoBadge",
    "EarthBadge"
]

class badgesOwned:
    def __init__(self, initial_block):
        self.badges = self.decodeBadges(initial_block)


    def decodeBadges(self, block):
        #Same process as pokedex. Reverse due to little-endian-ness
        bin_rep = [int(t) for t in format(block, 'b')]
        bin_rep.reverse()
        padded = bin_rep + [0 for t in range(0,8-len(bin_rep))]
        return [badges[index] for index, value in enumerate(padded) if value == 1]

    def checkBadgeUpdate(self, block):
        new_badges = self.decodeBadges(block)
        if self.badges != new_badges:
            self.badges = new_badges
            return self.badges
        else:
            return False

