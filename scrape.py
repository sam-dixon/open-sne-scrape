import sys
import os
import requests
import json
import pandas as pd
import datetime as dt
import pickle
from astropy.time import Time
from astropy import units as u
from IPython import embed


def ymd_to_mjd(date):
    """Convert a YYYY/MM/DD date string to MJD"""
    y, m, d = [int(n) for n in date.split('/')]
    date = Time(dt.datetime(y, m, d))
    return date.mjd


def sn_metadata(datadict):
    """
    Get metadata from the parsed JSON. This will add the name,
    MJD of max, sources, and heliocentric redshifts
    """
    meta = {}
    sn_name = datadict.keys()[0]
    meta['name'] = sn_name
    meta['t_max'] = ymd_to_mjd(datadict[sn_name]['maxvisualdate'][0]['value'])
    meta['sources'] = datadict[sn_name]['sources']
    meta['redshift'] = datadict[sn_name]['redshift'][0]['value']
    return meta


def spectra_metadata(datadict, datadir='./data'):
    """
    Writes the spectra to file if datadir is not None, collects selected
    metadata, and returns that metadata in a dictionary
    """
    sn_name = datadict.keys()[0]
    speclist = datadict[sn_name]['spectra']
    t_max = ymd_to_mjd(datadict[sn_name]['maxvisualdate'][0]['value'])
    for spec in speclist:
        time, t_unit = float(spec['time']), spec['u_time'].lower()
        date = Time(time, format=t_unit).mjd
        phase = date-t_max
        if datadir is not None:
            if not os.path.isdir(datadir):
                os.makedirs(datadir)
            if phase >= 0:
                fname = '{}_P{:2d}.txt'.format(sn_name, int(phase*10))
            else:
                fname = '{}_M{:2d}.txt'.format(sn_name, int(abs(phase*10)))
            path = os.path.join(datadir, fname)
            pd.DataFrame(spec['data']).to_csv(path, index=None, header=False)
        spec_meta = {}
        spec_meta['phase'] = phase
        spec_meta['source'] = spec['source']
        spec_meta['path'] = path
    return spec_meta


if __name__ == '__main__':
    names = pd.read_csv(sys.argv[1]).Name
    prefix = 'https://sne.space/astrocats/astrocats/supernovae/output/json/'
    urls = [prefix + name.replace(' ', '%20')+'.json' for name in names]
    metadata = {}
    for url in urls[:20]:
        print('Parsing '+url.split('/')[-1])
        r = requests.get(url)
        data = json.loads(r.content)
        sn_meta = sn_metadata(data)
        sn_meta['spectra'] = spectra_metadata(data)
        metadata[data.keys()[0]] = sn_meta
    pickle.dump(metadata, open('META.pkl', 'wb'))
