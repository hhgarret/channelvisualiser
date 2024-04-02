import socket, time, sys
import matplotlib.pyplot as plt
import numpy as np
import math
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import CheckButtons
from tkinter import *
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.gridspec as gridspec
import termios
import matplotlib.ticker as ticker
import asyncio
import argparse
import os
import struct

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--binary", help="Binary Flag", default=False, action='store_true')
args = parser.parse_args()
binaryFlag = args.binary
#print("Binary {}".format(binaryFlag))

#Some initial variable declarations. 
starttime = time.time();
decimationfactor = 10
decimationcount = 0
count = 0
totallength = int(48000 / (2*decimationfactor))
appendlength = int(4800 / (decimationfactor))
maxchannels = 24
numchannels = 24
charts = np.zeros((24, totallength))
tempcharts = np.zeros((24, appendlength))
framecount = 0;
curchannels = [i for i in range(maxchannels)]
faucet = True
disabledaxes = []
disabledindex = []
disabledcount = 0
nyquist = 24000 #48k / 2
fftlength = .5 #.5 of a second
fftbinwidth = 1/fftlength #as fftlength decreases, binwidth increases

fftMode = False
curselected = 0
def changeselected(leftorright):
	global curselected, maxchannels
	if leftorright == "left":
		curselected = (curselected - 1)%maxchannels
	else:
		curselected = (curselected + 1)%maxchannels
	selection.delete("1.0", "1.100")
	selection.insert(INSERT, "Selected: "+str(curselected+1))
#the on_draw method is called whenever the on_draw event is triggered
def on_draw(event):
	a = 1
	#print('hello')
	#toggleFaucet(True)
	
#the on_click method is called whenever the on_click event is triggered
#Here, it checks to see if a plot was clicked, then determined which plot was clicked, and essentially minimizes that plot.


plots = []
fig, axes = plt.subplots(2,2) 
old_fig_size = fig.get_size_inches()
#gs = axes[0,0].get_gridspec()
xvals = range(totallength)
ylim = 0.05
flushflag = False
#init_fig initalizes fig and axes for any given enabled channels. Called once at the start, and also whenever a channel is disabled.
def init_fig():
	print('init_fig')
	global plots, totallength, fig, axes, xvals, ylim, numchannels, disabledindex, numchannels, canvas, window, maxchannels, fftMode, old_fig_size, decimationfactor, totallength, appendlength, charts, tempcharts, curselected
	decimationfactor = 10
	totallength = int(48000 / (2*decimationfactor))
	appendlength = int(4800 / (decimationfactor))
	charts = np.zeros((maxchannels, totallength))
	tempcharts = np.zeros((maxchannels, appendlength))
	plots = []
	xvals = range(totallength)
	width, height = (1, 1)
	plt.close()
	fig, axes = plt.subplots(nrows=height, ncols=width, squeeze=True, sharex=True,sharey=True)
	ylim = .05
	plt.connect('draw_event', on_draw)
	skipped = 0
	pltline, = axes.plot(charts[curselected], '.k', ms=".25", ls='', alpha=1, animated=True, zorder=10)
	plots = pltline
	axes.set_xlim(0, totallength)
	axes.set_ylim(-1*ylim, ylim)
	axes.draw_artist(pltline)
	axes.set_yticks([])
	axes.set_xticks([])
	axes.set_title((curselected+1), fontsize='small',loc='left')

	plt.tight_layout()
	canvas.get_tk_widget().pack_forget()
	canvas.get_tk_widget().destroy()
	canvas = FigureCanvasTkAgg(fig, master = window)
	canvas.draw()
	canvas.get_tk_widget().pack(fill='both',expand=True,side='top')
	old_fig_size = old_fig_size - [1,1]
	diff =  (height*width) - numchannels



window = Tk()
window.title("Harley's Data Viewer")
window.geometry("500x500")
canvas = FigureCanvasTkAgg(fig, master = window)
canvas.draw()
canvas.get_tk_widget().pack(fill='both',expand=True,side='top')


#resetfig reenables all disabled axes 
def resetfig():
	global axes, fig, disabledaxes, old_fig_size, disabledindex, numchannels, maxchannels, curchannels, fftMode
	if fftMode == False:
		toggleFaucet(False)
		disabledaxes = []
		disabledindex = []
		numchannels = maxchannels
		curchannels = [elem for elem in range(maxchannels)]
		print(curchannels, disabledaxes, disabledindex, numchannels)
		init_fig()
		old_fig_size = old_fig_size - [1,1]
		toggleFaucet(True)
#tkinter window/gui creation
masterFrame = Frame(master = window)
masterFrame.pack()


selectionFrame = Frame(master = masterFrame)
selectionFrame.pack()
selectleft = Button(master = selectionFrame, command = lambda:updatewidth("add"), height=2, width=10, text="<--")
selectleft.pack(side=LEFT, expand=1)
window.bind('<Right>', lambda event:changeselected("right"))
selection = Text(master = selectionFrame, height = 2, width=40)
selection.insert(INSERT, "Selected: "+str(curselected+1))
#selection.place(x=10, width=400)
selection.pack(side=LEFT, expand=1)
selectright = Button(master = selectionFrame, command = lambda:updatewidth("remove"), height=2, width=10, text="-->")
selectright.pack(side=LEFT, expand=1)
window.bind('<Left>', lambda event:changeselected("left"))

init_fig()
window.attributes('-zoomed', True)


#plt.pause(0.0000001)
plt.close()
bg = fig.canvas.copy_from_bbox(fig.bbox)
old_fig_size = fig.get_size_inches()
fig.canvas.blit(fig.bbox)

def read(n):
	buffer = b""
	while len(buffer) < n:
		#data = sys.stdin.buffer.read(n - len(buffer))
		data = os.read(0, n - len(buffer))
		buffer += data
	return buffer

def readflush():
	changelength = 1
	while changelength > 0:
		data = os.read(0, maxchannels*8)
		changelength = len(data)


if binaryFlag is False:
	tempmaxchannels = len(sys.stdin.readline().split("\t"))
	if(tempmaxchannels != maxchannels):
		maxchannels = tempmaxchannels
		numchannels = maxchannels
		charts = np.zeros((maxchannels, totallength))
		tempcharts = np.zeros((maxchannels, appendlength))
		curchannels = [i for i in range(maxchannels)]
		init_fig()
	#print(maxchannels)
elif binaryFlag is True:
	sys.stdin.read
	byte = read(1)
	#print(byte)
	#byte = sys.stdin.buffer.read()
	tempmaxchannels = struct.unpack('b', byte)[0]
	if(tempmaxchannels != maxchannels):
		maxchannels = tempmaxchannels
		numchannels = maxchannels
		charts = np.zeros((maxchannels, totallength))
		tempcharts = np.zeros((maxchannels, appendlength))
		curchannels = [i for i in range(maxchannels)]
		init_fig()
	print(maxchannels)


sleeptimer = 0
latencycount = 0
async def readin():
	global flushflag, faucet, decimationcount, decimationfactor, fig, axes, tempcharts, count, old_fig_size, bg, charts, plots, framecount, sleeptimer, latencyText, starttime, latencycount, fftMode, prevselected, fftbinwidth, nyquist, curselected
	for line in sys.stdin:
		if faucet is False:
			return
		if flushflag is True:
			starttime = time.time()
			framecount = 0
			flushflag = False
		if decimationcount < (decimationfactor-1):
			decimationcount += 1
		else:
			decimationcount = 0
			linesplit = line.split("\t")
			tempcharts[:, count] = np.asarray(linesplit, dtype=float)
			count += 1
		if (count - appendlength == 0):
			if(old_fig_size != fig.get_size_inches()).any():
		        	fig.canvas.flush_events()
		        	bg = fig.canvas.copy_from_bbox(fig.bbox)
		        	old_fig_size = fig.get_size_inches()
			fig.canvas.restore_region(bg)
			charts = np.concatenate((charts[:,appendlength:],tempcharts), axis=1)
			plots.set_data(xvals, charts[curselected])
			axes.draw_artist(plots)
			fig.canvas.blit(fig.bbox)
			fig.canvas.flush_events()
			count = 0
	print(time.time() - starttime)
	

async def readinbinary():
	global flushflag, faucet, decimationcount, decimationfactor, fig, axes, tempcharts, count, old_fig_size, bg, charts, plots, framecount, sleeptimer, latencyText, starttime, latencycount, fftMode, prevselected, fftbinwidth, nyquist, maxchannels, curselected
	structstring = '@'+('d'*maxchannels)
	structsize = maxchannels*8
	#print(structstring)
	while True:
		if faucet is False:
			return
		if flushflag is True:
			starttime = time.time()
			framecount = 0
			flushflag = False
		if decimationcount < (decimationfactor-1):
			nextpacket = read(structsize*(decimationfactor-1))
			decimationcount += decimationfactor-1
		else:
			decimationcount = 0
			nextpacket = None
			nextpacket = read(structsize)
			linesplit = struct.unpack(structstring, nextpacket)
			#print(linesplit)
			#linesplit = [i/INT_MAX for i in linesplit]
			tempcharts[:, count] = np.asarray(linesplit, dtype=float)
			count += 1
		if (count - appendlength == 0):
			if(old_fig_size != fig.get_size_inches()).any():
		        	fig.canvas.flush_events()
		        	bg = fig.canvas.copy_from_bbox(fig.bbox)
		        	old_fig_size = fig.get_size_inches()
			fig.canvas.restore_region(bg)
			charts = np.concatenate((charts[:,appendlength:],tempcharts), axis=1)
			plots.set_data(xvals, charts[curselected])
			axes.draw_artist(plots)
			fig.canvas.blit(fig.bbox)
			fig.canvas.flush_events()
			count = 0
if binaryFlag is False:
	asyncio.run(readin())
elif binaryFlag is True:
	asyncio.run(readinbinary())
window.mainloop()

