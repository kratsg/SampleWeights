import csv
import yaml

cutflows={}
with open("nevents.list") as f:
  reader = csv.reader(f, delimiter=":")
  c = list(reader)
f.close()

for cc in c:
  cutflows[cc[0]] = cc[1]

def write_new_weights(sample):
  filename = sample + '.json'
  weights = yaml.load(file(filename))
  for k in weights.keys():
    tag = weights[k].keys()[0]
    try:
      weights[k][tag]['num events'] = cutflows[k]
    except:
      weights[k][tag]['num events'] = 0

  with open(sample+'.yml','w+') as outfile:
    outfile.write(yaml.dump(weights,default_flow_style=False))
  outfile.close()

write_new_weights('ttbar')
