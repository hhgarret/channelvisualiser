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

fftMode = False

#The toggleFaucet method exists to interact with the xstream process, namely by turning on or off the flow of data from xstream to stdout/stdin.
#This is achieved by writing either '0' or '1' to /tmp/xstreamControl, a pipe which is read in by xstream
#When toggled off, the faucet flag is set to False, which turns off readin(). When turned back on, readin() should be also called.
def toggleFaucet(onoroff):
	global flushflag, faucet, fc
	#print(onoroff)
	if(onoroff == True):
		fc = open("/tmp/xstreamControl", "ab")
		fc.write(b"\x01")
		fc.close()
		faucet = True
		flushflag = True
		asyncio.run(readin())
	elif onoroff == False:
		fc = open("/tmp/xstreamControl", "ab")
		fc.write(b"\x00")
		fc.close()
		faucet = False
		flushflag = True
	else:
		if faucet == True:
			fc = open("/tmp/xstreamControl", "ab")
			fc.write(b"\x00")
			fc.close()
			faucet = False
		elif faucet == False:
			fc = open("/tmp/xstreamControl", "ab")
			fc.write(b"\x01")
			fc.close()
			faucet = True
			asyncio.run(readin())
	print(faucet)


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
	if event.inaxes is not None:
		event.inaxes.set_axis_off()
		disabledaxes.append(event.inaxes)
		actindex = considerateaddition(np.where(axes.flat == event.inaxes)[0][0], disabledindex)
		print(actindex)
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


def init_fft():
	print('init_fft')
	global plots, totallength, fig, axes, xvals, ylim, numchannels, disabledindex, numchannels, canvas, window, maxchannels, fftMode, prevselected, old_fig_size, decimationfactor, totallength, appendlength, charts, tempcharts
	decimationfactor = 1
	totallength = int(48000 / (2*decimationfactor))
	appendlength = int(4800 / (decimationfactor))
	charts = np.zeros((maxchannels, totallength))
	tempcharts = np.zeros((maxchannels, appendlength))
	fftMode = True
	plots = []
	xvals = range(totallength)
	width, height = factor_int(len(prevselected))
	print(width,height)
	plt.close()
	fig, axes = plt.subplots(nrows=height, ncols=width, squeeze=True, sharex=True,sharey=True)
	ylim = .05
	plt.connect('button_press_event', on_click)
	plt.connect('draw_event', on_draw)
	skipped = 0

	if len(prevselected) > 1:
		for count, i in enumerate(prevselected):
		    #ms = "{:.1f}".format((2+(maxchannels-numchannels)/2)/10)
		    pltline, = axes.flat[count].plot(charts[i], alpha=1, animated=True, zorder=10)
		    plots.append(pltline)
		    axes.flat[count].set_xlim(0, totallength/2)
		    axes.flat[count].set_ylim(0, ylim*2)
		    axes.flat[count].draw_artist(pltline)
		    axes.flat[count].set_yticks([])
		    axes.flat[count].set_xticks([])
		    axes.flat[count].set_title((i+1), fontsize='small',loc='left')
		plt.tight_layout()
		plt.connect('button_press_event', on_click)
		canvas.get_tk_widget().pack_forget()
		canvas.get_tk_widget().destroy()
		canvas = FigureCanvasTkAgg(fig, master = window)
		canvas.draw()
		canvas.get_tk_widget().pack(fill='both',expand=True,side='top')
	elif len(prevselected) == 1:
		#ms = "{:.1f}".format((2+(maxchannels-numchannels)/2)/10)
		pltline, = axes.plot(charts[prevselected[0]], alpha=1, animated=True, zorder=10)
		plots.append(pltline)
		axes.set_xlim(0, totallength/2)
		axes.set_ylim(0, ylim*2)
		axes.draw_artist(pltline)
		axes.set_yticks([])
		axes.set_xticks([])
		axes.set_title((prevselected[0]+1), fontsize='small',loc='left')
		plt.tight_layout()
		plt.connect('button_press_event', on_click)
		canvas.get_tk_widget().pack_forget()
		canvas.get_tk_widget().destroy()
		canvas = FigureCanvasTkAgg(fig, master = window)
		canvas.draw()
		canvas.get_tk_widget().pack(fill='both',expand=True,side='top')
	old_fig_size = old_fig_size - [1,1]


window = Tk()
window.title("Harley's Data Viewer")
window.geometry("500x500")
canvas = FigureCanvasTkAgg(fig, master = window)
canvas.draw()
canvas.get_tk_widget().pack(fill='both',expand=True,side='top')

#updateheight increases/decreases the ylim of the graphs
def updateheight(add_or_remove):
    global axes, ylim, plt, old_fig_size
    #toggleFaucet(False)
    if add_or_remove == "add":
        ylim *= 1.5
        yText.delete("1.0", "1.60")
        yText.insert(INSERT, "Height: +/-"+("%.4f"%ylim))
    else:
        ylim *= 1/1.5
        yText.delete("1.0", "1.60")
        yText.insert(INSERT, "Height: +/-"+("%.4f"%ylim))
    for i in range(numchannels):
        axes.flat[i].set_ylim(-1*ylim, ylim)
    old_fig_size = old_fig_size - [1,1]
    fig.canvas.draw_idle()
#updatewidth increases/decreases the xlim of the graphs & charts, either allowing more or less points/frames to be displayed
def updatewidth(add_or_remove):
    global axes, totallength, plt, xvals, height, charts, old_fig_size, decimationfactor, appendlength, count, decimationcount, tempcharts
    if add_or_remove == "add":
        totallength += appendlength #increase width by a frame
        charts = np.append(np.zeros((maxchannels,appendlength)), charts, axis=1)
        for i in range(numchannels):
            axes.flat[i].set_xlim(0, totallength)
        xvals = range(totallength)
    elif totallength > 2*appendlength:
        totallength -= appendlength
        charts = charts[:, appendlength:]
        for i in range(numchannels):
            axes.flat[i].set_xlim(0, totallength)
        xvals = range(totallength)
       
    else: #decrease, but below the current two frames... idea is to decrease df, increase frames
    	if appendlength == 480:
    		appendlength = int(appendlength/2)
    		decimationfactor = 8
    	elif appendlength == 240:
    		appendlength = int(appendlength/2)
    		decimationfactor = 7
    	tempcharts = np.zeros((maxchannels, appendlength))
    	for i in range(numchannels):
    	    axes.flat[i].set_xlim(0, totallength)
    	xvals = range(totallength)
    	count = 0
    	decimationcount = 0
    xText.delete("1.0", "1.100")
    xText.insert(INSERT, "Width: "+("%.0f"%(totallength*decimationfactor))+" samples (undecimated), decimation of "+str(decimationfactor))
    old_fig_size = old_fig_size - [1,1]
    fig.canvas.draw_idle()
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
yFrame = Frame(master = masterFrame)
yFrame.pack(side = LEFT)
xFrame = Frame(master = masterFrame)
xFrame.pack(side = RIGHT)
increase_y_button = Button(master = yFrame, command = lambda:updateheight("add"), height=2, width=20, text="zoom out height")
increase_y_button.pack()
window.bind('<Up>', lambda event:updateheight("add"))
yText = Text(master = yFrame, height = 1)
yText.insert(INSERT, "Height: +/-"+("%.4f"%ylim))
yText.pack()
decrease_y_button = Button(master = yFrame, command = lambda:updateheight("remove"), height=2, width=20, text="zoom in height")
decrease_y_button.pack()
window.bind('<Down>', lambda event:updateheight("remove"))
increase_x_button = Button(master = xFrame, command = lambda:updatewidth("add"), height=2, width=20, text="zoom out width")
increase_x_button.pack()
window.bind('<Right>', lambda event:updatewidth("add"))
xText = Text(master = xFrame, height = 1)
xText.insert(INSERT, "Width: "+("%.0f"%(totallength*decimationfactor))+" samples (undecimated)")
xText.pack()
decrease_x_button = Button(master = xFrame, command = lambda:updatewidth("remove"), height=2, width=20, text="zoom in width")
decrease_x_button.pack()
window.bind('<Left>', lambda event:updatewidth("remove"))
latencyText = Text(master = masterFrame, height = 1)
latencyText.pack(side = BOTTOM)
resetButton = Button(master = masterFrame, height = 1, command = lambda:resetfig(),text="reset fig")
resetButton.pack(side= BOTTOM)
pauseButton = Button(master = masterFrame, height = 1, command = lambda:toggleFaucet(""), text="pause fig")
pauseButton.pack(side=BOTTOM)

fftToggleVar = IntVar()
fftToggleVar.set(0)
def fftToggleFunc():
	global fftToggleVar
	if(fftToggleVar.get() == 1):
		init_fft()
	else:
		init_fig()
fftToggle = Checkbutton(masterFrame, variable=fftToggleVar, text='FFT Mode', command=fftToggleFunc)
fftToggle.pack()
init_fig()
window.attributes('-zoomed', True)


plt.pause(0.0000001)
plt.close()
bg = fig.canvas.copy_from_bbox(fig.bbox)
old_fig_size = fig.get_size_inches()
fig.canvas.blit(fig.bbox)


#once everything is ready, turn on the faucet and start streaming in data
try:
	fc = open("/tmp/xstreamControl", "ab")
	fc.write(b"\x01")
	fc.close()
except:
	print("exception")
tempmaxchannels = len(sys.stdin.readline().split("\t"))
if(tempmaxchannels != maxchannels):
	maxchannels = tempmaxchannels
	numchannels = maxchannels
	charts = np.zeros((maxchannels, totallength))
	tempcharts = np.zeros((maxchannels, appendlength))
	curchannels = [i for i in range(maxchannels)]
print(maxchannels)


mb = Menubutton(masterFrame, text="FFT Channels", relief=RAISED)
#mb.grid()
mb.menu = Menu(mb)
checkbuttonvars = []
prevselected = []
def printSelectedOptions():
	global checkbuttonvars, prevselected
	selectedOptions = [count for (count, var) in enumerate(checkbuttonvars) if var.get()]
	latestOption = np.setdiff1d(selectedOptions, prevselected)
	print(latestOption)
	if len(selectedOptions) > 4:
		checkbuttonvars[latestOption[0]].set(False)
	else:
		prevselected = selectedOptions
	print(prevselected)
mb['menu'] = mb.menu
for i in range(maxchannels):
	var = BooleanVar()
	checkbuttonvars.append(var)
	mb.menu.add_checkbutton(variable=var, label=str(i+1), command=lambda:printSelectedOptions())
mb.pack()

sleeptimer = 0
latencycount = 0
async def readin():
	global flushflag, faucet, decimationcount, decimationfactor, fig, axes, tempcharts, count, old_fig_size, bg, charts, plots, framecount, sleeptimer, latencyText, starttime, latencycount, fftMode, prevselected
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
					x = range(len(y))
					plots[count].set_data(x, y)
					axes.flat[count].draw_artist(plots[count])
			elif len(prevselected) == 1:
				y = np.fft.fft(charts[curchannels[i]])
				y1, y2 = np.split(y, 2)
				y2 = y2[::-1]
				y = np.sqrt(np.square(y1) + np.square(y2))
				x = range(len(y))
				plots[0].set_data(x, y)
				plots[0].set_data(x,y)
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
asyncio.run(readin())
window.mainloop()


#TODO: Flush sys.stdin upon reinit of fig ~~
#TODO: Allow for zooming in EVEN FURTHER
#TODO: Binary flag
#Ideas on how to continue to zoom in. After a certain point, decrease decimation
#TODO: rescale fft window, y = 0 -> ylim, x = 0 -> x/2

#TODO: Implement FFT Mode (toggle, read in the selected channels, plot their rfft)
