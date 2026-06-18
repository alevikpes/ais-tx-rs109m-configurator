import serial
import time


max_retries = 3


def serial_cmd(ser, tx_bytes, expected_prefix, read_extra=0):
    print(f'Writing data: {tx_bytes}')
    # Send command and check response, with retries. Returns full response bytes.
    for attempt in range(max_retries):
        ser.reset_input_buffer()
        ser.write(tx_bytes)
        r = ser.read(len(expected_prefix))
        print(f'Expected prefix length: {r.hex()}')
        if r == expected_prefix:
            if read_extra > 0:
                re = ser.read(read_extra)
                print(f'Read extra: {re.hex()}')
                return r + re

            return r

    return None


with serial.Serial(
    '/dev/ttyUSB0',
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1,
    write_timeout=3,
) as ser:
    # --- wake up device ---
    ser.rts = False
    ser.rts = True
    ser.read(0xffff)

    # Send handshake
    ser.write(bytes.fromhex('59 01 42 06 30 30 30 30 30 30'))
    handshake = ser.read(32)
    print(f'Handshake response [HEX]: {handshake.hex()}')
    print(
        'Handshake response: '
        #f'{handshake.decode("ascii", errors="ignore").strip()}'
        f'{bytes.fromhex("95 20")}'
    )

    # If you receive 95 20, try read-config
    if handshake.startswith(bytes.fromhex('95 20')):
        ser.write(bytes.fromhex('51 40'))
        ser.flush()

        time.sleep(0.5)

        data = ser.read_all()
        print(f'Config length: {data.len()}\nConfig [HEX]: {data.hex()}')
        print(f'Config: {data.decode("ascii", errors="ignore").strip()}')
