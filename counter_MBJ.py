def counter(f):
  cutflow = f.Get("cut_flow")
  return cutflow.GetBinContent(2)
