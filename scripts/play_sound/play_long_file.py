import queue
import sys
import threading

import sounddevice as sd
import soundfile as sf

#arguments
filename = "JID - Kody Blu 31.mp3"
device = None
blocksize = 2048
buffersize = 20

q = queue.Queue(maxsize=buffersize)
event = threading.Event()

def callback(outdata, frames, time, status):
    assert frames == blocksize
    if status.output_underflow:
        print('Output underflow: increase blocksize?', file=sys.stderr)
        raise sd.CallbackAbort
    assert not status
    try:
        data = q.get_nowait()
    except queue.Empty:
        print('Buffer is empty: increase buffersize?', file=sys.stderr)
        raise sd.CallbackAbort
    if len(data) < len(outdata):
        outdata[:len(data)] = data
        outdata[len(data):] = b'\x00' * (len(outdata) - len(data))
        raise sd.CallbackStop
    else:
        outdata[:] = data


import time
t1 = (time.perf_counter_ns())
with sf.SoundFile(filename) as f:
    for _ in range(buffersize):
        data = f.buffer_read(blocksize, dtype='float32')
        if not data:
            break
        q.put_nowait(data)  # Pre-fill queue
    stream = sd.RawOutputStream(
        samplerate=f.samplerate, blocksize=blocksize,
        device=device, channels=f.channels, dtype='float32',
        callback=callback, finished_callback=event.set)
    with stream:
        print((time.perf_counter_ns() - t1)/1000000)
        timeout = blocksize * buffersize / f.samplerate
        while data:
            data = f.buffer_read(blocksize, dtype='float32')
            q.put(data, timeout=timeout)
        event.wait()
