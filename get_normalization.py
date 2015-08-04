'''import csv
with open("dids.txt") as input_file:
  reader = csv.reader(input_file, delimiter=" ")
  lines = list(reader)
input_file.close()
dids = [line[0] for line in lines]'''
dids = ['410000']

import glob
import ROOT as r

for did in dids:
  data_file = '/atlas/local/acukierm/user.amarzin.'+did+'.ttbar.DAOD_SUSY10.e3698_s2608_s2183_r6630_r6264_p2375_tag_05_output_xAOD.root.364*/*.root'
  filelist = glob.glob(data_file)

  sumw = 0
  for filename in filelist:
    print filename
    f = r.TFile(filename)
    histo = f.Get("cut_flow")
    print histo.GetBinContent(2)
    sumw += histo.GetBinContent(2)

  print str(did)+"\t"+str(sumw)
