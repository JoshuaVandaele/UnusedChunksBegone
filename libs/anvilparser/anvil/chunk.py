from nbt import nbt
from .region import Region


# This version removes block state value stretching from the storage
# so a block value isn't in multiple elements of the array
_VERSION_20w17a = 2529

# This is the version where "The Flattening" (https://minecraft.gamepedia.com/Java_Edition_1.13/Flattening) happened
# where blocks went from numeric ids to namespaced ids (namespace:block_id)
_VERSION_17w47a = 1451

# This is the version where the height limit was increased from 0 - 255 to -64 -319
_VERSION_21w06a = 2694

# This is the version where chunk's "Level" was removed and everything it contains were moved
_VERSION_21w43a = 2844

def bin_append(a, b, length=None):
    """
    Appends number a to the left of b
    bin_append(0b1, 0b10) = 0b110
    """
    length = length or b.bit_length()
    return (a << length) | b

def nibble(byte_array, index):
    value = byte_array[index // 2]
    if index % 2:
        return value >> 4
    else:
        return value & 0b1111

class Chunk:
    """
    Represents a chunk from a ``.mca`` file.

    Note that this is read only.

    Attributes
    ----------
    x: :class:`int`
        Chunk's X position
    z: :class:`int`
        Chunk's Z position
    version: :class:`int`
        Version of the chunk NBT structure
    data: :class:`nbt.TAG_Compound`
        Raw NBT data of the chunk
    tile_entities: :class:`nbt.TAG_Compound`
        ``self.data['TileEntities']`` as an attribute for easier use
    """
    __slots__ = ('version', 'data', 'x', 'z', 'tile_entities')

    def __init__(self, nbt_data: nbt.NBTFile):
        self.version : int = nbt_data['DataVersion'].value

        if self.version < _VERSION_21w43a:
            self.data = nbt_data['Level']
            self.tile_entities = self.data['TileEntities']
        else:
            self.data = nbt_data
            self.tile_entities = self.data['block_entities']
        self.x = self.data['xPos'].value
        self.z = self.data['zPos'].value

    @classmethod
    def from_region(cls, region: (str | Region), chunk_x: int, chunk_z: int):
        """
        Creates a new chunk from region and the chunk's X and Z

        Parameters
        ----------
        region
            Either a :class:`anvil.Region` or a region file name (like ``r.0.0.mca``)

        Raises
        ----------
        anvil.ChunkNotFound
            If a chunk is outside this region or hasn't been generated yet
        """
        if isinstance(region, str):
            region = Region.from_file(region)
        nbt_data = region.chunk_data(chunk_x, chunk_z)  # type: ignore
        return cls(nbt_data)
