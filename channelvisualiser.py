import socket, time, sys
import matplotlib.pyplot as plt
import numpy as np
import math
from matplotlib.animation import FuncAnimation
from tkinter import *
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.gridspec as gridspec
import termios
import matplotlib.ticker as ticker

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
frameratio = appendlength * decimationfactor / 1000
curchannels = [i for i in range(maxchannels)]
def toggleFaucet(onoroff):
	global flushflag
	fc = open("/tmp/xstreamControl", "wb")
	if(onoroff == True):
		fc.write(b"\x01")
	else:
		fc.write(b"\x00")
	fc.close()
	flushflag = True
toggleFaucet(True)
#for i in range(numchannels):
#    charts.append([0] * totallength)
#for i in range(numchannels):
#    tempcharts.append([])

disabledaxes = []
disabledindex = []
disabledcount = 0
width = 4
height = 6
widthratios = [1]*width #for columns 0-3
heightratios = [1]*height # for rows 0-5

def considerateaddition(n, arr):
	saven = n
	for num in arr:
		if num <= saven:
			saven += 1
	return saven
def factor_int(n): #sufficiently close integer factors of n
	a = math.floor(math.sqrt(n))
	b = math.ceil(n/float(a))
	return a, b
def on_draw(event):
	toggleFaucet(True)
def on_click(event):
	global old_fig_size, window, fig, plt, disabledaxes, disabledcount, axes, numchannels, curchannels
	#event.inaxes.set_axis_off()
	if event.inaxes is not None:
		#event.inaxes.remove()
		event.inaxes.set_axis_off()
		#event.inaxes.set_in_layout(False)
		disabledaxes.append(event.inaxes)
		#print(np.where(axes == event.inaxes)[1][0])
		#if num of axes left <= 3, np.where()[1]
		#print(np.where(axes.flat == event.inaxes)[0][0])
		actindex = considerateaddition(np.where(axes.flat == event.inaxes)[0][0], disabledindex)
		disabledindex.append(actindex)
		#print(disabledindex)
		#print(np.where(axes==event.inaxes)[1][0], disabledindex)
		#event.inaxes.set_xlim((0, 0.01))
		#event.inaxes.set_ylim((0, 0.01))
		#check columns
		#for i in range(width):
		#	col = False #presume that all are gone
		#	for j in range(height):
		#		if axes.flat[i + width*j] not in disabledaxes: #if any are present
		#			col = True
		#	if col is False:
		#		widthratios[i] = .001
		#for j in range(height):
		#	row = False
		#	for i in range(width):
		#		if axes.flat[width*j + i] not in disabledaxes:
		#			row = True
		#	if row is False:
		#		heightratios[j] = .001
		#print(heightratios)
		#print(widthratios)
		#print(vars(axes.flat[0]))
		#gs.set_height_ratios(heightratios)
		#gs.set_width_ratios(widthratios)
		#plt.tight_layout()
		#gs.update()
		#gs.tight_layout(fig)
		#for i in range(numchannels):
			#axes.flat[i].set_position(gs[i].get_position(fig))
		
	
	old_fig_size = old_fig_size - [1,1]
	#window.update_idletasks()
	#fig.canvas.draw_idle()
	numchannels -= 1
	
	allchannels = {i for i in range(maxchannels)}
	dischannels = {i for i in disabledindex}
	curset = allchannels - dischannels
	curchannels = [elem for elem in curset]
	init_fig()


plots = []
fig, axes = plt.subplots(2,2) 
#gs = axes[0,0].get_gridspec()
xvals = range(totallength)
ylim = 0.05
flushflag = False
cid1, cid2 = (0, 0)
def init_fig():
	global plots, totallength, fig, axes, xvals, ylim, numchannels, disabledindex, numchannels, canvas, window, maxchannels, cid1,cid2
	toggleFaucet(False)
	plots = []
	xvals = range(totallength)
	height, width = factor_int(numchannels)
	#print(f"%d numchannels, %d height, %d width" % (numchannels, height, width))
	plt.close()
	fig, axes = plt.subplots(nrows=height, ncols=width, squeeze=True, sharex=True,sharey=True)
	fig.canvas.draw()
	ylim = .05
	#cid1=plt.connect('button_press_event', on_click)
	#cid2=plt.connect('draw_event', on_draw)
	#print(cid1,cid2)
	skipped = 0
	for i in range(maxchannels):
	    if i in disabledindex:
	    	skipped += 1
	    	continue
	    pltline, = axes.flat[i-skipped].plot(charts[i], marker='.', ms='.2', ls='', mfc='midnightblue', alpha=1, animated=True, zorder=10)
	    plots.append(pltline)
	    axes.flat[i-skipped].set_xlim(0, totallength)
	    axes.flat[i-skipped].set_ylim(-1*ylim, ylim)
	    axes.flat[i-skipped].draw_artist(pltline)
	    axes.flat[i-skipped].set_yticks([])
	    #ticks_x = ticker.FuncFormatter(lambda x, pos:'{0:.2f}'.format(x*decimationfactor/48000))
	    #axes.flat[i-skipped].xaxis.set_major_formatter(ticks_x)
	    axes.flat[i-skipped].set_xticks([])
	    #print("title of axes %d, %d, with skipped=%d" % ((i-skipped), (i+1), skipped))
	    axes.flat[i-skipped].set_title((i+1), fontsize='small',loc='left')
	plt.tight_layout()
	#plt.connect('button_press_event', on_click)
	canvas.get_tk_widget().pack_forget()
	canvas.get_tk_widget().destroy()
	canvas = FigureCanvasTkAgg(fig, master = window)
	cid1 = canvas.mpl_connect('button_press_event', on_click)
	civd2 = canvas.mpl_connect('draw_event', on_draw)
	canvas.draw()
	canvas.get_tk_widget().pack(fill='both',expand=True,side='top')
	diff =  (height*width) - numchannels
	for i in range(1, diff+1):
		axes.flat[-1*i].set_axis_off()
		
	toggleFaucet(True)


#for i in range(numchannels):
	#axes.flat[i].set_position(gs[i].get_position(fig))

window = Tk()
window.title("Harley's Data Viewer")
window.geometry("500x500")
canvas = FigureCanvasTkAgg(fig, master = window)
canvas.draw()
canvas.get_tk_widget().pack(fill='both',expand=True,side='top')

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
    #toggleFaucet(True)
    # bg = fig.canvas.copy_from_bbox(fig.bbox)
def updatewidth(add_or_remove):
    global axes, totallength, plt, xvals, width, height, charts, old_fig_size
    #toggleFaucet(False)
    if add_or_remove == "add":
        totallength += appendlength #increase width by a frame
        charts = np.append(np.zeros((24,appendlength)), charts, axis=1)
        for i in range(numchannels):
            axes.flat[i].set_xlim(0, totallength)
        xvals = range(totallength)
        xText.delete("1.0", "1.60")
        xText.insert(INSERT, "Width: "+("%.0f"%(totallength*decimationfactor))+" samples (undecimated)")
    elif totallength > 2*appendlength:
        totallength -= appendlength
        charts = charts[:, appendlength:]
        for i in range(numchannels):
            axes.flat[i].set_xlim(0, totallength)
        xvals = range(totallength)
        xText.delete("1.0", "1.60")
        xText.insert(INSERT, "Width: "+("%.0f"%(totallength*decimationfactor))+" samples (undecimated)")
    #for i in range(len(axes)):
        #ticks_x = ticker.FuncFormatter(lambda x, pos:'{0:.2f}'.format(x*decimationfactor/48000))
        #axes.flat[i].xaxis.set_major_formatter(ticks_x)
    old_fig_size = old_fig_size - [1,1]
    fig.canvas.draw_idle()
    toggleFaucet(True)
def resetfig():
	global axes, fig, disabledaxes, old_fig_size
	toggleFaucet(False)
	for disabledax in disabledaxes:
		disabledax.set_axis_on()
	disabledaxes = []
	disabledindex = []
	#for i in range(numchannels):
		#axes.flat[i].set_position(gs[i].get_position(fig))
	old_fig_size = old_fig_size - [1,1]
	#window.update_idletasks()
	fig.canvas.draw_idle()
	#toggleFaucet(True)
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
init_fig()
#window.attributes('-zoomed', True)



# plt.get_current_fig_manager().window.state('zoomed')
# plt.show(block=False)
#plt.pause(0.0000001)
plt.close()
bg = fig.canvas.copy_from_bbox(fig.bbox)
old_fig_size = fig.get_size_inches()
fig.canvas.blit(fig.bbox)

#print(cid1, cid2)
for line in sys.stdin:
    if flushflag:
     #   sys.stdin.flush()
        starttime = time.time()
        framecount = 0
        flushflag = False
        #continue
    if decimationcount < (decimationfactor-1):
        decimationcount += 1
    else:
        decimationcount = 0
        linesplit = line.split("\t")
        tempcharts[:, count] = np.asarray(linesplit, dtype=float)
        #for i in range(numchannels):
        #   tempcharts[i].append(float(linesplit[i]))
        count += 1
        if (count % appendlength == 0):
            if(old_fig_size != fig.get_size_inches()).any():
                fig.canvas.flush_events()
                bg = fig.canvas.copy_from_bbox(fig.bbox)
                old_fig_size = fig.get_size_inches()
            fig.canvas.restore_region(bg)
            charts = np.concatenate((charts[:,appendlength:],tempcharts), axis=1)
            for i in range(numchannels):
                plots[i].set_data(xvals, charts[curchannels[i]])
                #if axes.flat[i] not in disabledaxes:
                axes.flat[i].draw_artist(plots[i])
            fig.canvas.blit(fig.bbox)
            # fig.canvas.draw()
            fig.canvas.flush_events()
            framecount += frameratio
            #print("Time Since Start: %3.2f, Framecount: %5dk, Ideal: %5dk" % (time.time() - starttime, framecount, 48*(time.time()-starttime)))
            latencyText.delete("1.0", "1.50")
            latencyText.insert(INSERT, "Frame Difference: "+("%.0f"%(48*(time.time()-starttime) - framecount))+"k")
            #if 48*(time.time()-starttime) - framecount < -100:
            #	flushflag = True
            
            
            
            count = 0
print(time.time() - starttime)
window.mainloop()


#TODO: Flush sys.stdin upon reinit of fig
#TODO: Make markers much more darker/visible, look into reinstating lines
#TODO: Allow for zooming in beyond 2 frames
#TODO: Utilize xstream faucet for data control?
#NOTE: Ideally, append enableFaucet(True) to the end of draw_idle
#	OR: stop using draw_idle()
