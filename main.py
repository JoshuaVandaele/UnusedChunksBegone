#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import libs.anvilparser.anvil as anvil

_VERSION_21w43a = 2844 # Version where "Level" was removed from chunk

def getChunkVersion(chunk: anvil.Chunk) -> int:
    """
    Used to know the chunk version.

    This function uses the chunk's "DataVersion" value.

    Parameters
    ----------
    chunk : anvil.Chunk
        Chunk to check the version from.

    Returns
    -------
    int
        * 0 For version from 1.17 and prior
        * 1 For version from 1.18 and up.
    """
    if chunk["DataVersion"].value < _VERSION_21w43a:
        return 0 # 1.17-
    else:
        return 1 # 1.18+

def seventeenChecks(chunk: anvil.Chunk) -> bool: # 1.17 Checks
    """
    Used for checks prior to the 1.18 chunk format change.

    This function simply checks if a chunk is useless using a few known critters:

    * Has "Biomes" been generated? If not, this means the chunk hasn't been populated yet.
    * Does the chunk have an "InhabitedTime" over 0? If not, this means the chunk has never been loaded by a player.

    Parameters
    ----------
    chunk : anvil.Chunk
        Chunk to verify.

    Returns
    -------
    bool
        Weither the chunk is considered useless or not.

    See Also
    --------
    eighteenChecks : Checks for the 1.18+ versions.
    """
    return (
        "Biomes" in chunk["Level"] # Chunk has been loaded
        and chunk["Level"]["InhabitedTime"].value > 0 # Chunk has been visisted
        )

def eighteenChecks(chunk: anvil.Chunk) -> bool: # 1.18 Checks
    """
    Used for checks after the 1.18 chunk format change.

    This function simply checks if a chunk is useless using a few known critters:

    * Has the chunk "Status" been set to full? If not, this means the chunk hasn't been populated yet.
    * Does the chunk have an "InhabitedTime" over 0? If not, this means the chunk has never been loaded by a player.

    Parameters
    ----------
    chunk : anvil.Chunk
        Chunk to verify.

    Returns
    -------
    bool
        Weither the chunk is considered useless or not.

    See Also
    --------
    seventeenChecks: Checks for the 1.17- versions.
    """
    return (
        chunk["Status"].value == "full" # Minecraft thinks the chunk has been fully populated/loaded
        and chunk["InhabitedTime"].value > 0 # Chunk has been visited/loaded by a player
        )

def removeEmptyChunks(regionX: str, regionZ: str, directory: str) -> anvil.EmptyRegion:
    """
    Used to filter out useless chunks from a region file, given it's X and Y position, and it's directory.

    Parameters
    ----------
    regionX : str
        The region's X position.
    regionY : str
        The region's Y position.
    directory : str
        The region file's directory.

    Returns
    -------
    anvil.EmptyRegion
        The new, filtered region.
    None
        The function returns None if the filtered region is completely empty.

    Examples
    --------
    >>> removeEmptyChunks("-1","0","./world/regions/")
    libs.anvilparser.anvil.empty_region.EmptyRegion object
    """
    region = anvil.Region.from_file(directory+'r.'+regionX+"."+regionZ+'.mca')
    newRegion = anvil.EmptyRegion(regionX,regionZ)
    isEmpty = True
    for chunkX in range(0,32):
        for chunkZ in range(0,32):
            chunk = region.chunk_data(chunkX,chunkZ)
            if chunk:
                ver = getChunkVersion(chunk)
                if ver == 0 and seventeenChecks(chunk):
                    newRegion.add_chunk(anvil.Chunk.from_region(region,chunkX,chunkZ))
                    isEmpty = False
                elif ver == 1 and eighteenChecks(chunk):
                    newRegion.add_chunk(anvil.Chunk.from_region(region,chunkX,chunkZ))
                    isEmpty = False
    if isEmpty:
        return None
    else:
        return newRegion

if __name__ == "__main__":
    import os
    import re
    from multiprocessing.pool import ThreadPool as Pool
    import multiprocessing

    inputDir = "./input/"
    outputDir = "./output/"

    def worker(regionCoords: tuple[str, str]) -> None:
        filename = "r."+regionCoords[0]+"."+regionCoords[1]+".mca"
        region = removeEmptyChunks(regionCoords[0],regionCoords[1], inputDir)
        if region:
            print(filename+" has been cleaned! Saving..")
            region.save(outputDir+filename)
        else:
            print("Removing file '"+filename+"' as it contains nothing but empty chunks.")

    with Pool(multiprocessing.cpu_count()) as pool:
        regions = []
        for item in os.scandir(inputDir):
            if item.path.endswith(".mca") and item.is_file(): # if it's a mca file...
                regionCoords = re.findall(r'r\.(-?\d+)\.(-?\d+)\.mca',item.name)[0] # Extract the region coordinates from the file name
                if regionCoords:
                    regions.append(regionCoords)
        pool.map(worker,regions)

    print("Done!")