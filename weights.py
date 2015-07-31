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


if not sys.version_info[:2] == (2, 7):
  logger.error("You must use python 2.7.")
  sys.exit(0)

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

did_regex = re.compile('(\d{6,8})')
def get_did(filename):
  m = did_regex.search(filename)
  if m is None:
    raise ValueError("{0:s} is not a valid filename. Could not get did.".format(filename))
  return m.groups()[0]

generatorTag_regex = re.compile('\.?(e\d{4})_?')
def get_generator_tag(filename):
  m = generatorTag_regex.search(filename)
  if m is None:
    raise ValueError("{0:s} is not a valid filename. Could not get generator tag.".format(filename))
  return m.groups()[0]

def get_info(pattern, fields='files.cross_section,files.gen_filt_eff,nfiles'):
  global api
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

  return avgXSec, avgFiltEff

if __name__ == "__main__":
  class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
    pass

  __version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
  __short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

  parser = argparse.ArgumentParser(description='Author: Giordon Stark. v.{0}'.format(__version__),
                                   formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))

  parser.add_argument('-v','--verbose', dest='verbose', action='count', default=0, help='Enable verbose output of various levels. Use --debug to enable output for debugging.')
  parser.add_argument('--debug', dest='debug', action='store_true', help='Enable ROOT output and full-on debugging. Use this if you need to debug the application.')
  parser.add_argument('-b', '--batch', dest='batch_mode', action='store_true', help='Enable batch mode for ROOT.')

  parser.add_argument('--inputDAODs', required=True, type=str, metavar='filelist', help='a text file containing a list of DAODs used')

  # parse the arguments, throw errors if missing any
  args = parser.parse_args()

  try:
    # Set up ROOT
    import ROOT
  except ImportError:
    logger.exception("You must set up ROOT first with PyROOT bindings.")
    sys.exit(0)

  try:
    # get PyAMI
    import pyAMI.client
    import pyAMI.atlas.api as api
  except ImportError:
    logger.exception("You must set up PyAMI first. localSetupPyAMI will do the trick. Make sure you have a valid certificate (voms-proxy-init -voms atlas) or run `ami auth` to log in.")
    sys.exit(0)

  # INIT ATLAS API
  api.init()
  # INSTANTIATE THE PYAMI CLIENT FOR ATLAS
  client = pyAMI.client.Client('atlas')

  try:
    # start execution of actual program
    import timing

    # set verbosity for python printing
    if args.verbose < 5:
      logger.setLevel(25 - args.verbose*5)
    else:
      logger.setLevel(logging.NOTSET + 1)

    with tempfile.NamedTemporaryFile() as tmpFile:
      if not args.debug:
        ROOT.gSystem.RedirectOutput(tmpFile.name, "w")

      # if flag is shown, set batch_mode to true, else false
      ROOT.gROOT.SetBatch(args.batch_mode)

    wdict = {}

    samplePattern = re.compile(".*:(.*)\.(e\d{4})_.*")
    with open(args.inputDAODs, 'r') as f:
      for line in f:
        if line.startswith('#'): continue
        try:
          res = subprocess.check_output(['dq2-ls', line.rstrip()]).split()
        except subprocess.CalledProcessError:
          logger.exception("dq2 is probably not set up. We use it to find your files (using patterns) before using pyami")
          sys.exit(0)

        for sample in res:
          logger.info("Processing: {0:s}".format(sample))
          did = get_did(sample)
          gen_tag = get_generator_tag(sample)
          logger.info("\tDID: {0:s}\n\tGen: {1:s}".format(did, gen_tag))
          matches = samplePattern.search(sample)
          if matches is None:
            logger.error("\tCould not parse {0:s}. Skipping it.".format(sample))
            continue
          sample_name, generator_tag = matches.groups()
          evnt_file_name = '.'.join(sample_name.split('.')[:-2] + ['evgen', 'EVNT', generator_tag])
          logger.info("\tEVNT file: {0:s}".format(evnt_file_name))
          # search for EVNT file
          #pattern = 'mc15_13TeV.410008.aMcAtNloHerwigppEvtGen_ttbar_allhad.evgen.EVNT.e3964'
          avgXSec, avgFiltEff = get_info(evnt_file_name)
          logger.info("\tavg. xsec = {0:0.6f} pb\n\tavg. filter eff = {1:0.6f}".format((avgXSec*1000), avgFiltEff))

    if not args.debug:
      ROOT.gROOT.ProcessLine("gSystem->RedirectOutput(0);")

  except Exception, e:
    # stop redirecting if we crash as well
    if not args.debug:
      ROOT.gROOT.ProcessLine("gSystem->RedirectOutput(0);")

    logger.exception("{0}\nAn exception was caught!".format("-"*20))

