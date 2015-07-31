#!/bin/bash

# so we know what home is
export HOME=$(pwd)
# ALRB
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh --quiet
# export proxy for pyami access
export X509_USER_PROXY=$HOME/$X509_USER_PROXY_FILENAME
# needed for script
localSetupFAX
localSetupPyAMI
localSetupROOT

echo $X509_USER_PROXY
# print directory listing for sanity
ls -lavh

printf "Start time: "; /bin/date
printf "Job is running on node: "; /bin/hostname
printf "Job running as user: "; /usr/bin/id
printf "Job is running in directory: "; /bin/pwd

python weights.py --inputDAODs ${2} -v --debug
