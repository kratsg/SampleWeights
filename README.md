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
python --inputDAODs data.list
python --inputDAODs dijets.list
python --inputDAODs gbb.list
python --inputDAODs gtt.list
python --inputDAODs singletop.list
python --inputDAODs topew.list
python --inputDAODs ttbar.list
python --inputDAODs weights.py
python --inputDAODs wjets.list
python --inputDAODs zjets.list
```
