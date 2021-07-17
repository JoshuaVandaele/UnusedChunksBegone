Due to https://github.com/matcool/anvil-parser/issues/27, you will need to edit the file located at `%localappdata%\Programs\Python\Python39\lib\site-packages\anvil\empty_region.py` on Windows. Edit line 49 of `empty_region.py` to just be `return True`.

# Use case
This script is a script that locates and deletes unloaded and unused chunks inside of region files. This saves significants amounts of space. (In my own testing, it went down by five or seven folds.)

# Usage
Put all of your .mca region files into the `input` folder and then run the script. Once it finished, you can replace your old region files with the one inside of the `output` folder.