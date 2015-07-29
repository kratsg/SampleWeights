import csv
with open("dids.txt") as input_file:
  reader = csv.reader(input_file, delimiter=" ")
  lines = list(reader)
input_file.close()
dids = [line[0] for line in lines]

import glob
import ROOT as r

for did in dids:
  data_file = '/atlas/local/acukierm/*'+did+'*/*.root'
  filelist = glob.glob(data_file)

  sumw = 0
  for filename in filelist:
    f = r.TFile(filename)
    histo = f.Get("cut_flow")
    sumw += histo.GetBinContent(2)

  print sumw
