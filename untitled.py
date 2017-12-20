#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Quick start example that presents how to use libnfc"""

from __future__ import print_function
import sys
import nfc
from door_protocol import DoorProtocol

print('Version: ', nfc.__version__)

context = nfc.init()

# nfcInitListen
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
# res = 0
rapdu = [0] * 264
#capdu = DoorProtocol.APDU
pbtTx = '\x00\xA4\x04\x00\x07\xF0\x39\x41\x48\x14\x81\x00\x00'
szTx = sys.getsizeof(pbtTx);
rapdulen = sys.getsizeof(rapdu); 
print(help(nfc.initiator_transceive_bytes))
res = nfc.initiator_transceive_bytes(pnd, pbtTx, capdulen, rapdu, rapdulen, 500)
printf("Application selected!\n");

# verificar se rapdu é DOOR_HELLO
print(rapdu)

print('The following (NFC) ISO14443A tag was found:')
print('    ATQA (SENS_RES): ', end='')
nfc.print_hex(nt.nti.nai.abtAtqa, 2)
id = 1
if nt.nti.nai.abtUid[0] == 8:
    id = 3
print('       UID (NFCID%d): ' % id , end='')
nfc.print_hex(nt.nti.nai.abtUid, nt.nti.nai.szUidLen)
print('      SAK (SEL_RES): ', end='')
print(nt.nti.nai.btSak)
if nt.nti.nai.szAtsLen:
    print('          ATS (ATR): ', end='')
    nfc.print_hex(nt.nti.nai.abtAts, nt.nti.nai.szAtsLen)

nfc.close(pnd)
nfc.exit(context)
