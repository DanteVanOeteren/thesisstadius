import socket
import sys
from datetime import datetime
import time

server_socket = None
ADDRESS = "192.168.74.242"
PORT = 2468
NUM_OF_TIMES = 100

OFFSETS = []
DELAYS = []

import soundfile as sf

#!/usr/bin/env python3
"""Play a sine signal."""
import numpy as np
import sounddevice as sd
import time

device = 2
frequency = 3000
amplitude = 0.5
start_idx = 0
sd.default.latency = 'low'
sd.default.device = device
outputChannelMap = [1,2]
samplerate = sd.query_devices(device, 'output')['default_samplerate']

def callback(outdata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    global start_idx
    t = (start_idx + np.arange(frames)) / samplerate
    t = t.reshape(-1, 1)
    outdata[:] = amplitude * np.sin(2 * np.pi * frequency * t)
    start_idx += frames

test = sd.OutputStream(device=device, channels=2, callback=callback,
                     samplerate=samplerate)

def main():
    try:
        global server_socket
        print("Creating socket ...")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error as e:
        print("Error creating socket: " + str(e) + ". Exitting ...")
        server_socket.close()
        sys.exit(-1)

    try:
        print("Connecting to socket ... " + str(ADDRESS) + ":" + str(PORT))
        server_socket.connect((ADDRESS, PORT))
    except socket.error as e:
        print("Error connecting to socket: " + e + ". Exitting ...")
        server_socket.close()
        sys.exit(-1)

    sync_clock()


def sync_clock():
    print("\nSyncing time with " + ADDRESS + ":" + str(PORT) + " ...")
    send("sync")
    t, resp = recv()
    send(str(NUM_OF_TIMES))

    t, resp = recv()

    if(resp == "ready"):
        time.sleep(1)  # to allow for server to get ready
        for i in range(NUM_OF_TIMES):
            ms_diff = sync_packet()
            sm_diff = delay_packet()

            offset = (ms_diff - sm_diff)/2
            delay = (ms_diff + sm_diff)/2

            OFFSETS.append(offset)
            DELAYS.append(delay)
            
            send("next")
                    
        
        offset_final = sum(OFFSETS) / len(OFFSETS)
        delay_final = sum(DELAYS) / len(DELAYS)
        print('Final offset: ', offset_final)
        print('Final delay: ', delay_final)

        send('stream')
        time.sleep(1) # to allow for client to load the outputstream
        
        send('audio')
        
        delay = 1 # both computers agree to start at time.time() + delay based on this computer's clock
        
        time_to_start = time.time() + delay
        send(str(time_to_start + offset_final))
        
        time_to_wait = time_to_start - time.time()
        accurate_delay(time_to_wait)
        synced_time = time.time() + offset_final
        with test:
            time.sleep(1)
        print('Synced time: ', synced_time)
        print('Stream latency: ', test.latency)
        '''
        ONEBILLION = 1000000000
        print("\n\nAVG OFFSET: %sns" % str(sum(OFFSETS) * ONEBILLION / len(OFFSETS) \
                                           ) + "\nAVG DELAY: %sns" % str(sum(DELAYS) * ONEBILLION / len(DELAYS)))
        print("\n\nMIN OFFSET: %sns" % str(min(OFFSETS) * ONEBILLION) +
              "\nMIN DELAY: %sns" % str(min(DELAYS) * ONEBILLION))
        print("\n\nMAX OFFSET: %sns" % str(max(OFFSETS) * ONEBILLION) +
              "\nMAX DELAY: %sns" % str(max(DELAYS) * ONEBILLION))
        print("\nDone!")
        '''
    else:
        print("Error syncing times, received: " + resp.decode("utf8"))

def accurate_delay(delay):
    _ = time.perf_counter() + delay
    while time.perf_counter() < _:
        pass

def sync_packet():
    t1 = send("sync_packet")
    t, t2 = recv()
    return float(t2) - float(t1)


def delay_packet():
    send("delay_packet")
    t4, t3 = recv()
    return float(t4) - float(t3)


def recv():
    try:
        msg = server_socket.recv(4096)
        t = get_time()
        return (t, msg.decode("utf8"))
    except socket.error as e:
        print("Error while receiving request: " + str(e))
        server_socket.close()
        sys.exit(-1)


def send(data):
    try:
        server_socket.sendall(data.encode('utf8'))
        t = get_time()
        return t
        # print "Sent:" + str(data)
    except socket.error as e:
        print("Error while sending request: " + str(e))
        print("Tried to send: " + data)
        server_socket.close()
        sys.exit(-1)


def get_time():
    return time.time()


if __name__ == '__main__':
    main()