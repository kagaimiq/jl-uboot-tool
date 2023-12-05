from scsiio import SCSIDev
from scsiio.common import SCSIException
import sys, os, time
import subprocess, re

def find_jl_devices(venfilter=None):
    devpaths = []

    if sys.platform == 'linux':
        #
        # FIXME - hardcoded '/dev' probably isn't right..
        #
        devdir = '/dev'

        for path in os.listdir(devdir):
            if path.startswith('sg'):
                devpaths.append(os.path.join(devdir, path))

    elif sys.platform == 'win32':
        #
        # XXX FIXME TODO - proper way of finding that 
        #    also it limits to 128 volumes which won't work
        #    right after it exceeds 127.
        #    (as the drives doesn't occupy the same number)
        #

        #for i in range(26):
        #    path = '\\\\.\\%s:' % chr(ord('A') + i)
        #    if os.path.exists(path):
        #        devpaths.append(path)

        for i in range(128):
            path = '\\\\.\\HardDiskVolume%d' % i
            if os.path.exists(path):
                devpaths.append(path)

        # stolen from UF2 utility thing
        # yet it doesn't really work now
        '''
        #res = subprocess.check_output(['wmic', 'DISKDRIVE', 'get', 'DeviceID,InterfaceType']).decode('ascii')
        res = subprocess.check_output(['wmic', 'DISKDRIVE', 'get', 'DeviceID,InterfaceType']).decode('ascii')
        print(res)

        for line in res.split('\n'):
            words = re.split('\s+', line)
            if len(words) < 2: continue
            print(words)
            if words[1] == 'USB':
                devpaths.append(words[0])
        '''

    else:
        raise NotImplemented('Platform %s is not supported (yet)' % sys.platform)

    devs = []

    for path in devpaths:
        try:
            with SCSIDev(path) as dev:
                inquiry = bytearray(36)
                dev.execute(b'\x12' + b'\x00\x00' + len(inquiry).to_bytes(2, 'big') + b'\x00', None, inquiry)

                vendor   = str(inquiry[ 8:16], 'ascii').strip()
                product  = str(inquiry[16:32], 'ascii').strip()
                revision = str(inquiry[32:36], 'ascii').strip()

                if venfilter is not None:
                    if vendor.lower() != venfilter.lower():
                        continue

                # TODO: filter based on the 'vendor', not on 'product', we don't want any wrong false-positive
                if product.startswith(('UBOOT', 'UDISK', 'DEVICE')):
                    devs.append({'path': path, 'name': '%s %s (%s) at %s' % (vendor, product, revision, path)})

        except SCSIException:
            pass

        except PermissionError:
            pass

    return devs

def choose_jl_device(venfilter=None, wait=True):
    att = 0

    if venfilter is not None:
        print('Searching for "%s" devices..' % venfilter)
    else:
        print('Searching for some JieLi devices..')

    while True:
        devs = find_jl_devices(venfilter)

        if not wait:
            break

        else:
            if len(devs) > 0:
                if att > 0:
                    print(' - got one!')
                break

            att += 1

            print('\rNo devices found yet. Attempt %d' % att, end='', flush=True)

        time.sleep(1)

    ## ---------------------------------------------- ##

    if len(devs) == 0:
        print('No devices found')

    elif len(devs) == 1:
        print('Found a device: %s' % devs[0]['name'])
        return devs[0]['path']

    else:
        print('Found %d devices, please choose the one you want to use right now, or quit (q)' % len(devs))

        for i, dev in enumerate(devs):
            print('%3d: %s' % (i, dev['name']))

        print()

        while True:
            inp = input('[0..%d|q]: ' % (len(devs) - 1)).strip()

            if inp == '': continue

            if inp.lower().startswith('q'):
                break

            try:
                num = int(inp)
            except ValueError:
                print('Please enter a number!')
                continue

            try:
                return devs[num]['path']
            except IndexError:
                print('Please enter a number in range 0..%d!' % (len(devs) - 1))

    return None

if __name__ == '__main__':
    devs = find_jl_devices()

    if len(devs) > 0:
        print('Found %d device(s)' % len(devs))

        for i, dev in enumerate(devs):
            print('%3d: %s' % (i, dev['name']))

    else:
        print('No devices found.')
        exit(1)
