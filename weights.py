#!/usr/bin/env python

# @file:    weights.py
# @purpose: generate the appropriate weights.yml file
# @author:  Giordon Stark <gstark@cern.ch>
# @date:    July 2015
#

# __future__ imports must occur at beginning of file
# redirect python output using the newer print function with file description
#   print(string, f=fd)
from __future__ import print_function
# used to redirect ROOT output
#   see http://stackoverflow.com/questions/21541238/get-ipython-doesnt-work-in-a-startup-script-for-ipython-ipython-notebook
import tempfile

import os, sys
# grab the stdout and have python write to this instead
# ROOT will write to the original stdout
STDOUT = os.fdopen(os.dup(sys.stdout.fileno()), 'w')

# for logging, set it up
import logging
root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler(STDOUT))
logger = logging.getLogger("weights")
logger.setLevel(20)

# import all libraries
import argparse
import subprocess
import json
import hashlib
import copy
import operator
import re
import fnmatch
import math

try:
  # Set up ROOT
  import ROOT
except ImportError:
  logger.exception("You must set up ROOT first with PyROOT bindings.")

try:
  # get PyAMI
  import pyAMI.client
  import pyAMI.atlas.api as api
except ImportError:
  logger.exception("You must set up PyAMI first. localSetupPyAMI will do the trick. Make sure you have a valid certificate (voms-proxy-init -voms atlas) or run `ami auth` to log in.")

# INIT ATLAS API
api.init()

# INSTANTIATE THE PYAMI CLIENT FOR ATLAS
client = pyAMI.client.Client('atlas')

# search for EVNT file
pattern = 'mc15_13TeV.410008.aMcAtNloHerwigppEvtGen_ttbar_allhad.evgen.EVNT.e3964'
fields = 'files.cross_section,files.gen_filt_eff,nfiles'
resDict = api.list_datasets(client, patterns = pattern, fields = fields)

# loop over files in dataset, calculate avg filter efficiency
numFiles = 0
avgFiltEff = 0.0
avgXSec = 0.0
for results in resDict:
    numFiles = (float)(results['nfiles'])
    if (results['files_gen_filt_eff'] != 'NULL'): avgFiltEff += (float) (results['files_gen_filt_eff'])
    if (results['files_cross_section'] != 'NULL'): avgXSec += (float) (results['files_cross_section'])
    pass # end loop over files

if(numFiles != 0):
    avgFiltEff = avgFiltEff/numFiles
    avgXSec = avgXSec/numFiles

logger.info("{0:s} : avg. xsec = {1:0.2f} pb,  avg. filter eff = {2:0.2f}".format(pattern, (avgXSec*1000), avgFiltEff))
