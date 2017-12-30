#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Quick start example that presents how to use fido with IOT"""

from __future__ import print_function
import sys
import nfc
import requests
from door_protocol import DoorProtocol
from settings import fido_server
import time 

BLOCK_SIZE = 250

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
        print("** Opss ** I'm expecting HELLO msg, but card sent to me: %s. len: %d\n", rapdu, len(rapdu))
        sys.exit(1)

    # FIDO Auth Request Message
    print("Doing AuthRequest to FIDO UAF Server\n");
    UAFurl = fido_server['AUTH_REQUEST_MSG'] % (fido_server['SCHEME'], fido_server['HOSTNAME'], fido_server['PORT'], fido_server['AUTH_REQUEST_ENDPOINT'])
    
    r = requests.get(UAFurl)
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

    # Sending UAFRequestMessage to card
    chunks = len(content)
    msg_packages = ([ content[i:i + BLOCK_SIZE] for i in range(0, chunks, BLOCK_SIZE) ])
    for pack, index in zip(msg_packages, range(1, chunks+1)):
        print("Seding package %s..." % index)
        pbtTx = pack
        szTx = len(pbtTx)
        szRx = len(DoorProtocol['DOOR_OK'])
        res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
        print("REC: " + rapdu)

    print("\nSending READY!")

    pbtTx = DoorProtocol['DOOR_READY']
    szTx = len(pbtTx)
    szRx = len(DoorProtocol['DOOR_WAIT'])
    res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
    print("REC: " + rapdu)
    print("\nWaiting...\n")

    while rapdu == DoorProtocol['DOOR_WAIT']:
        time.sleep(5)
        print("\nWaiting...\n") 
        szTx = len(pbtTx)
        szRx = len(DoorProtocol['DOOR_WAIT'])
        res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
        print("SEND: " + pbtTx)
        print("REC: " + rapdu)
        if (rapdu == DoorProtocol['DOOR_DONE']):
            print("Sending RESPONSE!")
            pbtTx = DoorProtocol['DOOR_RESPONSE']
            szTx = len(pbtTx)
            szRx = len(DoorProtocol['DOOR_WAIT'])
            res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
            print("RED " + rapdu)
            break

    #timeout = sys.maxsize
    #while True:
    #    print("\nWaiting...\n") 
    #    szTx = len(pbtTx)
    #    szRx = len(DoorProtocol['DOOR_WAIT'])
    #    res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
    #    print("SEND: " + pbtTx)
    #    print("REC: " + rapdu)
    #    if (rapdu == DoorProtocol['DOOR_DONE']):
    #        print("Sending RESPONSE!")
    #        pbtTx = DoorProtocol['DOOR_RESPONSE']
    #        szTx = len(pbtTx)
    #       szRx = len(DoorProtocol['DOOR_WAIT'])
    #       res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
    #       print("RED " + rapdu)
    #       break
    #   timeout -= 1
    #   if timeout <= 0: break

    #szTx = len(pbtTx)
    #szRx = len(DoorProtocol['DOOR_WAIT'])
    #res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
    #print("SEND: " + pbtTx)
    #print("REC: " + rapdu)
    #if (rapdu == DoorProtocol['DOOR_DONE']):
    #    print("Sending RESPONSE!")
    #    pbtTx = DoorProtocol['DOOR_RESPONSE']
    #    szTx = len(pbtTx)
    #    szRx = len(DoorProtocol['DOOR_WAIT'])
    #    res, rapdu = cardTransmit(pnd, pbtTx, szTx, szRx) 
    #    print("RED " + rapdu)  

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
