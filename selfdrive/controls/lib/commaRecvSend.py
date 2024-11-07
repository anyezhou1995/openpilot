import socket
import numpy as np
import struct
import sys

def main(args):
	
    UDP_IP = "0.0.0.0"
    UDP_PORT = 6666
    sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_recv.bind((UDP_IP, UDP_PORT))
    TARGET_IP = "192.168.43.92"
    TARGET_PORT = 1006
    sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ticks = 0

    while True:
        try:
            readable, _, _ = select.select([sock_recv], [], [], timeout)
            if readable:
                missing = 0
                comm_flag = True
                data, addr = sock_recv.recvfrom(1024)
                #print(data, addr)
                received_speed, received_accel, received_jerk = struct.unpack('>fff', data)
                print(f"Received speed info: {received_num1}, accel info: {received_num2}, and jerk info: {received_num3} from {addr}")
            else:
                #print(f"Not receiving, using default speed: {default_speed}")
                missing += 1
            if missing >=20:
                comm_flag = False

            speed = 10 + np.sin(ticks+0.2)
            packed_message = struct.pack('>f', speed)
            sock_send.sendto(packed_message, (TARGET_IP, TARGET_PORT))
            print(f"Send speed: {speed}")
            print("Waiting...")
        except BlockingIOError:
            #print(f"Not receiving, using default speed: {default_speed}")
            comm_flag = False
        except KeyboardInterrupt:
            break
            print("\nTransmission interrupted by user.")
        ticks += 1
        
    sock_recv.close()
    scok_send.close()
	
if __name__ == "__main__":
    main(sys.argv[1:])