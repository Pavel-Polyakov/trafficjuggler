import cPickle as pickle
import re

def convertToGbps(value):
    if value != 'None' and value != 'Down':
        return str(round(float(value)/1000,2))

def convertBandwidthToM(band):
    if re.match('m|g', band):
        band = re.sub('m','000',band)
        band = re.sub('g','000000',band)
    band = re.sub('000000$','m',band)
    band = re.sub('g$','000m',band)
    if re.match('m', band):
        re.sub('m','',band)
        band = float(band)/1000
    band = re.sub('m','',band)
    try:
        band = int(band)
    except ValueError:
        band = 0
    return band

def loaditems(file):
    try:
        with open('%s.pkl' % (file) ,'rb') as fr:
            items = pickle.load(fr)
        return items
    except IOError:
        return []

def saveitems(file,items):
    with open('%s.pkl' % (file),'wb') as fr:
        pickle.dump(items,fr)
