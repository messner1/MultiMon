#MEMORY ADDRESSES

#The range for the "owned" pokemon data in the pokedex.
POKEDEX_RANGE_START = 0xD2F7
POKEDEX_RANGE_END = 0xD309

#The range for skippable objects -- includes floor items and events. A flagfield.
START_MISSABLE_RANGE = 0xD5A6
END_MISSABLE_RANGE = 0xD5C5

MAP_NUMBER = 0xD35E

#A string that displays "Caught" in the battle tileset
CAUGHT_MESSAGE = [0x82, 0x80, 0x94, 0x86, 0x87, 0x93]

#Battle type (Trainer etc.) Wild pokemon most important for our purposes
BATTLE_TYPE = 0xd057
WILD_POKEMON_BATTLE = 1

#ID number of pokemon when in battle with it
POKEMON_ID = 0xCFE5

#Catch rate for pokemon in encounter -- theoretically setting it to zero isn't a perfect solution (status effect/master ball)
CATCH_RATE = 0xD007

#Constants for sprite data.
SPRITE_BLOCK_1_OFFSET = 0xC100
SPRITE_BLOCK_2_OFFSET = 0xC200
SPRITE_INCREMENT = 0x0010