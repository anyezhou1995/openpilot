import socket
import numpy as np
import struct
import sys

def main(args):
	UDP_IP = "0.0.0.0"  # Change this to the receiver IP address
	UDP_PORT = 6666  # Change this to the receiver port

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT))
	
	while True:
		try:
			data, addr = sock.recvfrom(1024)
			received_message = struct.unpack('>f', data)[0]
			print(f"Received speed info: {received_message} as float from {addr}")
		except KeyboardInterrupt:
			break
			print("\nTransmission interrupted by user.")
		
	sock.close()
	
if __name__ == "__main__":
    main(sys.argv[1:])