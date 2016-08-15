
# Instructions

Clone me.

```
git clone https://github.com/kratsg/SampleWeights
```

Enter me.

```
cd SampleWeights
```

Environmentalize me.

```
lsetup rucio fax dq2 pyami
voms-proxy-init -voms atlas
rcSetup Base,2.X.Y
```

Understand me.

```
python weights.py -h
```

Use me.

```
python weights.py inputSamples/dijets.list --inputGrid --inputList --config counter_MBJ.py
```

## Counter Config File

A counter config file is how you tell the script how to compute the number of events for a file in your datasets. In the example for MultiBJets, we produce a cutflow histogram in every output that contains the number of events for the file. So our [counter_MBJ.py](counter_MBJ.py) looks like:

```
def counter(f):
  cutflow = f.Get("cut_flow")
  return cutflow.GetBinContent(2)
```

You specify a `counter` function which:

- takes in one argument - an opened ROOT file for reading
- returns one number - the number of events in that file

# Requirements

We need:

- RootCore: for SampleHandler functionality
  - rucio: used by SampleHandler to scan the grid to get datasets for a given pattern
  - fax: used by SampleHandler to get the files for a dataset that we can open over xrdcp
- PyAMI: given an input dataset, we'll look up the evgen.EVNT file and get the sample's metadata (cross-section, filter efficiency, and k-factor)
  - Note: relative uncertainty (cross-section uncertainty) is not stored in PyAMI or any database for that matter so you will need to add this if you want it
- PyROOT: open up the mini-xAODs via `TFile::Open()` and `xrd` to get the cut flow histograms for number events.


# Condor

CURRENTLY BROKEN. FIXIT GIORDON.
