universe = grid
GridResource = gt2 fnpcosg1.fnal.gov/jobmanager-condor
executable = g4bl_grid.sh 
arguments = $(Cluster) $(Process) $ENV(USER) $ENV(PWD) g4bl_grid.tar
output = grid_job.$(Cluster).$(Process).out
error = grid_job.$(Cluster).$(Process).err
log = grid_job.$(Cluster).$(Process).log
transfer_input_files = g4bl_grid.tar
when_to_transfer_output = ON_EXIT
notification = NEVER
queue 10
