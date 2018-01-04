#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Quick start example that presents how to use fido with IOT

TODO: 
- [fix] get the uaf msg from the app, convert to json and send to fido server
- [improve] check the returns

PS: if fido server and raspberry are on differents networks, is needed change the ip sended in UAFRequestMessage to card.
"""

from __future__ import print_function
import sys
import nfc
import requests
from door_protocol import DoorProtocol
from settings import fido_server
import time 
import json
import re 
from util import bytearry2json

BLOCK_SIZE = 200

context = None # context
pnd = None     # device
nt = None      # target


def cardTransmit(pnd, pbtTx, szTx, szRx):
    """ Send data to target then retrieve data from target.
    
    @param pnd: currently used device
    @param pbtTx: contains a byte array of the frame that needs to be transmitted (bytes)
    @param szTx: contains the length in bytes (int)
    @param szRx: size of pbtRx (Will return NFC_EOVFLOW if RX exceeds this size) (int)

    @return res: received bytes count on success, otherwise returns libnfc's error code (int)
    @return rapdu: response from the target (bytes)
    """  
    res, rapdu = nfc.initiator_transceive_bytes(pnd, pbtTx, szTx, szRx, 800)
    return res, rapdu


def nfcInitListen(): 
    """ Open nfc device and set opened NFC device to initiator mode: 
    """ 

    global pnd, context
    pnd = nfc.open(context)

    if pnd is None:
        print('ERROR: Unable to open NFC device.')
        sys.exit(1)

    if nfc.initiator_init(pnd) < 0:
        nfc.perror(pnd, "nfc_initiator_init")
        print('ERROR: Unable to init NFC device.')
        sys.exit(1)

    print('NFC reader: %s opened' % nfc.device_get_name(pnd))

def nfcProtocol():
    """ NFC Protocol
    """ 
    global pnd, nt, context

    nmMifare = nfc.modulation()
    nmMifare.nmt = nfc.NMT_ISO14443A
    nmMifare.nbr = nfc.NBR_106

    print("Polling for target...\n");
    nt = nfc.target()
    ret = nfc.initiator_select_passive_target(pnd, nmMifare, 0, 0, nt)
    print("Target detected!\n");

   
    # Select application
    pbtTx = DoorProtocol['APDU'] 
    szTx = len(pbtTx) 
    szRx = len(DoorProtocol['DOOR_HELLO'])  
    res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx)
    print("Application selected!");

    print("REC: " + rapdu)
    if rapdu != DoorProtocol['DOOR_HELLO']:
        print("** Opss ** I'm expecting HELLO msg, but card sent to me: %s. len: %d\n" % (rapdu, len(rapdu)))
        sys.exit(1)

    # FIDO Auth Request Message
    print("Doing AuthRequest to FIDO UAF Server\n");
    UAFurl = fido_server['AUTH_REQUEST_MSG'] % (fido_server['SCHEME'], fido_server['HOSTNAME'], fido_server['PORT'], fido_server['AUTH_REQUEST_ENDPOINT'])
    
    try:
        r = requests.get(UAFurl)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        sys.exit(1)

    if (r.status_code != 200):
    	print("** Opss ** Error to connect to FIDO Server")
        pbtTx = DoorProtocol['ERROR'] 
        szTx = len(pbtTx) 
        szRx = len(DoorProtocol['ERROR'])  
        res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx)
        sys.exit(1)
     
    content = r.content  
    blocks = (len(content) / BLOCK_SIZE) + 1 

    pbtTx = "BLOCK:%s" % blocks
    print("Sending number of blocks: %s " % pbtTx);
    szTx = len(pbtTx)
    szRx = len(DoorProtocol['DOOR_NEXT']) 
    res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx)
    print("REC: " + rapdu)

    if rapdu != DoorProtocol['DOOR_NEXT']:
        print("Error to send number of blocks")
        sys.exit(1)

    # Sending UAFRequestMessage to card
    chunks = len(content)
    msg_packages = ([ content[i:i + BLOCK_SIZE] for i in range(0, chunks, BLOCK_SIZE) ])
    for pack, index in zip(msg_packages, range(1, chunks+1)):
        print("Seding package %s..." % index)
        pbtTx = pack
        szTx = len(pbtTx)
        szRx = len(DoorProtocol['DOOR_OK'])
        res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
        if rapdu != DoorProtocol['DOOR_OK']:
            print("** Opss ** I'm expecting OK msg, but card sent to me: %s. len: %s" % (rapdu, len(rapdu)))
            sys.exit(1)
        print("REC: " + rapdu)

    print("\nSending READY!")

    pbtTx = DoorProtocol['DOOR_READY']
    szTx = len(pbtTx)
    szRx = len(DoorProtocol['DOOR_WAIT'])
    res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
    if rapdu != DoorProtocol['DOOR_WAIT']:
        print("** Opss ** I'm expecting WAIT msg, but card sent to me: %s. len: %s" % (rapdu, len(rapdu)))
        sys.exit(1)
    print("REC: " + rapdu) 
    print("\nWaiting...\n") 
    
    time.sleep(5)
    
    while rapdu == DoorProtocol['DOOR_WAIT']: 
        szTx = len(pbtTx)
        szRx = len(DoorProtocol['DOOR_DONE'])
        res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
        print("SEND: " + pbtTx)
        if rapdu != DoorProtocol['DOOR_DONE'] and rapdu != DoorProtocol['DOOR_WAIT']:
            print("** Opss ** I'm expecting DONE or WAIT msg, but card sent to me: %s. len: %s" % (rapdu, len(rapdu)))
            sys.exit(1)
        print("REC: " + rapdu)  

    if (rapdu == DoorProtocol['DOOR_DONE']):
        print("Sending RESPONSE!")
        pbtTx = DoorProtocol['DOOR_RESPONSE']
        szTx = len(pbtTx)
        szRx = len("BLOCK:  ")
        res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
        if not "BLOCK" in rapdu:
            print("** Opss ** I'm expecting RESPONSE msg, but card sent to me: %s. len: %s" % (rapdu, len(rapdu)))
            sys.exit(1)
        print("REC: " + rapdu) 

    r_decode = rapdu.decode('utf-8') 
    blocks = re.search(r'\d+', r_decode)
    blocks = blocks.group()  
    blocks = int(blocks)  
    print("\nBLOCKS:%s" % blocks)
    UAFmsg = '\0'
    for block in range(0, blocks):
        print("receiving block --> %s" % block)
        pbtTx = DoorProtocol['DOOR_NEXT'] 
        szTx = len(pbtTx)
        szRx = BLOCK_SIZE
        res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx)   
        UAFmsg += rapdu
 
    UAFmsg = "".join(map(chr, UAFmsg))
    UAFmsg = bytearry2json(UAFmsg)
    print(UAFmsg) 

    # FIDO Auth Request Message
    print("Forwarding card response to FIDO UAF Server: \n")
    UAFurl = fido_server['AUTH_REQUEST_MSG'] % (fido_server['SCHEME'], fido_server['HOSTNAME'], fido_server['PORT'], fido_server['AUTH_RESPONSE_ENDPOINT'])
    headers = { 'Accept': 'application/json', 'Content-Type': 'application/json'}
    r = requests.post(UAFurl, data=UAFmsg, headers=headers)
    print(r.text) 

   

if __name__ == '__main__':
    # Reset the default Crtl-C behavior
    import signal
    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    except ValueError:
        pass

    print('Version: ', nfc.__version__)

    while (1):
        context = nfc.init()

        if not context:
            print("Unable to init libnfc (malloc)\n");
            sys.exit(1)

        nfcInitListen()
        nfcProtocol()

        nfc.close(pnd)
        nfc.exit(context)
        time.sleep(2)
        print("\nstarting again...\n")

    sys.exit(0)
