import socket, time
import numpy as np
import struct
import sys
import select

def main(args):
	
    UDP_IP = "192.168.1.84"
    UDP_PORT = 6667
    sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_recv.bind((UDP_IP, UDP_PORT))
    sock_recv.setblocking(False)
    #TARGET_IP = "192.168.43.92"  # comma tethering
    TARGET_IP = "192.168.1.79"  # wifi
    TARGET_PORT = 6667
    sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ticks = 0
    timeout = 0.1
    missing = 0
    comm_flag = False
    default_speed = 5

    while True:
        try:
            readable, _, _ = select.select([sock_recv], [], [], timeout)
            if readable:
                missing = 0
                comm_flag = True
                data, addr = sock_recv.recvfrom(1024)
                #print(data, addr)
                received_speed, received_accel, received_jerk = struct.unpack('>fff', data)
                print(f"Received speed info: {received_speed}, accel info: {received_accel}, and jerk info: {received_jerk} from {addr}")
            else:
                print("Not receiving")
                missing += 1
            if missing >=20:
                comm_flag = False

            speed = 10 + np.sin(0.1*ticks+0.02)
            packed_message = struct.pack('>f', speed)
            sock_send.sendto(packed_message, (TARGET_IP, TARGET_PORT))
            print(f"Send speed: {speed}")
            print(f"Missing ticks: {missing}; ", "comm_flag: ", comm_flag)
        except BlockingIOError:
            print(f"Not receiving, using default speed: {default_speed}")
            comm_flag = False
        except KeyboardInterrupt:
            break
            print("\nTransmission interrupted by user.")
        ticks += 1
        #time.sleep(0.1)
        
    sock_recv.close()
    sock_send.close()
	
if __name__ == "__main__":
    main(sys.argv[1:])