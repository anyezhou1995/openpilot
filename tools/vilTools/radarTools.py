#!/usr/bin/env python
import cereal.messaging as messaging

import time

if __name__ == '__main__':
    
    while 1:
        sm= messaging.SubMaster(['liveTracks'])
        sm.update(0)
        
        print(sm['liveTracks'])
        
        time.sleep(1)
    
    