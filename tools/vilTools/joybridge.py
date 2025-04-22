#!/usr/bin/env python
import os
import csv

import cereal.messaging as messaging
from common.numpy_fast import clip
from common.params import Params
from tools.lib.kbhit import KBHit

import threading
import select
import sys
import struct

from selfdrive.test.helpers import set_params_enabled
from common.realtime import DT_DMON, Ratekeeper

import time
import csv

import copy
import numpy as np

from logmanager import Logger
# import can_parser
from collections import deque

import socket

def read_write_udp(vs, exit_event):

    def read_udp(s):
        out= None
        t= time.time()
        while 1:
            try:
                data, addr = s.recvfrom(1024)
                out= data
            except socket.timeout:
                return out

            if time.time() - t > 0.1:
                return out

    def send_udp(s, f):
        message= struct.pack('>f', f)
        sock.sendto(message, ('192.168.0.16', SEND_PORT))

    # Configuration
    RECEIVER_IP = '0.0.0.0'
    RECEIVER_PORT = 6666
    SEND_PORT = 11007

    # Create REC UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.05)
    sock.bind((RECEIVER_IP, RECEIVER_PORT))

    # Create Send UDP socket
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2.settimeout(0.1)

    print(f"Listening on {RECEIVER_IP}:{RECEIVER_PORT}")

    while not exit_event.is_set():
        # Receive data
        data= read_udp(sock)

        if data is not None:
            # Decode and convert the received data to float
            # signal = float(data.decode('utf-8'))
            signal = struct.unpack('>f', data)[0]
            print(signal)

            vs.pid_setspeed = signal

        send_udp(sock2, vs.speed)

        time.sleep(0.02)
    sock.close()

class PIDController:
    def __init__(self, kp, ki, kd, setpoint, max_samples=50):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.max_samples = max_samples
        self.error_samples = deque(maxlen=max_samples)
        self.out_samples= deque(maxlen=max_samples)

        self.feedforward= 0
        self.last_error = 0
        self.sample_count = 0
        self.mult= 0.001

        self.epsilon= 0.05
        self.esum= 0


    def compute(self, process_variable):
        error = self.setpoint - process_variable

        # if abs(error) < self.epsilon:
        #     error=0


        # Update integral term
        abserr= abs(error)
        if abserr < 0.5:
            if abserr < self.epsilon:
                self.error_samples.append(0)
            else:
                self.error_samples.append(error)


        # if abs(error) < self.epsilon:
        #     self.error_samples.append(0)
        # if abs(error) < self.epsilon:
        #     self.error_samples.append(0)
            # self.esum += error
        error_mean= (sum(self.error_samples) / self.max_samples)


        # Calculate error difference for derivative term
        error_diff = error - self.last_error if self.sample_count > 0 else 0

        p_term = self.kp * error
        i_term = self.ki * error_mean
        d_term = self.kd * error_diff

        pid = p_term + i_term + d_term

        # if abs(error) < 1:
        #     self.mult += 0.0001 * error_mean
        #     print(self.mult)

        self.feedforward = self.mult * self.setpoint

        output= self.feedforward + pid

        # print(output)


        # print(self.mult)

        self.last_error = error
        self.sample_count += 1

        self.out_samples.append(output)

        # self.feedforward= sum(self.out_samples) / len(self.out_samples)

        return output

    def set_tunings(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd

    def set_setpoint(self, setpoint):
        self.setpoint = setpoint

    def reset(self):
        self.error_samples = deque(maxlen=self.max_samples)
        self.out_samples= deque(maxlen=self.max_samples)

        self.feedforward= 0
        self.last_error = 0
        self.sample_count = 0



class ControlState:
    def __init__(self):
        self.throttle_brake= 0
        self.speed= 0
        self.pid_setspeed= 0
        self.cruise_set= False

def keyboard_control(cs, exit_event):
    while not exit_event.is_set():
        i, o, e = select.select( [sys.stdin], [], [], 1 )
        if i:
            cmd= sys.stdin.readline().strip()
        else:
            cmd= ''

        if cmd == '0':
            cs.pid_setspeed += -1

        if cmd == '1':
            cs.pid_setspeed += 1

        time.sleep(0.2)


def vs_log(sub, control_state, explog, exit_event, update_log= False):
    rk2 = Ratekeeper(20, print_delay_threshold=None)

    # cr= can_parser.CP()
    # chan= ['carState', 'carControl', 'modelV2', 'controlsState', 'radarState',
    #                           'longitudinalPlan', 'lateralPlan', 'liveLocationKalman',
    #                           'managerState', 'liveParameters', 'liveCalibration']

    cruise_started= False
    while not exit_event.is_set():

        sub.update(0)
        cs= sub['carState']
        # can_data= cr.update()

        control_state.speed= round(cs.vEgo, 2)
        control_state.cruise_set= int(cs.cruiseState.enabled) == 1

        print(f"Speed Reading from Vehicle: {round(2.23694 * control_state.speed, 2)} mph")
        print(f"PID Set Speed {round(2.23694 * control_state.pid_setspeed, 2)} mph")
        print(f"ACC Enabled: {control_state.cruise_set}")
        print("__________")

        if cs.vEgo > 0.01 and update_log:
            cruise_started= True

            log_data= [('kin', {'v' : cs.vEgo, 'steering' : cs.steeringAngleDeg,
                                'setSpeed' : control_state.pid_setspeed})]
            # log_data.append(('can', can_data))
            log_data.append(('control', {'accel' : sub['carControl'].actuators.accel, 'steerDeg' : sub['carControl'].actuators.steeringAngleDeg,
                                         'steer' : sub['carControl'].actuators.steer}))

            log_data.append(('pid', {'setSpeed' : control_state.pid_setspeed, 'cmdAccel' : control_state.throttle_brake}))


            explog.update(rk2.frame, log_data)

        # if cruise_started:
        #     can_data= cr.update()
        #     if int(can_data['CRUISE_ACTIVE']) == 0:
        #         exit_event.set()

        rk2.keep_time()

def pid_compute(pm, control_state, pid, exit_event):
    Params().put_bool('JoystickDebugMode', True)

    rk = Ratekeeper(20, print_delay_threshold=None)

    throtset= 0
    cruise_init_set= False
    while not exit_event.is_set():
        if control_state.cruise_set:
            cruise_init_set= True
            # print(control_state.pid_setspeed)
            # pid.set_setpoint(control_state.pid_setspeed * 0.44704)
            pid.set_setpoint(control_state.pid_setspeed)
            throtset= pid.compute(control_state.speed)

            # print(str(control_state.speed) + '\n', control_state.pid_setspeed)

            # throtset += 0.01 * throtaccel
            throtset= float(np.clip(throtset, -1, 1)) / 4

            # throtset= -0.2

            dat = messaging.new_message('testJoystick')
            dat.valid = True
            dat.testJoystick.axes = [throtset,0]
            dat.testJoystick.buttons = [False]
            pm.send('testJoystick', dat)


            control_state.throttle_brake= throtset

        if not control_state.cruise_set and cruise_init_set:
            cruise_init_set= False
            pid.reset()

        rk.keep_time()

if __name__ == '__main__':

    os.environ["PYOPENCL_CTX"] = '0'

    # make sure params are in a good state
    set_params_enabled()

    pm = messaging.PubMaster(['testJoystick'])
    sm= messaging.SubMaster(['carState', 'carControl', 'radarState', 'modelV2'])


    # Params().put_bool('DisableRadar', True)

    #Carla calibration
    # calib_1= b'\x00\x00\x00\x00\x16\x00\x00\x00\x00\x00\x00\x00\x02\x00\x01\x00\xde\x98\xc5\xb7\xccu\x00\x00\x12\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x06\x00\x01d\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x11\x00\x00\x00d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1d\x00\x00\x00\x1c\x00\x00\x00!\x00\x00\x00\x1c\x00\x00\x00\xa0\x94\x97\xba\xf5\xff\x7f\xbf[\x08\x08\xb4\x00\x00\x00\x00\xd7\xbd\xe58\x00\x00\x00\x00\x00\x00\x80\xbf\xf6(\x9c?\xf5\xff\x7f?\xa0\x94\x97\xba\xcd\xbd\xe58\x00\x00\x00\x00\x1b\xc3\xbc3\xd7\xbd\xe5\xb8\xa2\x94\x97\xba\x00\x00\x00\x00\xbd\x05\xf049\x8f\xc1:\xdd\xe8D;\x00\x00\x00\x00'
    # Params().put("CalibrationParams", calib_1)

    exit_event = threading.Event()
    control_state= ControlState()
    explog= Logger("VIL Speed Control", path= 'logs')

    pid= PIDController(1.5, 1.7 ,0, control_state.pid_setspeed)

    threads= []
    threads.append(threading.Thread(target=keyboard_control, args=(control_state, exit_event)))
    threads.append(threading.Thread(target=read_write_udp, args=(control_state, exit_event)))
    threads.append(threading.Thread(target=vs_log, args=(sm, control_state, explog, exit_event)))
    # threads.append(threading.Thread(target=pid_compute, args=(pm, control_state, pid, exit_event)))

    for t in threads:
        t.start()

    try:
        while 1:
            time.sleep(0.1)
    finally:
        exit_event.set()
        for t in reversed(threads):
            t.join()

        # inp= input("\n Save log? Enter run description for YES, or type 'n' for NO \n")
        inp= 'n'

        if inp != 'n':
            pass
            explog.save_output(inp)

        print("Succesful shutdown")







