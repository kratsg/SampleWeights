#!/usr/bin/env python

# @file:    GetWeights.py
# @purpose: For a given list of samples, produce a working weights.json file
# @author:  Giordon Stark <gstark@cern.ch>
# @date:    August 2015
#
# @example:
# @code
# GetWeights.py --help
# @endcode
#

from __future__ import print_function
import logging

root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler())
getWeights_logger = logging.getLogger("getWeights")

import argparse
import os
import subprocess
import sys
import datetime
import time
import re
import json
from operator import itemgetter
import time
import itertools
from multiprocessing import Pool

SCRIPT_START_TIME = datetime.datetime.now()

# think about using argcomplete
# https://argcomplete.readthedocs.org/en/latest/#activating-global-completion%20argcomplete

if __name__ == "__main__":

  # catch CTRL+C
  import signal
  def signal_handler(signal, frame):
    print("Exiting the program now. Have a nice day!{0:s}".format(" "*40))  # extra spaces just in case
    sys.exit(0)
  signal.signal(signal.SIGINT, signal_handler)

  did_regex = re.compile('\.?(?:00)?(\d{6,8})\.?')
  def get_did(filename):
    global did_regex
    m = did_regex.search(filename)
    if m is None: raise ValueError('Can\'t figure out the DID! Filename: {0:s}'.format(filename))
    return m.group(1)

  generatorTag_regex = re.compile('\.?(e\d{4})_?')
  def get_generator_tag(filename):
    m = generatorTag_regex.search(filename)
    if m is None:
      raise ValueError("{0:s} is not a valid filename. Could not get generator tag.".format(filename))
    return m.groups()[0]

  def get_info(filename):
    global client
    # get the responses
    response = client.execute(['GetPhysicsParamsForDataset',"--logicalDatasetName=%s"%filename], format='dict_object')
    # format this into dictionaries
    response = sorted(response.get_rows(), key=lambda item: time.mktime(time.strptime(item['insert_time'], '%Y-%m-%d %H:%M:%S')))
    results = {}

    for physics_param, items in itertools.groupby(response, key=itemgetter('paramName')):
      for item in items:
        results[physics_param] = item['paramValue']
        # only want the first item
        break

    getWeights_logger.info(results)
    results['cross section'] = float(results.pop('crossSection', 0.0))
    results['filter efficiency'] = float(results.pop('genFiltEff', 0.0))
    results['k-factor'] = float(results.pop('kFactor', 0.0))

    return results

  # pass in the filename, get a cutflow number
  def get_cutflow(fname, numErrors=0):
    global args
    if numErrors > 3:
      return fname
    try:
      configLocals  = {}
      execfile(args.config, {}, configLocals)
      f = ROOT.TFile.Open(fname, "READ")
      count = configLocals['counter'](f)
      f.Close()
      return count
    except:
      getWeights_logger.exception("{0}\nAn exception was caught for {1:s}!".format("-"*20, fname))
      return get_cutflow(fname, numErrors+1)

  # if we want multiple custom formatters, use inheriting
  class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter):
    pass

  __version__ = subprocess.check_output(["git", "describe", "--always"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()
  __short_hash__ = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.realpath(__file__))).strip()

  parser = argparse.ArgumentParser(add_help=True, description='Make a proper weights file using cutflow information and susytools metadata.',
                                   usage='%(prog)s --files ... file [file ...] [options] {driver} [driver options]',
                                   formatter_class=lambda prog: CustomFormatter(prog, max_help_position=30))

  # http://stackoverflow.com/a/16981688
  parser._positionals.title = "required"
  parser._optionals.title = "optional"

  # positional argument, require the first argument to be the input filename
  parser.add_argument('files', type=str, nargs='+', help='input file(s) to read')
  parser.add_argument('--config', metavar='', type=str, required=True, help='configuration for the cutflow computation. See counter_MBJ.py for example')

  parser.add_argument('-o', '--output', dest='output_filename', metavar='file', type=str, help='Output filename', default='weights.json')
  parser.add_argument('-f', '--force', dest='force_overwrite', action='store_true', help='Overwrite previous output if it exists.')
  parser.add_argument('--version', action='version', version='%(prog)s {version}'.format(version=__version__))

  parser.add_argument('--inputList', dest='use_inputFileList', action='store_true', help='If enabled, will read in a text file containing a list of files.')
  parser.add_argument('--inputGrid', dest='use_addGrid', action='store_true', help='If enabled, will search using DQ2. Can be combined with `--inputList`.')
  parser.add_argument('--flat-layout', action='store_true', help='Enable if you have a flatter sample layout, where the sample is a file and not a directorty.')
  parser.add_argument('-v', '--verbose', dest='verbose', action='count', default=0, help='Enable verbose output of various levels. Default: no verbosity')
  parser.add_argument('-y', '--yes', dest='skip_confirm', action='count', default=0, help='Skip the configuration confirmations. Useful for when running in the background.')

  parser.add_argument('--debug', dest='debug', action='store_true', help='Enable verbose output of the algorithms.')

  # parse the arguments, throw errors if missing any
  args = parser.parse_args()

  # set verbosity for python printing
  if args.verbose < 4:
    getWeights_logger.setLevel(20 - args.verbose*5)
  else:
    getWeights_logger.setLevel(logging.NOTSET + 1)

  try:
    # get PyAMI
    import pyAMI.client
    import pyAMI.atlas.api as api
  except ImportError:
    getWeights_logger.exception("You must set up PyAMI first. lsetup pyami will do the trick. Make sure you have a valid certificate (voms-proxy-init -voms atlas) or run `ami auth` to log in.")
    sys.exit(0)

  # INIT ATLAS API
  api.init()
  # INSTANTIATE THE PYAMI CLIENT FOR ATLAS
  client = pyAMI.client.Client('atlas')


  try:
    import timing

    # check submission directory
    if args.force_overwrite:
      getWeights_logger.info("removing {0:s}".format(args.output_filename))
      try:
        os.remove(args.output_filename)
      except OSError:
        pass
    else:
      # check if directory exists
      if os.path.exists(args.output_filename):
        raise OSError('Output file {0:s} already exists. Either re-run with -f/--force, choose a different --output, or rm it yourself. Just deal with it, dang it.'.format(args.output_filename))

    # they will need it to get it working
    if args.use_addGrid:
      if os.getenv('XRDSYS') is None:
        raise EnvironmentError('xrootd client is not setup. Run localSetupFAX or equivalent.')

    # at this point, we should import ROOT and do stuff
    import ROOT
    getWeights_logger.info("loading packages")
    ROOT.gROOT.Macro("$ROOTCOREDIR/scripts/load_packages.C")

    #Set up the job for xAOD access:
    ROOT.xAOD.Init("GetWeights").ignore();

    # create a new sample handler to describe the data files we use
    getWeights_logger.info("creating new sample handler")
    sh_all = ROOT.SH.SampleHandler()

    # this portion is just to output for verbosity
    if args.use_inputFileList:
      getWeights_logger.info("\t\tReading in file(s) containing list of files")
      if args.use_addGrid:
        getWeights_logger.info("\t\tAdding samples using addGrid")
      else:
        getWeights_logger.info("\t\tAdding using readFileList")
    else:
      if args.use_addGrid:
        getWeights_logger.info("\t\tAdding samples using addGrid")
      else:
        getWeights_logger.info("\t\tAdding samples using scanDir")

    for fname in args.files:
      if args.use_inputFileList:
        if args.use_addGrid:
          with open(fname, 'r') as f:
            for line in f:
              if line.startswith('#') : continue
              if not line.strip()     : continue
              ROOT.SH.scanRucio(sh_all, line.rstrip())
        else:
          ROOT.SH.readFileList(sh_all, os.path.basename(fname).replace('.list',''), fname)
      else:
        if args.use_addGrid:
          ROOT.SH.scanRucio(sh_all, fname)
        else:
          fname = fname.replace('"','')
          # need to parse and split it up
          fname_base = os.path.basename(fname)
          sample_dir = os.path.dirname(os.path.abspath(fname))
          mother_dir = os.path.dirname(sample_dir)
          sh_list = ROOT.SH.DiskListLocal(mother_dir)
          ROOT.SH.scanDir(sh_all, sh_list, fname_base, os.path.basename(sample_dir))

    # print out the samples we found
    getWeights_logger.info("\t%d different dataset(s) found", len(sh_all))
    if not args.use_addGrid:
      for dataset in sh_all:
        getWeights_logger.info("\t\t%d files in %s", dataset.numFiles(), dataset.name())
    sh_all.printContent()

    if len(sh_all) == 0:
      getWeights_logger.info("No datasets found. Exiting.")
      sys.exit(0)

    # set the name of the tree in our files (should be configurable)
    sh_all.setMetaString("nc_tree", "CollectionTree")

    # get cutflow number
    # if there is any sort of error with the file, retry up to 3 times
    #   before just completely erroring out
    samplePattern = re.compile(".*:(.*)\.(e\d{4})_.*")
    def get_sample_info(fargs):
      global samplePattern
      sample, flat_layout = fargs
      weight = {'num events': 0.0,
                'errors': [],
                'cross section': -1.0,
                'filter efficiency': -1.0,
                'k-factor': -1.0,
                'rel uncert': -1.0}

      if flat_layout:
        sampleName = os.path.basename(sample.fileName(0))
      else:
        sampleName = sample.name()

      getWeights_logger.info("Processing: {0:s}".format(sampleName))
      did = get_did(sampleName)
      gen_tag = get_generator_tag(sampleName)
      getWeights_logger.info("\tDID: {0:s}\n\tGen: {1:s}".format(did, gen_tag))
      # find the corresponding EVNT sample name
      res = api.list_datasets(client,  patterns='{0:s}.{1:s}.%.evgen.EVNT.{2:s}'.format('mc15_13TeV',did, gen_tag))
      if len(res) != 1: return (did, weight)
      evnt_file_name = res[0]['ldn']
      getWeights_logger.info("\tEVNT file: {0:s}".format(evnt_file_name))

      try:
        for fname in sample.makeFileList():
          count = get_cutflow(fname)
          # we return the filename if we can't open it for reading
          try:
            weight['num events'] += float(count)
          except (ValueError, TypeError) as e:
            weight['errors'].append(count)
        weight.update(get_info(evnt_file_name))
        return (did, weight)
      except Exception, e:
        # we crashed
        getWeights_logger.exception("{0}\nAn exception was caught!".format("-"*20))
        return (did, weight)

    # dictionary to hold results of all calculations
    weights = {}
    # a process for each sample
    num_procs = 8
    pool = Pool(num_procs)

    getWeights_logger.info("spinning up {0:d} processes".format(num_procs))

    for res in pool.imap_unordered(get_sample_info, zip(sh_all, [args.flat_layout]*len(sh_all))):
      weights.update(dict((res,)))

      with open(args.output_filename, 'w+') as f:
        f.write(json.dumps(weights, sort_keys=True, indent=4))

    SCRIPT_END_TIME = datetime.datetime.now()

    with open(args.output_filename, 'w+') as f:
      f.write(json.dumps(weights, sort_keys=True, indent=4))

  except Exception, e:
    # we crashed
    getWeights_logger.exception("{0}\nAn exception was caught!".format("-"*20))
