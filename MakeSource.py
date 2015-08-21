#!/bin/python 3
# source  /grid/fermiapp/products/mu2e/setupmu2e-art.sh
# setup root v5_34_05 -qmu2e:e2:prof
# Run as: python MakeSource.py Source.root 0/1
# 0 - PS Only. Neutrons only
# 1 - Beam source. All particles, excluding neutrons, soft gammas and electrons

from ROOT import TFile, TTree
from ROOT import gROOT
from math import sqrt
from math import fabs
import sys

gROOT.Reset()

file_name = sys.argv[1]
source = sys.argv[2]

if int(source) == 0:
    file_out = file_name[0:len(file_name)-5]+"_ps.txt"
elif int(source) == 1:
    file_out = file_name[0:len(file_name)-5]+"_bm.txt" 
else:
    print 'Uknown argument. Run as: python MakeSource.py Source.root [0/1]'
    sys.exit(0)

f = file(file_out, 'w')
_file = TFile(file_name)
#_tree = _file.Get("/NTuple/Z3712")
_tree = _file.Get("/NTuple/Z3883")
oldID = -999
oldEV = -999

print '-----Start producing the output-----'
print 'The intput source file:'+file_name
print 'The output source file:'+file_out

f.write('#BLTrackFile: Source file\n')
f.write('#{:<12} {:<12} {:<12} {:<10} {:<10} {:<10} {:<12} {:<7} {:<10} {:<10} {:<9} {:<7}\n'.format("x", "y", "z", "Px", "Py", "Pz", "t", "PDGid", "EventID", "TrackID", "ParentID", "PDGid"))
f.write('#{:<12} {:<12} {:<12} {:<10} {:<10} {:<10} {:<12} {:<7} {:<10} {:<10} {:<9} {:<7}\n'.format("mm", "mm", "mm", "MeV/c", "MeV/c", "MeV/c", "ns", "ID", "ID", "ID", "ID", "ID"))

for i in _tree:

    if int(i.EventID)%50000 == 0:
        print 'Processing event: ', int(i.EventID)

    # Skip track if appears twice
    if oldID == int(i.TrackID) and oldEV == int(i.EventID):
        continue

    # Remove exotic particles. g4bl can't handle them as the source
    if int(i.PDGid)>1000000:
        continue

    # Select only neutrons in PS source
    if int(i.PDGid) != 2112 and int(source) == 0:
        continue

    # Drop neutrons in beam source
    if int(i.PDGid) == 2112 and int(source) == 1:
        continue

    # Drop visible and soft gammas in beam source
    if int(i.PDGid) == 22 and sqrt(i.Px*i.Px+i.Py*i.Py+i.Pz*i.Pz)<1.0 and int(source) == 1:
        continue

   # Drop soft electrons in beam source
    if fabs(int(i.PDGid)) == 11 and sqrt(i.Px*i.Px+i.Py*i.Py+i.Pz*i.Pz)<1.0 and int(source) == 1:
        continue

    # Select upstream particles. TrackID is forced to be "1" to avoid g4bl warning about large TrackID 
    if i.Pz < 0:
        continue
    else:
        f.write('{:<13.3f} {:<12.3f} {:<12.3f} {:<10.3f} {:<10.3f} {:<10.3f} {:<12.3f} {:<7} {:<10} {:<10} {:<7} {:<7}\n'.format(i.x, i.y, i.z, i.Px, i.Py, i.Pz, i.t, int(i.PDGid), int(i.EventID), 1, int(i.ParentID), int(i.PDGid)))
        oldID = int(i.TrackID)
        oldEV = int(i.EventID)


_file.Close()
f.close()


if __name__ == '__main__':
    a = 0
