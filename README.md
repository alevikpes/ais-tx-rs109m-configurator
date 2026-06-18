# RS-109M AIS Net Locator AIS buoy

This repo contains a [config tool](rs109m.py) and some info about the
[RS-109M](https://opcenter.de/pub/Boot/RS_109M_manual.pdf) Net Locator AIS
device.

The device is sold by
[Socotran](http://web.archive.org/web/20210806132018/https://socotran.com/products/fishing-net-tracker-locator-gps-marine-ais-netsonde-net-sonde-for-boating-rs-109m)
and is also available on Ali\*xpress and e\*ay. In the UK, it is also sold by
[East Anglian Radio](http://web.archive.org/web/20210806152420/https://www.eastanglianradio.com/rs-109-ais.html).

[![buoy complete](images/buoy_800px.jpg)](images/buoy.jpg)

Information was gathered by personal observations like photographs of the
PCB and logging of the data stream while configuring.


## Attention

It is questionable if this device could be operated as a proper
("valid", "legal") AIS device!

Take appropriate measures when trying out things (e.g. shield RF, dummy load).

See [FCC statement](http://web.archive.org/web/20210806152632/https://docs.fcc.gov/public/attachments/DA-18-1211A1_Rcd.pdf)
concerning the ban of fishing net buoys that use radio frequencies reserved
for marine navigation safety.


## Usage on Linux

[rs109m.py](rs109m.py) is a configuration tool written in Python. Current
version is for command line usage only. There is no intention to make a
GUI version.


### Connecting to PC

You will need a special programming cable to connect the device to the PC.
It is a standard FTDI USB adapter connected to the compatible plug, so if you
are into electronics and you have the corresponding components, you may try
to make this connection yourself. If not, it is best to buy the device
with the cable. Immediately after connecting the device, check the
`dmesg` output. You must see something like this:
```bash
[ 3268.873053] usb 1-5: new full-speed USB device number 7 using xhci_hcd
[ 3268.998090] usb 1-5: New USB device found, idVendor=xxxx, idProduct=xxxx, bcdDevice= x.xx
[ 3268.998099] usb 1-5: New USB device strings: Mfr=0, Product=2, SerialNumber=0
[ 3268.998102] usb 1-5: Product: USB Serial
[ 3269.052589] usbcore: registered new interface driver ch341
[ 3269.052610] usbserial: USB Serial support registered for ch341-uart
[ 3269.052626] ch341 1-5:1.0: ch341-uart converter detected
[ 3269.053115] usb 1-5: ch341-uart converter now attached to ttyUSB0
```
In this case the device is connected to `/dev/ttyUSB0` port, which would be
the default for most of the devices.


### Writing data

##### Create a virtual environment

If you don't know how to create and use python virtual environments, check
online tutorials. For this project I recommend using standard `venvs` module
and external `pip-tools` module. First run:
```bash
python -m venvs /path/to/virtual/env
```
to create a virtual environment. Then run:
```bash
source /path/to/virtual/env/bin/activate
```
to activate it. I recommend to upgrade pip, since it is not always the latest
virsion by default, and install `pip-tools`:
```bash
pip install --upgrade pip pip-tools
```
Lastly, run:
```bash
pip-compile && pip-sync
```
to create a dependencies file `requirements.txt` and to install all the
dependencies.

##### Execution

Every time you want to run the script, you need to activate the virtual
environment, which was created in the previous chapter:
```bash
source /path/to/virtual/env/bin/activate
```
Then run:
```bash
python src/rs109m.py -h` to see the help message.
```
When reading or writing the data, the `device` positional argument is
required, the rest are optional. You can get it from the `dmesg` command
as explained earlier in [Connecting to PC](#connecting-to-pc).

The default mode is reading. In order to write data, the `-W` flag must be
explicitely specified.


## Internals

Unscrewing the cap gives access to on/off switch (a magnet which acts
on a reed relais) and the charging and programming connectors:

[![buoy connectors](images/buoy_connectors_800px.jpg)](images/buoy_connectors.jpg)

The PCB in all its glory:

[![pcb complete](images/pcb_complete_800px.jpg)](images/pcb_complete.jpg)

[![pcb front side](images/pcb_front_800px.jpg)](images/pcb_front.jpg)

[![pcb back side](images/pcb_back_800px.jpg)](images/pcb_back.jpg)


## Manufacturer's software for Windows

The software is available upon request from the dealer. There are two
variants (ST_109M_SETTING.exe and RS_10xM_SETTING.exe) which are
functionally identical - the RS-10xM version is a rebrand with a different
icon and default device name.

It is a Qt application compiled for Windows. I could get it to start with
Wine 6.14 on Linux (Linux 5.12.15-arch1-1 x86_64, ArchLinux distribution),
but had no chance to get the serial communications running.

![programming software screenshot](images/pcsw17_screenshot_en.png)

Using the software on a Windows VM, I was able to produce some [logs](logs/)
to get knowledge of the serial protocol.

"Production mode" seems to do nothing more than incrementing MMSI number
on subsequent writes.


## Configuration protocol

See [logs dir](logs/) for data I obtained while doing tiny configuration
changes.

The protocol is via serial 115200,8n1.

Device expects an init sequence with a password. This password is a weak
protection, as it defaults to 000000 and is in the range of 0..999999.
It seems that the password protection can be bypassed by supplying a
zero-length password init sequence.

Initialisation has to take place in the first few seconds after power-up.

After init, you can do 3 things:
* read config
* write config
* set/clear password

Config is done as a whole block of data with some values weirdly stuffed
together to save some space.

Original software always reads/writes 0x40 bytes, but there is possibility
to access 0xff bytes.

When supplying an "update" command without actually delivering any data,
there seems to be a glitch leading to the content from an unknown memory
region being stored in config space. This can be restored by simply
copying default memory content (0xff length) again.

Different buoy variants encode battery status differently:
* Some buoys send battery voltage as 1/10V in place of the Reference A value.
* Some buoys report battery level (%) in the vendor serial number field.

Battery voltage is measured via a voltage divider (43k/56k or 47k/56k - can
not measure exactly due to small part size) on PB1 (pin 19) of the STM32F103.


## Hardware

Buoy is built around Si4463 radio.

Microprocessor matches the layout of ubiquitous STM32F103C8, but as it has
no markings, it could as well be a clone or different STM32 ARM µC. A SWDIO
debug port is available on the PCB (marked G=ground, C=clock, D=swdio,
V=VCC), but did not check.

GPS module is ATGM332D with GPS and BDS/BeiDou support, but no GLONASS. It
seems to be tied only with its TX pin to an RX pin of the µC.

[Adrain Studer did also some investigations](https://mobile.twitter.com/AdiStuder/status/1380290819056304130)
and posted a
[pcb photo](http://web.archive.org/web/20210809180746/https://pbs.twimg.com/media/Ex3FZafUcAIMJLL?format=jpg&name=4096x4096).

See [MAIANA AIS project](https://github.com/peterantypas/maiana) for a
far more capable Open Source board.
