"""Command line arguments parser."""

import argparse


def cli_parser():
    parser = argparse.ArgumentParser(
        description='RS-109M Net Locator AIS configurator.',
    )
    parser.add_argument(
        'device',
        help='[Required] Serial port where the device is connected (e.g. /dev/ttyUSB0).',
    )
    parser.add_argument('-m', '--mmsi', help='MMSI.')
    parser.add_argument('-n', '--ship-name', help='Ship name.')
    parser.add_argument(
        '-i',
        '--interval',
        help='Transmit interval in s [30..600].',
    )
    parser.add_argument(
        '-t',
        '--ship-type',
        help='Ship type, eg sail=36, pleasure craft=37.',
    )
    parser.add_argument('-c', '--call-sign', help='Call sign.')
    parser.add_argument(
        '-v',
        '--vendor-id',
        help='AIS unit vendor id (3 characters).',
    )
    parser.add_argument('-u', '--unit-model', help='AIS unit vendor model code')
    parser.add_argument(
        '-s',
        '--ser-num',
        help=(
            'AIS unit serial num '
            '(some devices report battery charge level here).'
        ),
    )
    parser.add_argument(
        '-A',
        '--ais2bow',
        help=(
            'distance AIS to bow (m) '
            '(some buoys report battery voltage here).'
        ),
    )
    parser.add_argument(
        '-B',
        '--ais2stern',
        help='distance AIS to stern (m).',
    )
    parser.add_argument(
        '-C',
        '--ais2port',
        help='distance AIS to port (m).',
    )
    parser.add_argument(
        '-D',
        '--ais2star',
        help='distance AIS to starboard (m).',
    )
    parser.add_argument(
        '-P',
        '--password',
        help='Password to access Net Locator. Default is 000000.',
    )
    parser.add_argument(
        '--setpass',
        help='Set new password (use -P for current password).',
    )
    parser.add_argument(
        '--clearpass',
        help='Clear password (use -P for current password)',
        action='store_true',
    )
    parser.add_argument(
        '-E',
        '--extended',
        help='Operate on 0xff size config instead of default 0x40',
        action='store_true',
    )
    parser.add_argument(
        '-W',
        '--write',
        help='Write config to Net Locator',
        action='store_true',
    )
    parser.add_argument(
        '-R',
        '--noread',
        help='Do not read from Net Locator',
        action='store_true',
    )
    return parser.parse_args()
