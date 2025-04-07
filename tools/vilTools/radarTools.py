#!/usr/bin/env python
import cereal.messaging as messaging

import time
import numpy as np
import pickle
import socket

def send_array(sock, array, ip="192.168.254.14", port=5000):
    serialized_data = pickle.dumps(array)
    sock.sendto(serialized_data, (ip, port))

#Example output
'''
[ ( trackId = 0,
    dRel = 1.2,
    yRel = -0.04,
    vRel = 0,
    aRel = nan,
    yvRel = nan,
    measured = true ),
  ( trackId = 1,
    dRel = 0.48,
    yRel = -0,
    vRel = 0,
    aRel = nan,
    yvRel = nan,
    measured = true ),
  ( trackId = 29,
    dRel = 16.08,
    yRel = 16.64,
    vRel = -0.05,
    aRel = nan,
    yvRel = nan,
    measured = true ) ]
'''

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sm= messaging.SubMaster(['liveTracks'])
    try:
        while 1:
            sm.update()
            mes= sm['liveTracks']
            
            points= mes.points
            if len(points) > 0:
                d= [[points[i].trackId, points[i].dRel, points[i].yRel] for i in range(len(points))]
                d= np.array(d)
                print(d)
            
            send_array(sock, d)
            
            time.sleep(0.05)
            
    finally:
        sock.close()
        
    
    

