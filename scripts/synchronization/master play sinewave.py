import sounddevice as sd
import numpy as np
import soundfile as sf
import time

# AUDIO SETUP
#Setting up the audio input output channels
    
# see all the available audio devices
snd_dev = sd.query_devices()
#set corrresponding input and output devices
sd.default.device =  1
print(snd_dev)
print(sd.default.device)

# Set channel maps for input and output 
outputChannelMap = [1,2]

# Set number of channels for input and number for output
# sd.default.channels = [len(inputChannelMap),len(outputChannelMap)]

#set the sampleratee
sd.default.samplerate = 44100

#%
# # Generate the output signal for sinusoids
fs = sd.default.samplerate = 44100
dt = 1/fs
T = 1
N = T*fs
taudio = np.arange(0,T,dt)
ww = np.hanning(N)
fo = 4000
# yout = np.cos(2*np.pi*fo*taudio)

fmix = [500, 2000]
yout = np.cos(2*np.pi*fmix[0]*taudio) + np.cos(2*np.pi*fmix[1]*taudio)
t1 = time.perf_counter_ns()
play = sd.play(0.2*yout, fs, mapping=outputChannelMap, blocking=True)
t2 = time.perf_counter_ns()
print((t1-t2)/1_000_000)