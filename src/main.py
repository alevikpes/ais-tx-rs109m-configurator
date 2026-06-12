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
    #time.sleep(0.05)
    ser.rts = True
    #time.sleep(0.2)
    ser.read(0xffff)
    #ser.timeout = 3

    # --- AUTH ---
    #password = b'000000'
    #password = 0x00
    #auth_cmd = bytes([0x59, 0x01, 0x42, len(password)]) + password

    #r = serial_cmd(ser, auth_cmd, b'\x95\x20')

    #ser.reset_input_buffer()
    #ser.write(auth_cmd)
    #time.sleep(0.1)
    #ack = ser.read(2)
    #print("AUTH ACK:", ack.hex())

    #ser.reset_input_buffer()
    #ser.write(bytes([0x59, 0x01, 0x42, 0x00]))
    #ack = ser.read(2)
    #print("AUTH ACK:", ack.hex())
    #if ack != b"\x95\x20":
    #    raise RuntimeError("Auth failed")

    ## --- READ CONFIG ---
    #ser.reset_input_buffer()
    #ser.write(bytes([0x51, 0x40]))
    #header = ser.read(2)
    #print("HEADER:", header.hex())
    #data = ser.read(0x40)
    #print("DATA LENGTH:", len(data))
    #print("DATA:", data.hex())

    # Send handshake
    ser.write(bytes.fromhex('59 01 42 06 30 30 30 30 30 30'))
    #ser.flush()

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
