#!/bin/bash
#
# A script to run Mu2e G4BeamLine jobs on the GRID.
#
# It takes 5 arguments:
#   cluster    - the condor job cluster number
#   process    - the condor job process number, within the cluster
#   user       - the username of the person who submitted the job
#   submitdir  - the directory from which the job was submitted ( not used at this time).
#   g4bltar    - the name of the archive file that has g4beamline Input file and Geometry files
#
# Outputs:
#  - The text output from each job is put into the condor .out, .log and .err files
#  - The g4beamline.root file is put into:
#      /grid/data/mu2e/outstage/$user/g4beamline_${cluster}_$process.root
#
# Notes:
#
# 1) You have to run Mu2e setup on each worker node and setup G4BeamLine.
# 2) Each job does 100000 events and the first event number is (100000*process + 1)
# 3) The output files are presumed to be a large file and are copied to
#    the outstage area using the cpn program.  For discussions of cpn and outstage see:
#      http://mu2e.fnal.gov/atwork/computing/fermigrid.shtml#cpn
#      http://mu2e.fnal.gov/atwork/computing/fermigrid.shtml#outstage
#

# Copy arguments into meaningful names.
cluster=$1
process=$2
user=$3
submitdir=$4
g4bltar=$5
echo "Input arguments:"
echo "Cluster:    " $cluster
echo "Process:    " $process
echo "User:       " $user
echo "SubmitDir:  " $submitdir
echo "g4bl tar:   " $g4bltar
echo " "

# Do not change this section.
# It creates a temporary working directory that automatically cleans up all
# leftover files at the end.
ORIGDIR=`pwd`
TMP=`mktemp -d ${OSG_WN_TMP:-/var/tmp}/working_dir.XXXXXXXXXX`
TMP=${TMP:-${OSG_WN_TMP:-/var/tmp}/working_dir.$$}

{ [[ -n "$TMP" ]] && mkdir -p "$TMP"; } || \
  { echo "ERROR: unable to create temporary directory!" 1>&2; exit 1; }
trap "[[ -n \"$TMP\" ]] && { cd ; rm -rf \"$TMP\"; }" 0
cd $TMP
mv $ORIGDIR/* .
# End of the section you should not change.

# Directory in which to put the output file.
outstage=/grid/data/mu2e/outstage/$user

# Compute range of event numbers for this job.
First_Event=$(( $process*100000 + 1))
Num_Events=100000 
#echo "First event number will be: " $First_Event
#echo "Number of events will be:   " $Num_Events
echo " " 

# untar Geometry and Input files to worker node
tar -xf $g4bltar

# Run Mu2e setup and setup G4BeamLine (You can change version of G4BeamLine)
source /grid/fermiapp/products/mu2e/setupmu2e-art.sh
setup G4beamline v2_08

# Run G4BeamLine 
g4bl Mu2E.in First_Event=$First_Event Num_Events=$Num_Events

# Make sure the user's output staging area exists.
test -e $outstage || mkdir $outstage
if [ ! -d $outstage ];then
   echo "File exists but is not a directory."
   outstage=/grid/data/mu2e/outstage/nobody
   echo "Changing outstage directory to: " $outstage 
   exit
fi

# Copy the output file to the output staging area.
# Here the {} are important.
outstagecluster=${outstage}/${cluster}
test -e $outstagecluster || mkdir $outstagecluster

# Making copy of output files(add more lines and change filenames if you have different output files)
echo "making copy of output files"
/grid/fermiapp/minos/scripts/cpn g4beamline.root ${outstagecluster}/g4beamline_$process.root
if [ $process -eq 0 ]; then
    echo "Making copy of input archive"
    /grid/fermiapp/minos/scripts/cpn $g4bltar ${outstagecluster}/g4bl_grid.tar
fi
exit 0
