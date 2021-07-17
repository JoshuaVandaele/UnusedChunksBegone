# For this script to work, you need
# to edit line 49 of libs\anvilparser\anvil\empty_region.py
# to return True because one of the checks is messed up
# https://github.com/matcool/anvil-parser/issues/27

import libs.anvilparser.anvil as anvil
import os
import re

inputDir = "./input/"
outputDir = "./output/"

def removeEmptyChunks(regionX,regionZ):
	region = anvil.Region.from_file(inputDir+'r.'+str(regionX)+"."+str(regionZ)+'.mca')
	newRegion = anvil.EmptyRegion(regionX,regionZ)
	isEmpty = True
	for chunkX in range(0,32):
		for chunkZ in range(0,32):
			chunk = region.chunk_data(chunkX,chunkZ)
			if (
			chunk and 										# Chunk exists
			"Biomes" in chunk["Level"] and 					# Chunk has been loaded
			chunk["Level"]["InhabitedTime"].value > 0 and 	# Chunk has been visisted
			len(chunk["Level"]["Sections"]) > 0 			# Chunk contains blocks (including air)
			):
				newRegion.add_chunk(anvil.Chunk.from_region(region,chunkX,chunkZ))
				isEmpty = False
	if isEmpty:
		return None
	else:
		return newRegion

if __name__ == "__main__":
	for item in os.scandir(inputDir):
		if item.path.endswith(".mca") and item.is_file(): # if it's a mca file...
			regionCoords = re.findall('r\.(-?\d+)\.(-?\d+)\.mca',item.name)[0] # Extract the region coordinates from the file name
			if regionCoords:
				region = removeEmptyChunks(regionCoords[0],regionCoords[1])
				if region:
					print(item.name+" has been cleaned! Saving..")
					region.save(outputDir+item.name)
				else:
					print("Removing file '"+item.name+"' as it contains nothing but empty chunks.")