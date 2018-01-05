import json  
from collections import OrderedDict

def bytearry2json(content): 
    UAFmsg = content   
    UAFmsg = UAFmsg.replace('\x00{"uafProtocolMessage":', '').replace('"[', '[').replace(']"', ']').replace('\\"', '"').replace('\\n', '\n')
    UAFmsg = UAFmsg[:len(UAFmsg)-1]
    UAFmsg = UAFmsg.split('"')
    uaf_scope = '[{"assertions": [{ "assertion":"%s", "assertionScheme":"%s"}], "fcParams":"%s", "header":{ "appID":"%s", "op":"%s", "serverData":"%s", "upv":{ "major":1, "minor":0 }}}]' % (UAFmsg[5], UAFmsg[9], UAFmsg[13], UAFmsg[19], UAFmsg[23], UAFmsg[27])

    data = json.loads(uaf_scope, object_pairs_hook=OrderedDict, strict=False) 
    json_ = json.dumps(data, separators=(',', ':')) 
    return uaf_scope 

    