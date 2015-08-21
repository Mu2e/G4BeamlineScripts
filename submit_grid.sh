#!/bin/bash


if [ $# -eq 0 ]
  then
    echo "No arguments supplied. Use the following options:"
    echo "Submit stage 1 jobs:   ./submit_grid.sh 0"
    echo "Submit PS jobs:        ./submit_grid.sh 1"
    echo "Submit Beam jobs:      ./submit_grid.sh 2"
fi

cp Mu2E.in Geometry
tar cf Geometry.tar Geometry
command="./mu2egrid/v2_00_27/bin/mu2eg4bl --in=Mu2E.in --tar=Geometry.tar --njobs=2 --events-per-job=25 --g4bl-version=v2_16 --g4bl-add-args='READ_Beam_File=$1'"
echo "Executing:" $command
#echo `$command`
now=$(date +"%m_%d_%Y")
cp Geometry.tar Geometry_${PWD##*/}_${now}_${1}.tar
