#!/bin/bash

if [[ $1 != 0 && $1 != 1 && $1 != 2 ]] 
then
    echo "No arguments supplied. Use the following options:"
    echo "Submit stage 1 jobs:   ./submit_grid.sh 0 Mu2e.in"
    echo "Submit PS jobs:        ./submit_grid.sh 1 Mu2e.in"
    echo "Submit Beam jobs:      ./submit_grid.sh 2 Mu2e.in"
    exit
fi

if [[ ! -f $2 ]] ; then
    echo 'File $2 is not there, aborting.'
    exit
fi

cp $2 Geometry
tar cf Geometry.tar Geometry
now=$(date +"%m_%d_%Y_%H_%M_%S")
tarbal=Geometry_${PWD##*/}_${now}_${1}.tar
mu2ein=Mu2E_${PWD##*/}_${now}_${1}.in
cp Geometry.tar ${tarbal}
cp $2 ${mu2ein}

run_offsite=0
opt_offsite=""
if [ ${run_offsite} == 1 ] 
then
    opt_offsite=" --prestage-spec=prestage.txt --OS=SL6 --resource-provides=usage_model=DEDICATED,OPPORTUNISTIC,OFFSITE --site=Caltech,FERMIGRID,FNAL,MIT,MWT2,Michigan,Nebraska,Omaha,SU-OG,Wisconsin,UCSD"
fi


if [ $1 == 0 ] 
then
    command="mu2eg4bl --in=${mu2ein} --tar=${tarbal} --njobs=200 --events-per-job=5000 --g4bl-version=v2_16 --g4bl-add-args='READ_Beam_File=$1' ${opt_offsite}"
else
    command="mu2eg4bl --in=${mu2ein} --tar=${tarbal} --njobs=250 --events-per-job=5000000 --g4bl-version=v2_16 --g4bl-add-args='READ_Beam_File=$1' ${opt_offsite}"
fi

echo "Executing:" $command
echo `$command`


