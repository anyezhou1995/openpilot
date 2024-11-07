#!/usr/bin/env python3
from cereal import car
from openpilot.common.params import Params
from openpilot.common.realtime import Priority, config_realtime_process
from openpilot.common.swaglog import cloudlog
from openpilot.selfdrive.controls.lib.ldw import LaneDepartureWarning
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
import cereal.messaging as messaging

import socket, select, struct
import numpy as np


def main():
  config_realtime_process(5, Priority.CTRL_LOW)

  cloudlog.info("plannerd is waiting for CarParams")
  params = Params()
  CP = messaging.log_from_bytes(params.get("CarParams", block=True), car.CarParams)
  cloudlog.info("plannerd got CarParams: %s", CP.carName)

  ldw = LaneDepartureWarning()

  comm_flag = False
  UDP_IP = "0.0.0.0"
  UDP_PORT = 6667
  sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock_recv.bind((UDP_IP, UDP_PORT))
  TARGET_IP = "192.168.0.151"
  TARGET_PORT = 6665
  sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  timeout = 0.05
  missing = 0
  extMsg = np.array([5, 0, 0])

  longitudinal_planner = LongitudinalPlanner(CP)
  pm = messaging.PubMaster(['longitudinalPlan', 'driverAssistance'])
  sm = messaging.SubMaster(['carControl', 'carState', 'controlsState', 'liveParameters', 'radarState', 'modelV2', 'selfdriveState'],
                           poll='modelV2', ignore_avg_freq=['radarState'])

  while True:
    sm.update()
    try:
      readable, _, _ = select.select([sock_recv], [], [], timeout)
      if readable:
        missing = 0
        comm_flag = True
        data, addr = sock_recv.recvfrom(1024)
        #print(data, addr)
        received_speed, received_accel, received_jerk = struct.unpack('>fff', data)
        #print(f"Received speed info: {received_num1}, accel info: {received_num2}, and jerk info: {received_num3} from {addr}")
        extMsg = np.array([received_speed, received_accel, received_jerk])
      else:
        #print(f"Not receiving, using default speed: {default_speed}")
        missing += 1
      if missing >=20:
        comm_flag = False

      CS = sm['carState']
      speed = CS.vEgo
      packed_message = struct.pack('>f', speed)
      sock_send.sendto(packed_message, (TARGET_IP, TARGET_PORT))
      #print(f"Send speed: {speed}")
      #print("Waiting...")
    except BlockingIOError:
      #print(f"Not receiving, using default speed: {default_speed}")
      comm_flag = False

    if sm.updated['modelV2']:
      if comm_flag:
        longitudinal_planner.update(sm, comm_flag, extMsg)
      else:
        longitudinal_planner.update(sm, comm_flag, [])
      longitudinal_planner.publish(sm, pm)

      ldw.update(sm.frame, sm['modelV2'], sm['carState'], sm['carControl'])
      msg = messaging.new_message('driverAssistance')
      msg.valid = sm.all_checks(['carState', 'carControl', 'modelV2', 'liveParameters'])
      msg.driverAssistance.leftLaneDeparture = ldw.left
      msg.driverAssistance.rightLaneDeparture = ldw.right
      pm.send('driverAssistance', msg)

  sock_recv.close()
  sock_send.close()


if __name__ == "__main__":
  main()
