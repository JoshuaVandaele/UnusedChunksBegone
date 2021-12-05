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

def optimiseChunk(chunk,chunkVer):
    """
    Optimise singular chunks.

    This is accomplished by deleting pre-calculated/cached data.

    Parameters
    ----------
    chunk : anvil.Chunk
        Chunk to verify.

    Returns
    -------
    anvil.Chunk
        Optimised chunk.

    See Also
    --------
    optimiseRegion: Optimise an entire region file.
    """
    if chunkVer == 0: # 1.17-
        if "Heightmaps" in chunk["Level"]:
            del chunk["Level"]["Heightmaps"]
        if "isLightOn" in chunk["Level"]:
            del chunk["Level"]["isLightOn"]
    elif chunkVer == 1: # 1.18+
        if "Heightmaps" in chunk:
            del chunk["Heightmaps"]
        if "isLightOn" in chunk:
            del chunk["isLightOn"]
    return chunk

def optimiseRegion(regionX: str, regionZ: str, directory: str, optimiseChunks: bool) -> anvil.EmptyRegion:
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
    optimiseChunks : bool
        Also optimise singular chunks or not?

    Returns
    -------
    anvil.EmptyRegion
        The new, filtered region.
    None
        The function returns None if the filtered region is completely empty.

    Examples
    --------
    >>> optimiseRegion("-1","0","./world/regions/",True)
    libs.anvilparser.anvil.empty_region.EmptyRegion object

    See Also
    --------
    optimiseChunk: Optimize a singular chunk.
    """
    region = anvil.Region.from_file(directory+'r.'+regionX+"."+regionZ+'.mca')
    newRegion = anvil.EmptyRegion(regionX,regionZ)
    isEmpty = True
    for chunkX in range(0,32):
        for chunkZ in range(0,32):
            chunk = region.chunk_data(chunkX,chunkZ)

            if chunk: # If a chunk exists at those chunk coordinates
                ver = getChunkVersion(chunk) # Get it's version
                if ver == 0 and seventeenChecks(chunk):
                    if optimiseChunks:
                        chunk = optimiseChunk(chunk,0) # Optimise the chunk itself if asked
                    newRegion.add_chunk(anvil.Chunk(chunk)) # Add the chunk to the proper position in the new, optimized region
                    isEmpty = False
                elif ver == 1 and eighteenChecks(chunk):
                    if optimiseChunks:
                        chunk = optimiseChunk(chunk,1) # Optimise the chunk itself if asked
                    newRegion.add_chunk(anvil.Chunk(chunk)) # Add the chunk to the proper position in the new, optimized region
                    isEmpty = False
    if isEmpty:
        return None
    return newRegion

if __name__ == "__main__":
    import sys
    import os
    import re
    from multiprocessing.pool import ThreadPool as Pool
    import multiprocessing

    settings = {
        "noKeep": False,
        "inputDir": "./input/",
        "outputDir": "./output/",
        "optimiseChunks": False
    }

    if "-nokeep" in sys.argv:
        settings["noKeep"] = True

    if "-optimisechunks" in sys.argv:
        settings["optimiseChunks"] = True

    if "-input" in sys.argv:
        settings["inputDir"] = sys.argv[sys.argv.index("-input")+1]

    if "-output" in sys.argv:
        settings["outputDir"] = sys.argv[sys.argv.index("-output")+1]

    if not settings["inputDir"].endswith("/") or not settings["inputDir"].endswith("\\"): # Ensure it's a directory
        settings["inputDir"]+="/"

    if not settings["outputDir"].endswith("/") or not settings["outputDir"].endswith("\\"): # Ensure it's a directory
        settings["outputDir"]+="/"

    if not os.path.exists(settings["outputDir"]): # Ensure the directory exists
        os.makedirs(settings["outputDir"])

    if not os.path.exists(settings["inputDir"]): # Ensure the directory exists
        os.makedirs(settings["inputDir"])


    def worker(regionCoords: tuple) -> None:
        filename = "r."+regionCoords[0]+"."+regionCoords[1]+".mca"
        region = optimiseRegion(regionCoords[0],regionCoords[1], settings["inputDir"], settings["optimiseChunks"])
        if region:
            print(filename+" has been cleaned! Saving..")
            region.save(settings["outputDir"]+filename)
            if settings["noKeep"]:
                os.remove(settings["inputDir"]+filename)
        else:
            print("Removing file '"+filename+"' as it contains nothing but empty chunks.")

    with Pool(multiprocessing.cpu_count()) as pool:
        regions = []
        for item in os.scandir(settings["inputDir"]):
            if item.path.endswith(".mca") and item.is_file(): # if it's a mca file...
                regionCoords = re.findall(r'r\.(-?\d+)\.(-?\d+)\.mca',item.name)[0] # Extract the region coordinates from the file name
                if regionCoords:
                    regions.append(regionCoords)
        pool.map(worker,regions)

    print("Done!")