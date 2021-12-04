# Use case
This script is a script that locates and deletes unloaded and unused chunks inside of region files. This saves significants amounts of space. (In my own testing, it went down by five or seven folds.)

# Usage
Put all of your .mca region files into the `input` folder and then run the script. Once it finished, you can replace your old region files with the one inside of the `output` folder.

# Arguments
* `-nokeep` Delete the files as they are done being treated (Default: False)
* `-input "directory"` Select your input folder (Default: ./input/)
* `-output "directory"` Select your output folds (Default: ./output/)