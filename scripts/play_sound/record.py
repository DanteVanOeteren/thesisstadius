import argparse
import tempfile
import queue
import sys
import time

import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)

filename = "shit2.wav" #output filename
device = 11 #input deivce
samplerate = None
channels = 1
subtype = "PCM_24"

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())

if samplerate is None:
    device_info = sd.query_devices(device, 'input')
    # soundfile expects an int, sounddevice provides a float:
    samplerate = int(device_info['default_samplerate'])
if filename is None:
    filename = tempfile.mktemp(prefix='delme_rec_unlimited_',
                                    suffix='.wav', dir='')

# Make sure the file is opened before recording anything:
now = time.time()
with sf.SoundFile(filename, mode='x', samplerate=samplerate,
                  channels=channels, subtype=subtype) as file:
    with sd.InputStream(samplerate=samplerate, device=device,
                        channels=channels, callback=callback):
        print('#' * 80)
        print('press Ctrl+C to stop the recording')
        print('#' * 80)
        while ((time.time() - now) < 5 ):
            file.write(q.get())
