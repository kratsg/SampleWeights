# OUTDATED

This is slowly being deprecated. https://github.com/kratsg/TheAccountant/#getweightspy contains current instructions for generating an appropriate `weights.json` file now.

# Instructions

To set up,

```
localSetupFAX
localSetupPyAMI
localSetupROOT
voms-proxy-init -voms atlas
python weights.py
```

We need:

- FAX: use `dq2-ls` to expand out all samples for a given pattern and loop over to get their provenance
- PyAMI: given a provenance dataset, get the filter efficiency and cross section
- PyROOT: open up the mini-xAODs via `TFile::Open()` and `xrd` to get the cut flow histograms for number events.

To run,

```
python weights.py --inputDAODs dijets.list
python weights.py --inputDAODs gbb.list
python weights.py --inputDAODs gtt.list
python weights.py --inputDAODs singletop.list
python weights.py --inputDAODs topew.list
python weights.py --inputDAODs ttbar.list
python weights.py --inputDAODs wjets.list
python weights.py --inputDAODs zjets.list
```

To use condor, edit the `condor_config` file to make sure the right X509 proxy is being used (set up your proxy via `voms-proxy-init -voms atlas` if you haven't). The rest should take care of itself since we create a job for each of the lists above.
