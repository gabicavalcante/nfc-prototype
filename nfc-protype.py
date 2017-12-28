#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Quick start example that presents how to use libnfc"""

from __future__ import print_function
import sys
import nfc
import requests
from door_protocol import DoorProtocol
from settings import fido_server
import time 
BLOCK_SIZE = 250

# Reset the default Crtl-C behavior
import signal
try:
    signal.signal(signal.SIGINT, signal.SIG_DFL)
except ValueError:
    pass

print('Version: ', nfc.__version__)

context = nfc.init()

# pnd : nfc_device (currently used device)
pnd = nfc.open(context)
if pnd is None:
    print('ERROR: Unable to open NFC device.')
    sys.exit(1)

if nfc.initiator_init(pnd) < 0:
    nfc.perror(pnd, "nfc_initiator_init")
    print('ERROR: Unable to init NFC device.')
    sys.exit(1)

print('NFC reader: %s opened' % nfc.device_get_name(pnd))

# nfcProtocol
nmMifare = nfc.modulation()
nmMifare.nmt = nfc.NMT_ISO14443A
nmMifare.nbr = nfc.NBR_106

print("Polling for target...\n");
nt = nfc.target()
ret = nfc.initiator_select_passive_target(pnd, nmMifare, 0, 0, nt)
print("Target detected!\n");

# cardTransmit   

# pbtTx : bytes (contains a byte array of the frame that needs to be transmitted.)
# pbtTx = '\x00\xA4\x04\x00\x07\xF0\x39\x41\x48\x14\x81\x00\x00'
pbtTx = DoorProtocol['APDU']
# szTx : int (contains the length in bytes.)
szTx = len(pbtTx)
# szRx : int (size of pbtRx (Will return NFC_EOVFLOW if RX exceeds this size))
szRx = len(DoorProtocol['DOOR_HELLO']) 
# print(help(nfc.initiator_transceive_bytes))
res, rapdu = nfc.initiator_transceive_bytes(pnd, pbtTx, szTx, szRx, 800)
print("Application selected!\n");

# verificar se rapdu é DOOR_HELLO
print(">>>> " + rapdu)

time.sleep(1)

print("Doing AuthRequest to FIDO UAF Server\n");
UAFurl = fido_server['AUTH_REQUEST_MSG'] % (fido_server['SCHEME'], fido_server['HOSTNAME'], fido_server['PORT'], fido_server['AUTH_REQUEST_ENDPOINT'])
# print(UAFurl) # url
r = requests.get(UAFurl)
if (r.status_code == 200):
	print("request 200")
else:
	print("** Opss ** Error to connect to FIDO Server")
 
content = r.content 
print(r.content)

blocks = (len(content) / BLOCK_SIZE) + 1 

pbtTx = "BLOCK:%s" % blocks
print("Sending number of blocks: %s " % pbtTx);
szTx = len(pbtTx)
szRx = len(DoorProtocol['DOOR_NEXT']) 
res, rapdu = nfc.initiator_transceive_bytes(pnd, pbtTx, szTx, szRx, 800)
print(">>>> " + rapdu)

"""start, end = 0, BLOCK_SIZE - 1
for block in blocks:
    pbtTx = content[start:end]
    start = end + 1
    end += BLOCK_SIZE

    szTx = len(pbtTx)
    szRx = szTx 
    res, rapdu = nfc.initiator_transceive_bytes(pnd, pbtTx, szTx, szRx, 800)
    print(">>>> " + rapdu)"""


chunks = len(content)
msg = ([ content[i:i + BLOCK_SIZE] for i in range(0, chunks, BLOCK_SIZE) ])
for d in msg:
    pbtTx = d
    szTx = len(pbtTx)
    szRx = len(DoorProtocol['DOOR_OK'])
    res, rapdu = nfc.initiator_transceive_bytes(pnd, pbtTx, szTx, szRx, 800)
    print("SEND >>>> " + pbtTx)
    print("REC ------------- " + rapdu)

print("Sending READY!")

pbtTx = DoorProtocol['DOOR_READY']
szTx = len(pbtTx)
szRx = len(DoorProtocol['DOOR_WAIT'])
res, rapdu = nfc.initiator_transceive_bytes(pnd, pbtTx, szTx, szRx, 800)
print(">>>> " + rapdu)

while rapdu == DoorProtocol['DOOR_WAIT']:
    print("Waiting...") 
    szTx = len(pbtTx)
    szRx = len(DoorProtocol['DOOR_WAIT'])
    res, rapdu = nfc.initiator_transceive_bytes(pnd, pbtTx, szTx, szRx, 800)
    print("SEND >>>> " + pbtTx)
    print("REC ------------- " + rapdu)
    if (rapdu == DoorProtocol['DOOR_DONE']):
        print("Sending RESPONSE!")
        pbtTx = DoorProtocol['DOOR_RESPONSE']
        szTx = len(pbtTx)
        szRx = len(DoorProtocol['DOOR_WAIT'])
        res, rapdu = nfc.initiator_transceive_bytes(pnd, pbtTx, szTx, szRx, 800)
        print(">>>> " + rapdu)
        break


nfc.close(pnd)
nfc.exit(context)
