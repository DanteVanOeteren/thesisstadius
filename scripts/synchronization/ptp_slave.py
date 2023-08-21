import socket
import sys
from datetime import datetime
import time

server_socket = None
ADDRESS = "192.168.0.117"
PORT = 2468

"""Play a sine signal"""
import time
import numpy as np
import sounddevice as sd

output_device = 11
frequency = 2000
amplitude = 0.5
start_idx = 0
samplerate = sd.query_devices(output_device, 'output')['default_samplerate']
sd.default.latency = 'high'

def sine_callback(outdata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    global start_idx
    t = (start_idx + np.arange(frames)) / samplerate
    t = t.reshape(-1, 1)
    outdata[:] = amplitude * np.sin(2 * np.pi * frequency * t)
    start_idx += frames

sine_stream = sd.OutputStream(device=output_device, channels=1, callback=sine_callback,
                     samplerate=samplerate)



"""Play audio"""
import threading
import soundfile as sf

PLAYBACK_TIME = 5

playback_filename = "JID.mp3"
playback_device = 11
event = threading.Event()
playback_data, fs = sf.read(playback_filename, always_2d=True)
current_frame = 0

def playback_callback(outdata, frames, time, status):
    global current_frame
    if status:
        print(status)
    chunksize = min(len(playback_data) - current_frame, frames)
    outdata[:chunksize] = playback_data[current_frame:current_frame + chunksize]
    if chunksize < frames:
        outdata[chunksize:] = 0
        raise sd.CallbackStop()
    current_frame += chunksize
    
def playback_audio(audio):
    with audio:
        accurate_delay(PLAYBACK_TIME)
        

audio_stream = sd.OutputStream(
    samplerate=fs, device=playback_device, channels=playback_data.shape[1],
    callback=playback_callback, finished_callback=event.set)


"""Recording setup"""
import queue
recording_filename = "shit3.wav" #output filename
recording_device = 11 #input deivce
recording_samplerate = None
recording_channels = 2
subtype = "PCM_24"

RECORDING_TIME = PLAYBACK_TIME + 5

q = queue.Queue()

if recording_samplerate is None:
    device_info = sd.query_devices(recording_device, 'input')
    # soundfile expects an int, sounddevice provides a float:
    recording_samplerate = int(device_info['default_samplerate'])
    
def recording_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())
    
def start_recording():
    now = time.time()
    with sf.SoundFile(recording_filename, mode='x', samplerate=recording_samplerate,
                      channels=recording_channels, subtype=subtype) as file:
        with sd.InputStream(samplerate=recording_samplerate, device=recording_device,
                            channels=recording_channels, callback=recording_callback):
            print("Started recording...")
            while ((time.time() - now) < RECORDING_TIME ):
                file.write(q.get())

time_of_recording = None


""" MAIN LOOP """
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
                sine_stream = sd.OutputStream(device=output_device, channels=1, callback=sine_callback,
                                     samplerate=samplerate)
                audio_stream = sd.OutputStream(
                    samplerate=fs, device=playback_device, channels=playback_data.shape[1],
                    callback=playback_callback, finished_callback=event.set)
                print("Syncing time with " + addr[0] + " ...")
                server_socket.sendto("ready".encode('utf8'), addr)
                num_of_times, addr = server_socket.recvfrom(4096)
                num_of_times = int(num_of_times)
                server_socket.sendto("ready".encode('utf8'), addr)
                
                for i in range(int(num_of_times)):
                    sync_clock()
            
            elif("check_connection" == data):
                server_socket.sendto("ready".encode('utf8'), addr)
            
            elif("start_recording" == data):
                #Start recording here
                time_of_recording = time.time()
                t1 = threading.Thread(target=start_recording)
                t1.start()
                
            elif("synced_execute" == data):
                data, addr = server_socket.recvfrom(4096)
                data = data.decode("utf8")
                data = float(data)
                time_to_wait =  data - time.time()
                accurate_delay(time_to_wait)
                synced_time = time.time()
                
                #sine wave is played for one second (actually played for 1s - sine_stream.latency)
                with sine_stream:
                    accurate_delay(1)

                #we wait one second
                accurate_delay(1)
                
                #now we start playing the audio
                with audio_stream:
                    time_of_audio = time.time()
                    accurate_delay(PLAYBACK_TIME)
                    
                print("Synced time: ",synced_time)
                print("Time of audio: ",time_of_audio)
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