import socket
import sys
from datetime import datetime
import time

server_socket = None
ADDRESS = "192.168.74.242"
PORT = 2468


import sounddevice as sd
import numpy as np
import soundfile as sf


# AUDIO SETUP
#Setting up the audio input output channels
    
# see all the available audio devices
snd_dev = sd.query_devices()
#set corrresponding input and output devices
sd.default.device =18
print(snd_dev)
print(sd.default.device)

sd.default.samplerate = 44100
fs = sd.default.samplerate = 44100
dt = 1/fs
T = 2
N = T*fs
taudio = np.arange(0,T,dt)
ww = np.hanning(N)
fo = 4000
# yout = np.cos(2*np.pi*fo*taudio)

fmix = [3000]
yout = np.cos(2*np.pi*fmix[0]*taudio)

def main():
    global server_socket
    try:
        print("Creating socket ...")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error as e:
        print("Error creating socket: " + str(e) + ". Exitting ...")
        server_socket.close()
        sys.exit(-1)

    try:
        print("Binding to socket ... " + str(ADDRESS) + ":" + str(PORT))
        server_socket.bind((ADDRESS, PORT))
    except socket.error as e:
        print("Error binding to socket: " + str(e) + ". Exitting ...")
        server_socket.close()
        sys.exit(-1)

    try:
        while True:
            print("\nReady to receive requests on port " + str(PORT) + " ...")
            data, addr = server_socket.recvfrom(4096)
            data = data.decode("utf8")
            print("Request from " + addr[0])
            if("sync" == data):
                server_socket.sendto("ready".encode('utf8'), addr)
                num_of_times, addr = server_socket.recvfrom(4096)
                num_of_times = int(num_of_times)
                server_socket.sendto("ready".encode('utf8'), addr)
                for i in range(int(num_of_times)):
                    sync_clock()
                """
                print(get_time())
                t1 = time.perf_counter_ns()
                while((time.perf_counter_ns() - t1)/1_000_000 < 500):
                    continue
                print("Synced time: ", get_time())
                print("Done!")
                """
                time.sleep(0.2)
                print("Synced time: ", get_time())
            elif("audio" == data):
                play = sd.play(0.5*yout, fs, blocking=True)
                #print("Play audio here")
            else:
                server_socket.sendto(
                    "Hello World!".encode('utf8'), addr)
    except socket.error as e:
        print("Error while handling requests: " + str(e))
        server_socket.close()
        sys.exit(-1)


def sync_clock():
    addr = sync_packet()
    delay_packet(addr)
    recv()


def sync_packet():
    t2, (t1, addr) = recv()
    send(str(t2), addr)
    return addr


def delay_packet(addr):
    recv()
    send(str(get_time()), addr)


def recv():
    try:
        request = server_socket.recvfrom(4096)
        t = get_time()
        # print "Request from " + str(request[1][0])
        return (t, request)
    except socket.error as e:
        print("Error while receiving request: " + str(e))
        server_socket.close()
        sys.exit(-1)


def send(data, addr):
    try:
        server_socket.sendto(data.encode('utf8'), addr)
        # print "Sent to " + addr[0]
    except socket.error as e:
        print("Error while sending request: " + str(e))
        print("Tried to send: " + data)
        server_socket.close()
        sys.exit(-1)


def get_time():
    return time.time()


if __name__ == '__main__':
    main()
