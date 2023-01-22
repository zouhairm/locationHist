#!/usr/bin/env python3

from collections import OrderedDict
from datetime import datetime, timedelta
from tqdm import tqdm
import argparse
import json
import logging
import numpy as np
import sys

from countries import countries

logging.basicConfig(format='%(levelname)s: %(message)s',level=logging.INFO)
log = logging.getLogger('LocHist')


# Progress bar
tqdm.monitor_interval = 0 # per https://github.com/tqdm/tqdm/issues/481


parser = argparse.ArgumentParser(
    description="location miner",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("locfile", default='LocationHistory.json', help="path to location file")
parser.add_argument("-s", dest="startdate",
                     help="Date to start analyzing in Format YYYY-Mo-DD \n Example: 2013-Jan-30")
parser.add_argument("-r", "--resolution", default=6,
                     help="Resolution of location data in hours (Default is 6hrs)")

args = parser.parse_args()

if args.startdate == None:
    log.error('Must provide a start date')
    parser.print_help()
    sys.exit(-1)


try:
    startdate = datetime.fromisoformat(datetime.strptime(args.startdate, '%Y-%b-%d').isoformat() + '+00:00')
except Exception as e:
    log.error('Error parsing start date')
    sys.exit(-1)


def setDate(loc):
    timestamp = loc['timestamp'][:-1] + '+00:00'
    loc['date'] = datetime.fromisoformat(timestamp)


cc = countries.CountryChecker('./countries/TM_WORLD_BORDERS-0.3.shp')
def setCountry(loc):
    lat = loc['latitudeE7']/1e7
    lon = loc['longitudeE7']/1e7
    country = cc.getCountry(lat, lon)
    if country:
        loc['country'] = country.name
    else:
        loc['country'] = '?'


log.info("Loading location history data")
with open(args.locfile) as fp:
    data = json.load(fp)
    locHist = data['locations']

log.info("Pruning Data")
dayHist = []
prevDate = None
for loc in tqdm(locHist):
    setDate(loc)

    if loc['date'] < startdate:
        continue

    if prevDate is None:
        prevDate = loc['date']

    dt = loc['date'] - prevDate
    #Keep locations in n Hours increments
    if(dt.seconds/3600 >= args.resolution):
        dayHist.append(loc)
        prevDate = loc['date']



log.info("Looking up countries")
for loc in tqdm(dayHist):
    setCountry(loc)

log.info("Compressing")
dates     = np.array([x['date'] for x in (dayHist)])
countries = np.array([x['country'] for x in (dayHist)])

#If currently on trip, ask when expected to return to US
if countries[-1] != 'United States':
    countries = np.append(countries, 'United States')
    returndate = input('Enter date you expect to return to the US: (YYYY-MON DD), for example 2018-Jan-10: \n')
    try:
        returndate = datetime.fromisoformat(datetime.strptime(
            returndate, '%Y-%b-%d').isoformat() + '+00:00')
    except:
        log.warning('Error interpreting date %s. Using today instead'%returndate)
        returndate = datetime.fromisoformat(datetime.today().isoformat() + '+00:00')

    dates = np.append(dates, returndate)
    #Need to pad array due to way indexing is done
    dates     = np.append(dates, [dates[-1]]*2)
    countries = np.append(countries, [countries[-1]]*2)

#Find unnique countries
idx = np.where(countries[:-1] != countries[1:])[0]
idx = np.append(idx, idx[-1]+1)
D = dates[idx+1]
DD= dates[idx+2]
C = countries[idx]


#Output all trips
outFile = open('locHist.csv','w')
totalDays   = {}
totalNZDays = {}
p = startdate
for i in range(len(D)):
    c = C[i]
    d = D[i]
    dt = (d.date() - p.date());
    outStr = "{cnt}, {st}, {en}, {d}".format(cnt=c, st=p.strftime('%m/%d/%y'), en=d.strftime('%m/%d/%y'), d=dt.days+1)
    p = DD[i]

    print(outStr)
    outFile.write(outStr+"\n")

    year = p.year
    if not year in totalDays:
        totalDays[year]   = 0
        totalNZDays[year] = 0

    if not c in ['United States', 'Puerto Rico']:
        totalDays[year] += dt.days + 1
    if c in ['New Zealand']:
        totalNZDays[year] += dt.days + 1


outFile.close()
print('Total days outside of US', sum(totalDays.values()))



#Output USCIS format
nTrips = 0
nDaysTotal  = 0
cList = []
DateLeft  = None

outStrings = []
for i in range(len(D)):
    c = C[i]

    if c in ['United States', 'Puerto Rico']:
        if cList == []: continue
        DateReturn = DD[i-1]

        nDays = (DateReturn - DateLeft).days
        outStr = "{Left}, {Return}, No, {list}, {daysOut}".format(
                    Left=DateLeft.strftime('%m/%d/%y'), Return=DateReturn.strftime('%m/%d/%y'),
                    list = ', '.join(np.unique(cList)),
                    daysOut = nDays)
        outStrings += [outStr]
        print(outStr)

        nDaysTotal += nDays
        cList = []
        DateLeft = D[i]
        continue

    if cList == []:
        nTrips  += 1
        DateLeft = D[i-1]

    cList += [c]

outFile = open('USCIS.csv','w')
outFile.write('\n'.join(outStrings[::-1]))
outFile.close()

print('Total days  outside of US', nDaysTotal)
print('Total trips outside of US', nTrips)


#find dates in NZ:
# idx = np.where(C == 'New Zealand')[0]
# enterD = np.array([d.date() for d in D[idx-1]])
# leftD  = np.array([d.date()+timedelta(days=0) for d in D[idx]])

# rangeofInterest = np.concatenate(([enterD[0]], leftD))
# lengthinNZ = np.array([0] + [x.days+1 for x in (leftD - enterD)])

# daysofInterest = np.array([timedelta(days=x) + rangeofInterest[0] for x in
# 							range((rangeofInterest[-1] - rangeofInterest[0]).days)])

# daysinNZ       = np.zeros(np.size(daysofInterest))
# cumLengthinNZ = np.zeros(np.size(daysofInterest))

# for (i, d) in enumerate(daysofInterest):
# 	inrange = ~ np.alltrue(~ np.logical_and(enterD <= d, leftD >= d))
# 	if inrange:
# 		daysinNZ[i] = 1

# for (i, d) in enumerate(daysofInterest):
# 	inrange = np.logical_and(daysofInterest >= d - timedelta(days=365) , daysofInterest <= d)
# 	cumLengthinNZ[i] = np.sum(daysinNZ[inrange])

# print('Total days in NZ', totalNZDays)
# print('Max on rolling basis', np.max(cumLengthinNZ))


