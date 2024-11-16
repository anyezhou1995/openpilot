import cereal.messaging as messaging
from opendbc.can.parser import CANParser
from openpilot.selfdrive.pandad import can_capnp_to_list, can_list_to_can_capnp

import logmanager
import time

class CP():
    def __init__(self):
        self.check_num= 100
        dbc_f = 'toyota_nodsu_pt_generated'
        # dbc_f = 'honda_civic_touring_2016_can_generated'
        
        self.signals = [
          ("RPM", "ENGINE_RPM"),
          ("WHEEL_SPEED_FL","WHEEL_SPEEDS"),
          ("WHEEL_SPEED_FR","WHEEL_SPEEDS"),
          ("WHEEL_SPEED_RL","WHEEL_SPEEDS"),
          ("WHEEL_SPEED_RR","WHEEL_SPEEDS"),
          ("STEER_RATE","STEER_ANGLE_SENSOR"),
          ("ACCEL_Y", "KINEMATICS"),
          ("YAW_RATE", "KINEMATICS"),
          #("ACCEL_Z", "ACCELEROMETER"),
          #("ACCEL_X", "ACCELEROMETER"),
          ("CRUISE_ACTIVE", "PCM_CRUISE"),
          ("ACCEL_NET", "PCM_CRUISE"),
          ("BRAKE_PRESSED", "BRAKE_MODULE"),
          #("GAS_PEDAL", "GAS_PEDAL"),
          #("ACCEL_CMD", "ACC_CONTROL")
          
          ]
        
        
        # self.signals = [
        #   ("WHEEL_SPEED_FL","WHEEL_SPEEDS")
        #   ]
        
        checks= []
        for s in self.signals:
            checks.append((s[1], self.check_num))
            
        checks= list(set(checks))
            
        self.cp = CANParser(dbc_f, checks, 0)
        self.can_sock = messaging.sub_sock('can', timeout=200)
        
    def update(self):
        can_strs = messaging.drain_sock_raw(self.can_sock, wait_for_one=True)
        can_list= can_capnp_to_list(can_strs)
        
        self.cp.update_strings(can_list)
        
        # print(self.cp.vl)
        
        out_dict= {}
        for s in self.signals:
            out_dict.update({s[0] : self.cp.vl[s[1]][s[0]]})
        
        return out_dict

if __name__ == '__main__':
    logger= logmanager.Logger("Can Read only", path= 'can_logs')
    cp = CP()
    frame=0
    try:
        while 1:
            cd_log= [('can', cp.update())]
            logger.update(frame, cd_log)
            
            frame += 1
            time.sleep(0.02)
    finally:
        inp= input("\n Save log? Enter run description for YES, or type 'n' for NO \n")
        if inp != 'n':
            logger.save_output(inp)