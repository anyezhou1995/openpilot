import socket
import numpy as np
import time
import struct
import sys

def main(args):
	UDP_IP = "192.168.1.84"  # Change this to the receiver IP address
	UDP_PORT = 6666  # Change this to the receiver port

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	
	i = 0
	while True:
		try:
			sineWave = 10 + 5*np.sin(i)
			packed_message = struct.pack('>f', sineWave)
			sock.sendto(packed_message, (UDP_IP, UDP_PORT))
			print('Advisory speed: ', sineWave, ' MPH')
			i += 1
			time.sleep(0.1)
		except KeyboardInterrupt:
			break
			print("\nTransmission interrupted by user.")
		
	sock.close()
	
if __name__ == "__main__":
    main(sys.argv[1:])