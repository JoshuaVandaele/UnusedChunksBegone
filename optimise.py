#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usage: python optimise.py <args\>

Please read the README for more information.

Examples
--------
>>> python optimise.py -nokeep
"""
import libs.anvilparser.anvil as anvil

_VERSION_21w43a = 2844  # Version where "Level" was removed from chunk


def get_chunk_version(chunk: anvil.Chunk) -> int:
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
        return 0  # 1.17-
    return 1  # 1.18+


def seventeen_checks(chunk: anvil.Chunk) -> bool:  # 1.17 Checks
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
    eighteen_checks : Checks for the 1.18+ versions.
    """
    return (
        # Chunk has been loaded
        "Biomes" in chunk["Level"]
        # Chunk has been visited
        and chunk["Level"]["InhabitedTime"].value > 0
    )


def eighteen_checks(chunk: anvil.Chunk) -> bool:  # 1.18 Checks
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
    seventeen_checks: Checks for the 1.17- versions.
    """
    return (
        # Minecraft thinks the chunk has been fully populated/loaded
        chunk["Status"].value == "full"
        # Chunk has been visited/loaded by a player
        and chunk["InhabitedTime"].value > 0
    )


def optimise_chunk(chunk, chunk_ver):
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
    optimise_region: Optimise an entire region file.
    """
    if chunk_ver == 0:  # 1.17-
        if "Heightmaps" in chunk["Level"]:
            del chunk["Level"]["Heightmaps"]
        if "isLightOn" in chunk["Level"]:
            del chunk["Level"]["isLightOn"]
    elif chunk_ver == 1:  # 1.18+
        if "Heightmaps" in chunk:
            del chunk["Heightmaps"]
        if "isLightOn" in chunk:
            del chunk["isLightOn"]
    return chunk


def optimise_region(region_x: str, region_z: str, directory: str, optimise_chunks: bool) -> anvil.EmptyRegion:
    """
    Used to filter out useless chunks from a region file, given it's X and Y position, and it's directory.

    Parameters
    ----------
    region_x : str
        The region's X position.
    regionY : str
        The region's Y position.
    directory : str
        The region file's directory.
    optimise_chunks : bool
        Also optimise singular chunks or not?

    Returns
    -------
    anvil.EmptyRegion
        The new, filtered region.
    None
        The function returns None if the filtered region is completely empty.

    Examples
    --------
    >>> optimise_region("-1","0","./world/region_coords_list/",True)
    libs.anvilparser.anvil.empty_region.EmptyRegion object

    See Also
    --------
    optimise_chunk: Optimize a singular chunk.
    """
    region = anvil.Region.from_file(directory+'r.'+region_x+"."+region_z+'.mca')
    new_region = anvil.EmptyRegion(region_x, region_z)
    is_empty = True
    for chunk_x in range(0, 32):
        for chunk_z in range(0, 32):
            chunk = region.chunk_data(chunk_x, chunk_z)

            if chunk:  # If a chunk exists at those chunk coordinates
                ver = get_chunk_version(chunk)  # Get it's version
                if ver == 0 and seventeen_checks(chunk):
                    if optimise_chunks:
                        # Optimise the chunk itself if asked
                        chunk = optimise_chunk(chunk, 0)
                    # Adds the chunk to the new optimized region
                    new_region.add_chunk(anvil.Chunk(chunk))
                    is_empty = False
                elif ver == 1 and eighteen_checks(chunk):
                    if optimise_chunks:
                        # Optimise the chunk itself if asked
                        chunk = optimise_chunk(chunk, 1)
                    # Adds the chunk to the new optimized region
                    new_region.add_chunk(anvil.Chunk(chunk))
                    is_empty = False
    if is_empty:
        return None
    return new_region


if __name__ == "__main__":
    import sys
    import os
    import re
    from multiprocessing.pool import ThreadPool as Pool
    import multiprocessing
    from nbt.nbt import MalformedFileError
    from zlib import error as ZlibError

    settings = {
        "no_keep": False,
        "input_dir": "./input/",
        "output_dir": "./output/",
        "optimise_chunks": False,
        "replace": False,
    }

    if "-nokeep" in sys.argv:
        settings["no_keep"] = True

    if "-optimisechunks" in sys.argv:
        settings["optimise_chunks"] = True

    if "-input" in sys.argv:
        settings["input_dir"] = sys.argv[sys.argv.index("-input")+1]

    if "-output" in sys.argv:
        settings["output_dir"] = sys.argv[sys.argv.index("-output")+1]

    if "-replace" in sys.argv:
        settings["no_keep"] = True
        settings["replace"] = True
        settings["output_dir"] = settings["input_dir"]

    # Ensure it's a directory
    if not settings["input_dir"].endswith("/") or not settings["input_dir"].endswith("\\"):
        settings["input_dir"] += "/"

    # Ensure it's a directory
    if not settings["output_dir"].endswith("/") or not settings["output_dir"].endswith("\\"):
        settings["output_dir"] += "/"

    # Ensure the directory exists
    if not os.path.exists(settings["output_dir"]):
        os.makedirs(settings["output_dir"])

    # Ensure the directory exists
    if not os.path.exists(settings["input_dir"]):
        os.makedirs(settings["input_dir"])

    def worker(region_coords: tuple) -> None:
        """Worker used for multiprocessing the I/O and optimising tasks"""
        worker_name = multiprocessing.Process().name
        filename = "r."+region_coords[0]+"."+region_coords[1]+".mca"
        print(f"{worker_name}: Starting work on {filename}!")
        try:
            region = optimise_region(region_coords[0], region_coords[1], settings["input_dir"], settings["optimise_chunks"])
            if region:
                print(f"{worker_name}: {filename} has been cleaned! Saving..")
                if settings["no_keep"]:
                    os.remove(settings["input_dir"]+filename)
                region.save(settings["output_dir"]+filename)
            else:
                print(f"{worker_name}: Removing file '{filename}' as it contains nothing but empty chunks.")
                if settings["replace"]:
                    os.remove(settings["input_dir"]+filename)
        except (IndexError, MalformedFileError, UnicodeDecodeError, ZlibError): # Errors that may occur if a file contains corrupted or unreadable data
            print(f"{worker_name}: Error while processing {filename}!")
            os.rename(inputDir + filename, outputDir + filename)

    with Pool(multiprocessing.cpu_count()) as pool:
        region_coords_list = []
        for item in os.scandir(settings["input_dir"]):
            # if it's a mca file...
            if item.path.endswith(".mca") and item.is_file():
                # Extract the region coordinates from the file name
                region_coords = re.findall(r'r\.(-?\d+)\.(-?\d+)\.mca', item.name)[0]
                if region_coords:
                    region_coords_list.append(region_coords)
        pool.map(worker, region_coords_list)

    print("Done!")
