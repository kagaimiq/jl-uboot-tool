from scsiio import SCSIDev
import sys

def find_jl_devices():
    devs = []

    for i in range(128): # 128 may be enough?...
        if sys.platform == 'linux':
            path = '/dev/sg%d' % i
        elif sys.platform == 'win32':
            path = '\\\\.\\HardDiskVolume%d' % i
        else:
            raise NotImplemented('Platform %s is not supported (yet)' % sys.platform)

        try:
            with SCSIDev(path) as dev:
                data = bytearray(36)
                dev.execute(b'\x12' + b'\x00\x00' + len(data).to_bytes(2, 'big')
                                                       + b'\x00', None, data)

                vendor = str(data[8:16], 'ascii').strip()
                product = str(data[16:32], 'ascii').strip()
                prodrev = str(data[32:36], 'ascii').strip()

                if product.startswith(('UBOOT', 'UDISK', 'DEVICE')):
                    devs.append({'path': path, 'name': '%s %s (%s) at %s' % (vendor, product, prodrev, path)})
        except:
            pass

    return devs

def choose_jl_device():
    devs = find_jl_devices()

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
