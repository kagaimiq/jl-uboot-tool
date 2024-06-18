""" Miscellaneous utilities """

__all__ = [
    'hexdump',
    'anyint',
    'align_by',
    'align_to'
]

def hexdump(data, width=16, off=0, size=None, base=0):
    if size is None: size = len(data) - off
    for off in range(off, off+size, width):
        line = data[off:off+width]

        #
        # Make a hex line
        #
        hexline = ''
        for i in range(width):
            if (i % 8) == 0:
                hexline += ' '

            if i >= len(line):
                hexline += '-- '
            else:
                hexline += '%02x ' % line[i]

        #
        # Make a text line
        #
        line = bytearray(line + (b' ' * (width - len(line))))
        for i, b in enumerate(line):
            if b < 0x20: # or b >= 0x7F:
                line[i] = ord('.')

        txtline = line.decode('1251', errors='replace')  # 1251 rocks!

        print('%08x:%s %s' % (off+base, hexline, txtline))

def anyint(s):
    """ Any-base string to integer conversion """
    return int(s, 0)

def align_by(val, alignment):
    """ Give an amount to pad the val to a specified alignment """
    val = val % alignment
    if val: val = alignment - val
    return val

def align_to(val, alignment):
    """ Pad the val to a specified alignment """
    return val + align_by(val, alignment)

