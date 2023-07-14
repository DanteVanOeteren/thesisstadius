#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 17:35:29 2023

@author: koen
"""
import sounddevice as sd
import numpy as np
import soundfile as sf

# AUDIO SETUP
#Setting up the audio input output channels
    
# see all the available audio devices
snd_dev = sd.query_devices()
#set corrresponding input and output devices
sd.default.device =13
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

fmix = [8000]
yout = np.cos(2*np.pi*fmix[0]*taudio)
play = sd.play(0.5*yout, fs, blocking=True)
