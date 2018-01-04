import json
from datetime import datetime
from tqdm import tqdm
import numpy as np

from countries import countries
cc = countries.CountryChecker('./countries/TM_WORLD_BORDERS-0.3.shp')

#TODO: provide some command line options to make editing easier
startdate = datetime.strptime('2013 Mar 14', '%Y %b %d');


def setDate(loc):
	ts_ms = int(loc['timestampMs']) / 1000
	loc['date'] = datetime.fromtimestamp(ts_ms)

def setCountry(loc):
	lat = loc['latitudeE7']/1e7
	lon = loc['longitudeE7']/1e7
	country = cc.getCountry(lat, lon)
	if country:
		loc['country'] = country.name
	else:
		loc['country'] = '?'


print "Reading Data"
with open('LocationHistory.json') as fp:
	data = json.load(fp)
	locHist = data['locations']

print "Pruning Data"
dayHist = []
prevDate = datetime.now()
for idx, loc in tqdm(enumerate(locHist)):
	setDate(loc)
	if loc['date'] < startdate:
		break

	dt = prevDate - loc['date']
	if(dt.days >= 1):
		dayHist.append(loc)
		prevDate = loc['date']



print "Finding out countries"
for loc in tqdm(dayHist):
	setCountry(loc)

print "Compressing"
dates     = np.array([x['date'] for x in reversed(dayHist)])
countries = np.array([x['country'] for x in reversed(dayHist)])

idx = np.where(countries[:-1] != countries[1:])[0]
D = dates[idx]
C = countries[idx]

outFile = open('locHist.csv','w')
totalDays = 0
totalNZDays = 0
p = startdate
for i in range(len(D)):
	c = C[i]
	d = D[i]
	dt = (d - p);
	outStr = "{cnt}, {st}, {en}, {d}".format(cnt=c, st=p.strftime('%m/%d/%y'), en=d.strftime('%m/%d/%y'), d=dt.days)
	p = d

	print outStr
	outFile.write(outStr+"\n")

	if not c in ['United States', 'Puerto Rico']:
		totalDays += dt.days + 1

	if c in ['New Zealand']:
		totalNZDays += dt.days + 1

	break
	
outFile.close()

print 'Total days outside of US', totalDays
print 'Total days in NZ', totalNZDays