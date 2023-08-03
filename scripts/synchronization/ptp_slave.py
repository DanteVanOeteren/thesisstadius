import socket
import sys
from datetime import datetime
import time

server_socket = None
ADDRESS = "192.168.61.242"
PORT = 2468

"""Play a sine signal."""
import time
import numpy as np
import sounddevice as sd

device = None
frequency = 14000
amplitude = 0.5
start_idx = 0
samplerate = sd.query_devices(device, 'output')['default_samplerate']
sd.default.latency = 'high'

def callback(outdata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    global start_idx
    t = (start_idx + np.arange(frames)) / samplerate
    t = t.reshape(-1, 1)
    outdata[:] = amplitude * np.sin(2 * np.pi * frequency * t)
    start_idx += frames

test = sd.OutputStream(device=device, channels=1, callback=callback,
                     samplerate=samplerate)

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
        print("\nReady to receive requests on port " + str(PORT) + " ...")
        while True:
            data, addr = server_socket.recvfrom(4096)
            data = data.decode("utf8")
            
            if("sync" == data):
                print("Syncing time with " + addr[0] + " ...")
                server_socket.sendto("ready".encode('utf8'), addr)
                num_of_times, addr = server_socket.recvfrom(4096)
                num_of_times = int(num_of_times)
                server_socket.sendto("ready".encode('utf8'), addr)
                for i in range(int(num_of_times)):
                    sync_clock()
            
            elif("stream" == data):
                test = sd.OutputStream(device=device, channels=1, callback=callback,
                                     samplerate=samplerate)

            elif("audio" == data):
                data, addr = server_socket.recvfrom(4096)
                data = data.decode("utf8")
                data = float(data)
                time_to_wait =  data - time.time()
                accurate_delay(time_to_wait)
                synced_time = time.time()
                with test:
                    time.sleep(1)
                    
                print("Synced time: ",synced_time)
                print("Stream latency: ", test.latency)
                print("Done!")
                print("")
                #print("Play audio here")
            else:
                server_socket.sendto(
                    "Hello World!".encode('utf8'), addr)
    except socket.error as e:
        print("Error while handling requests: " + str(e))
        server_socket.close()
        sys.exit(-1)

def accurate_delay(delay):
    ''' Function to provide accurate time delay in seconds
    '''
    _ = (time.perf_counter() + delay)
    while time.perf_counter() < _:
        pass

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