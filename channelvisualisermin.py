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

#The toggleFaucet method exists to interact with the xstream process, namely by turning on or off the flow of data from xstream to stdout/stdin.
#This is achieved by writing either '0' or '1' to /tmp/xstreamControl, a pipe which is read in by xstream
#When toggled off, the faucet flag is set to False, which turns off readin(). When turned back on, readin() should be also called.


#This method helps map the enabled/disabled axes to the plotaxes. This essentially places a given n in the first available space in arr.
#If given 1 and [0,1,2,4], it would return 3 (can't place at 1, so check at +1. Can't place at 2, so check at +2. 3 is open, so return 3)
def considerateaddition(n, arr):
	saven = n
	for num in arr:
		if num <= saven:
			saven += 1
	return saven
#Used to get a balanced width/height for any given number of plots.
#sufficiently close integer factors of n
def factor_int(n): 
	a = math.floor(math.sqrt(n))
	b = math.ceil(n/float(a))
	return a, b
#the on_draw method is called whenever the on_draw event is triggered
def on_draw(event):
	a = 1
	#print('hello')
	#toggleFaucet(True)
	
#the on_click method is called whenever the on_click event is triggered
#Here, it checks to see if a plot was clicked, then determined which plot was clicked, and essentially minimizes that plot.
def on_click(event):
	global old_fig_size, window, fig, plt, disabledaxes, disabledcount, axes, numchannels, curchannels
	#event.inaxes.set_axis_off()
	if numchannels == 2:
		return
	if event.inaxes is not None and np.where(axes.flat == event.inaxes)[0][0] < numchannels:
		event.inaxes.set_axis_off()
		disabledaxes.append(event.inaxes)
		actindex = considerateaddition(np.where(axes.flat == event.inaxes)[0][0], disabledindex)
		#print(actindex)
		disabledindex.append(actindex)
		numchannels -= 1
	
		old_fig_size = old_fig_size - [1,1]
		
		allchannels = {i for i in range(maxchannels)}
		dischannels = {i for i in disabledindex}
		curset = allchannels - dischannels
		curchannels = [elem for elem in curset]
		init_fig()


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
	global plots, totallength, fig, axes, xvals, ylim, numchannels, disabledindex, numchannels, canvas, window, maxchannels, fftMode, old_fig_size, decimationfactor, totallength, appendlength, charts, tempcharts
	decimationfactor = 10
	totallength = int(48000 / (2*decimationfactor))
	appendlength = int(4800 / (decimationfactor))
	charts = np.zeros((maxchannels, totallength))
	tempcharts = np.zeros((maxchannels, appendlength))
	fftMode = False
	plots = []
	xvals = range(totallength)
	width, height = factor_int(numchannels)
	plt.close()
	fig, axes = plt.subplots(nrows=height, ncols=width, squeeze=True, sharex=True,sharey=True)
	ylim = .05
	plt.connect('button_press_event', on_click)
	plt.connect('draw_event', on_draw)
	skipped = 0
	if maxchannels > 1:
		for i in range(maxchannels):
		    if i in disabledindex:
		    	skipped += 1
		    	continue
		    ms = "{:.1f}".format((2+(maxchannels-numchannels)/2)/10)
		    pltline, = axes.flat[i-skipped].plot(charts[i], '.k', ms=ms, ls='', alpha=1, animated=True, zorder=10)
		    plots.append(pltline)
		    axes.flat[i-skipped].set_xlim(0, totallength)
		    axes.flat[i-skipped].set_ylim(-1*ylim, ylim)
		    axes.flat[i-skipped].draw_artist(pltline)
		    axes.flat[i-skipped].set_yticks([])
		    axes.flat[i-skipped].set_xticks([])
		    axes.flat[i-skipped].set_title((i+1), fontsize='small',loc='left')
		    
		
		labels = [str(plot.get_label()) for plot in plots]
		visibility = [plot.get_visible() for plot in plots]
		#rax = fig.inset_axes([0.0, 0.0, 0.12,0.2])
		#check = CheckButtons(rax, labels, visibility)
		buttons = []
			
		#print(ms)
		plt.tight_layout()
		plt.connect('button_press_event', on_click)
		canvas.get_tk_widget().pack_forget()
		canvas.get_tk_widget().destroy()
		canvas = FigureCanvasTkAgg(fig, master = window)
		canvas.draw()
		canvas.get_tk_widget().pack(fill='both',expand=True,side='top')
		old_fig_size = old_fig_size - [1,1]
		diff =  (height*width) - numchannels
		for i in range(1, diff+1):
			axes.flat[-1*i].set_axis_off()



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

init_fig()
window.attributes('-zoomed', True)


plt.pause(0.0000001)
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


#once everything is ready, turn on the faucet and start streaming in data
try:
	fc = open("/tmp/xstreamControl", "ab")
	fc.write(b"\x01")
	fc.close()
except:
	print("exception")
if binaryFlag is False:
	tempmaxchannels = len(sys.stdin.readline().split("\t"))
	if(tempmaxchannels != maxchannels):
		maxchannels = tempmaxchannels
		numchannels = maxchannels
		charts = np.zeros((maxchannels, totallength))
		tempcharts = np.zeros((maxchannels, appendlength))
		curchannels = [i for i in range(maxchannels)]
		init_fig()
	print(maxchannels)
elif binaryFlag is True:
	sys.stdin.read
	byte = read(1)
	print(byte)
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

mb = Menubutton(masterFrame, text="FFT Channels", relief=RAISED)
#mb.grid()
mb.menu = Menu(mb)
checkbuttonvars = []
prevselected = []
def printSelectedOptions():
	global checkbuttonvars, prevselected, fftToggleVar
	selectedOptions = [count for (count, var) in enumerate(checkbuttonvars) if var.get()]
	latestOption = np.setdiff1d(selectedOptions, prevselected)
	print(latestOption)
	if len(selectedOptions) > 4:
		checkbuttonvars[latestOption[0]].set(False)
	else:
		prevselected = selectedOptions
	print(prevselected)
	if(fftToggleVar.get() == 1):
		init_fft()
mb['menu'] = mb.menu
for i in range(maxchannels):
	var = BooleanVar()
	checkbuttonvars.append(var)
	mb.menu.add_checkbutton(variable=var, label=str(i+1), command=lambda:printSelectedOptions())
mb.pack()

sleeptimer = 0
latencycount = 0
async def readin():
	global flushflag, faucet, decimationcount, decimationfactor, fig, axes, tempcharts, count, old_fig_size, bg, charts, plots, framecount, sleeptimer, latencyText, starttime, latencycount, fftMode, prevselected, fftbinwidth, nyquist
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
			if fftMode is False:
				for i in range(numchannels):
					plots[i].set_data(xvals, charts[curchannels[i]])
					#plots[i].set_data(xvals, np.fft.fft(charts[curchannels[i]]))
					axes.flat[i].draw_artist(plots[i])
			elif len(prevselected) > 1:
				for count, i in enumerate(prevselected):
					y = np.fft.fft(charts[curchannels[i]])
					y1, y2 = np.split(y, 2)
					y2 = y2[::-1]
					y = np.sqrt(np.square(y1) + np.square(y2))
					x = range(0, nyquist, int(fftbinwidth))
					plots[count].set_data(x, y)
					axes.flat[count].draw_artist(plots[count])
			elif len(prevselected) == 1:
				y = np.fft.fft(charts[prevselected[0]])
				y1, y2 = np.split(y, 2)
				y2 = y2[::-1]
				y = np.sqrt(np.square(y1) + np.square(y2))
				x = range(0, nyquist, int(fftbinwidth))
				plots[0].set_data(x, y)
				plots[0].set_data(x, y)
				axes.draw_artist(plots[0])
			fig.canvas.blit(fig.bbox)
			fig.canvas.flush_events()
			framecount += appendlength * decimationfactor / 1000
			latencyText.delete("1.0", "1.50")
			latencyval = (48*(time.time()-starttime) - framecount)
			latencyText.insert(INSERT, "Frame Delta: "+("%.0f"%(latencycount-latencyval))+"k")
			latencycount = 0.1*latencyval + 0.9*latencycount
			count = 0
	print(time.time() - starttime)
	

async def readinbinary():
	global flushflag, faucet, decimationcount, decimationfactor, fig, axes, tempcharts, count, old_fig_size, bg, charts, plots, framecount, sleeptimer, latencyText, starttime, latencycount, fftMode, prevselected, fftbinwidth, nyquist, maxchannels
	structstring = '@'+('d'*maxchannels)
	structsize = maxchannels*8
	print(structstring)
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
			if fftMode is False:
				for i in range(numchannels):
					plots[i].set_data(xvals, charts[curchannels[i]])
					#plots[i].set_data(xvals, np.fft.fft(charts[curchannels[i]]))
					axes.flat[i].draw_artist(plots[i])
			elif len(prevselected) > 1:
				for count, i in enumerate(prevselected):
					y = np.fft.fft(charts[curchannels[i]])
					y1, y2 = np.split(y, 2)
					y2 = y2[::-1]
					y = np.sqrt(np.square(y1) + np.square(y2))
					x = range(0, nyquist, int(fftbinwidth))
					plots[count].set_data(x, y)
					axes.flat[count].draw_artist(plots[count])
			elif len(prevselected) == 1:
				y = np.fft.fft(charts[prevselected[0]])
				y1, y2 = np.split(y, 2)
				y2 = y2[::-1]
				y = np.sqrt(np.square(y1) + np.square(y2))
				x = range(0, nyquist, int(fftbinwidth))
				plots[0].set_data(x, y)
				plots[0].set_data(x, y)
				axes.draw_artist(plots[0])
			fig.canvas.blit(fig.bbox)
			fig.canvas.flush_events()
			framecount += appendlength * decimationfactor / 1000
			latencyText.delete("1.0", "1.50")
			latencyval = (48*(time.time()-starttime) - framecount)
			latencyText.insert(INSERT, "Frame Delta: "+("%.0f"%(latencycount-latencyval))+"k")
			latencycount = 0.1*latencyval + 0.9*latencycount
			count = 0
	print(time.time() - starttime)
if binaryFlag is False:
	asyncio.run(readin())
elif binaryFlag is True:
	asyncio.run(readinbinary())
window.mainloop()



#USE sys.stdin.buffer.read() instead of os.read?
