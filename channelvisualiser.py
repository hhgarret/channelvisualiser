import socket, time, sys
import matplotlib.pyplot as plt
import numpy as np
import math
from matplotlib.animation import FuncAnimation
from tkinter import *
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.gridspec as gridspec

starttime = time.time();
decimationfactor = 10
decimationcount = 0
count = 0
totallength = int(48000 / (2*decimationfactor))
appendlength = int(4800 / (decimationfactor))
numchannels = 24
charts = np.zeros((24, totallength))
tempcharts = np.zeros((24, appendlength))

framecount = 0;
frameratio = appendlength * decimationfactor / 1000


#for i in range(numchannels):
#    charts.append([0] * totallength)
#for i in range(numchannels):
#    tempcharts.append([])

disabledaxes = []
disabledcount = 0
width = 4
height = 6
widthratios = [1]*width #for columns 0-3
heightratios = [1]*height # for rows 0-5
def on_click(event):
	global old_fig_size, window, fig, plt, disabledaxes, disabledcount, axes, gs, heightratios, widthratios
	#event.inaxes.set_axis_off()
	if event.inaxes is not None:
		#event.inaxes.remove()
		event.inaxes.set_axis_off()
		#event.inaxes.set_in_layout(False)
		disabledaxes.append(event.inaxes)
		#event.inaxes.set_xlim((0, 0.01))
		#event.inaxes.set_ylim((0, 0.01))
		#check columns
		for i in range(width):
			col = False #presume that all are gone
			for j in range(height):
				if axes.flat[i + width*j] not in disabledaxes: #if any are present
					col = True
			if col is False:
				widthratios[i] = .001
		for j in range(height):
			row = False
			for i in range(width):
				if axes.flat[width*j + i] not in disabledaxes:
					row = True
			if row is False:
				heightratios[j] = .001
		#print(heightratios)
		#print(widthratios)
		#print(vars(axes.flat[0]))
		gs.set_height_ratios(heightratios)
		gs.set_width_ratios(widthratios)
		#plt.tight_layout()
		gs.update()
		gs.tight_layout(fig)
		for i in range(numchannels):
			axes.flat[i].set_position(gs[i].get_position(fig))
		
	old_fig_size = old_fig_size - [1,1]
	window.update_idletasks()
	fig.canvas.draw_idle()

plots = []
xvals = range(totallength)
fig, axes = plt.subplots(nrows=height, ncols=width, squeeze=True, gridspec_kw={'width_ratios':widthratios, 'height_ratios':heightratios})
gs = axes[0,0].get_gridspec()
ylim = .05
plt.connect('button_press_event', on_click)
for i in range(numchannels):
    pltline, = axes.flat[i].plot(charts[i], marker='.', ms='.1', ls='', alpha=1, animated=True, zorder=10)
    plots.append(pltline)
    axes.flat[i].set_xlim(0, totallength)
    axes.flat[i].set_ylim(-1*ylim, ylim)
    axes.flat[i].draw_artist(pltline)
    axes.flat[i].set_yticks([])
    axes.flat[i].set_xticks([])
    axes.flat[i].set_title((i+1), fontsize='small',loc='left')
#plt.tight_layout()
gs.tight_layout(fig)

for i in range(numchannels):
	axes.flat[i].set_position(gs[i].get_position(fig))

window = Tk()
window.title("Harley's Data Viewer")
window.geometry("500x500")
canvas = FigureCanvasTkAgg(fig, master = window)
canvas.draw()
canvas.get_tk_widget().pack(fill='both',expand=True,side='top')
def updateheight(add_or_remove):
    global axes, ylim, plt
    if add_or_remove == "add":
        ylim *= 1.5
        yText.delete("1.0", "1.30")
        yText.insert(INSERT, "Height: +/-"+("%.4f"%ylim))
    else:
        ylim *= 1/1.5
        yText.delete("1.0", "1.30")
        yText.insert(INSERT, "Height: +/-"+("%.4f"%ylim))
    for i in range(numchannels):
        axes.flat[i].set_ylim(-1*ylim, ylim)
    # bg = fig.canvas.copy_from_bbox(fig.bbox)
def updatewidth(add_or_remove):
    global axes, totallength, plt, xvals, width, height, charts
    if add_or_remove == "add":
        totallength += appendlength #increase width by a frame
        charts = np.append(np.zeros((24,appendlength)), charts, axis=1)
        for i in range(numchannels):
            axes.flat[i].set_xlim(0, totallength)
        xvals = range(totallength)
        xText.delete("1.0", "1.30")
        xText.insert(INSERT, "Width: "+("%f"%(totallength*decimationfactor))+" samples (undecimated)")
    elif totallength > 2*appendlength:
        totallength -= appendlength
        charts = charts[:, appendlength:]
        for i in range(numchannels):
            axes.flat[i].set_xlim(0, totallength)
        xvals = range(totallength)
        xText.delete("1.0", "1.30")
        xText.insert(INSERT, "Width: "+("%f"%(totallength*decimationfactor))+" samples (undecimated)")
def resetfig():
	global axes, fig, gs, widthratios, heightratios, disabledaxes, old_fig_size
	for disabledax in disabledaxes:
		disabledax.set_axis_on()
	disabledaxes = []
	widthratios = [1]*width
	heightratios = [1]*height
	gs.set_height_ratios(heightratios)
	gs.set_width_ratios(widthratios)
	gs.update()
	gs.tight_layout(fig)
	for i in range(numchannels):
		axes.flat[i].set_position(gs[i].get_position(fig))
	old_fig_size = old_fig_size - [1,1]
	window.update_idletasks()
	fig.canvas.draw_idle()
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
xText.insert(INSERT, "Width: "+("%f"%(totallength*decimationfactor))+" samples (undecimated)")
xText.pack()
decrease_x_button = Button(master = xFrame, command = lambda:updatewidth("remove"), height=2, width=20, text="zoom in width")
decrease_x_button.pack()
window.bind('<Left>', lambda event:updatewidth("remove"))
latencyText = Text(master = masterFrame, height = 1)
latencyText.pack(side = BOTTOM)
resetButton = Button(master = masterFrame, height = 1, command = lambda:resetfig(),text="reset fig")
resetButton.pack(side= BOTTOM)
window.attributes('-zoomed', True)



# plt.get_current_fig_manager().window.state('zoomed')
# plt.show(block=False)
plt.pause(0.0000001)
plt.close()
bg = fig.canvas.copy_from_bbox(fig.bbox)
old_fig_size = fig.get_size_inches()
fig.canvas.blit(fig.bbox)


for line in sys.stdin:
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
                #charts[i] = charts[i][appendlength:] + tempcharts[i]
                #tempcharts[i] = []
                plots[i].set_data(xvals, charts[i])
                if axes.flat[i] not in disabledaxes:
                	axes.flat[i].draw_artist(plots[i])
            fig.canvas.blit(fig.bbox)
            # fig.canvas.draw()
            fig.canvas.flush_events()
            framecount += frameratio
            #print("Time Since Start: %3.2f, Framecount: %5dk, Ideal: %5dk" % (time.time() - starttime, framecount, 48*(time.time()-starttime)))
            latencyText.delete("1.0", "1.50")
            latencyText.insert(INSERT, "Frame Difference: "+("%.4f"%(48*(time.time()-starttime) - framecount))+"k")
            
            
            
            count = 0
print(time.time() - starttime)
window.mainloop()

def factor_int(n): #sufficiently close integer factors of n
	a = math.floor(math.sqrt(n))
	b = math.ceil(n/float(a))
	return a, b


#TODO: Recognize channel count from first line of input, adapt format to match
#	i.e., read in number of channels, find x,y which are closest factors
#TODO: Reset entire fig upon number of channels changed, i.e., redraw with n channels display
