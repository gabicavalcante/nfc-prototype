import json  

def bytearry2json(content): 
    UAFmsg = content 
    UAFmsg = UAFmsg.replace('\x00{"uafProtocolMessage":', '').replace('"[', '[').replace(']"', ']').replace("\\", "").replace("\x00", "").replace("\\", "")
    UAFmsg = UAFmsg[:len(UAFmsg)-1]
    UAFmsg = UAFmsg.split('"')
    uaf_scope = [{  
	      "assertions":[  
	         {  
	            "assertion":UAFmsg[5],
	            "assertionScheme":UAFmsg[9]
	         }
	      ],
	      "fcParams":UAFmsg[13],
	      "header":{  
	         "appID":UAFmsg[19],
	         "op":UAFmsg[23],
	         "serverData":UAFmsg[27],
	         "upv":{  
	            "major":UAFmsg[32][1:2],
	            "minor":UAFmsg[32][1:2]
	         }
	      }
	   }] 
    json_ = json.dumps(uaf_scope) 
    print(json_)
    return json_ 