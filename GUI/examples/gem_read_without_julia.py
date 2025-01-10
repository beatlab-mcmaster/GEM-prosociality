import sys, os, re

# Deal with adding the requisite GEM GUI modules to the path
if not os.environ.get('GEMROOT', None):
    # Try to get the GEM path from this module's path.
    p = re.compile('.*/GEM-prosociality/')
    m = p.match(os.path.join(os.path.abspath(os.path.curdir), __file__))
    if m:
        os.environ['GEMROOT'] = m.group(0)

sys.path.append(os.path.join(os.environ['GEMROOT'],'GUI'))

# from GEMIO import GEMDataFile
from gem_control_file import GEMDataFileReader # using Petr's new class

ifile = "/Users/beatlab/Desktop/GEM-prosociality_data/demo_data/20250108/GEM_example-069852aa_069852aa_069852aa_069852aa.gdf"
ofile = "/Users/beatlab/Desktop/GEM-prosociality_data/demo_data/20250108/GEM_example-069852aa_069852aa_069852aa_069852aa.csv"

gdf = GEMDataFileReader(ifile)
gdf.read_file()
# gdf.to_csv(ofile)
