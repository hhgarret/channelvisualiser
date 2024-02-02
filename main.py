import socket, time, sys
import matplotlib.pyplot as plt
import numpy as np
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
charts = []
tempcharts = []

framecount = 0;
frameratio = appendlength * decimationfactor / 1000


for i in range(24):
    charts.append([0] * totallength)
for i in range(24):
    tempcharts.append([])

disabledaxes = []
disabledcount = 0
widthratios = [1, 1, 1, 1] #for columns 0-3
heightratios = [1, 1, 1, 1, 1, 1] # for rows 0-5
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
		for i in range(4):
			col = False #presume that all are gone
			for j in range(6):
				if axes.flat[i + 4*j] not in disabledaxes: #if any are present
					col = True
			if col is False:
				widthratios[i] = .001
		for j in range(6):
			row = False
			for i in range(4):
				if axes.flat[4*j + i] not in disabledaxes:
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
		for i in range(24):
			axes.flat[i].set_position(gs[i].get_position(fig))
		
	old_fig_size = old_fig_size - [1,1]
	window.update_idletasks()
	fig.canvas.draw_idle()

plots = []
xvals = range(totallength)
fig, axes = plt.subplots(nrows=6, ncols=4, squeeze=True, gridspec_kw={'width_ratios':widthratios, 'height_ratios':heightratios})
gs = axes[0,0].get_gridspec()
ylim = .05
plt.connect('button_press_event', on_click)
for i in range(24):
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

for i in range(24):
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
        yText.insert(INSERT, "Height: +/-"+str(ylim))
    else:
        ylim *= 1/1.5
        yText.delete("1.0", "1.30")
        yText.insert(INSERT, "Height: +/-"+str(ylim))
    for i in range(24):
        axes.flat[i].set_ylim(-1*ylim, ylim)
    # bg = fig.canvas.copy_from_bbox(fig.bbox)
def updatewidth(add_or_remove):
    global axes, totallength, plt, xvals
    if add_or_remove == "add":
        totallength += appendlength #increase width by a frame
        for i in range(24):
            charts[i] = [0]*appendlength + charts[i]
            axes.flat[i].set_xlim(0, totallength)
        xvals = range(totallength)
        xText.delete("1.0", "1.30")
        xText.insert(INSERT, "Width: "+str(totallength)+" samples")
    elif totallength > 2*appendlength:
        totallength -= appendlength
        for i in range(24):
            charts[i] = charts[i][appendlength:]
            axes.flat[i].set_xlim(0, totallength)
        xvals = range(totallength)
        xText.delete("1.0", "1.30")
        xText.insert(INSERT, "Width: "+str(totallength)+" samples")
def resetfig():
	global axes, fig, gs, widthratios, heightratios, disabledaxes, old_fig_size
	for disabledax in disabledaxes:
		disabledax.set_axis_on()
	disabledaxes = []
	widthratios = [1,1,1,1]
	heightratios = [1,1,1,1,1,1]
	gs.set_height_ratios(heightratios)
	gs.set_width_ratios(widthratios)
	gs.update()
	gs.tight_layout(fig)
	for i in range(24):
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
yText = Text(master = yFrame, height = 1)
yText.insert(INSERT, "Height: +/-"+str(ylim))
yText.pack()
decrease_y_button = Button(master = yFrame, command = lambda:updateheight("remove"), height=2, width=20, text="zoom in height")
decrease_y_button.pack()
increase_x_button = Button(master = xFrame, command = lambda:updatewidth("add"), height=2, width=20, text="zoom out width")
increase_x_button.pack()
xText = Text(master = xFrame, height = 1)
xText.insert(INSERT, "Width: "+str(totallength)+" samples")
xText.pack()
decrease_x_button = Button(master = xFrame, command = lambda:updatewidth("remove"), height=2, width=20, text="zoom in width")
decrease_x_button.pack()
latencyText = Text(master = masterFrame, height = 1)
latencyText.pack(side = BOTTOM)
resetButton = Button(master = masterFrame, height = 1, command = lambda:resetfig(),text="reset fig")
resetButton.pack(side= BOTTOM)



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
        for i in range(24):
            tempcharts[i].append(float(linesplit[i]))
        count += 1
        if (count % appendlength == 0):
            if(old_fig_size != fig.get_size_inches()).any():
                fig.canvas.flush_events()
                bg = fig.canvas.copy_from_bbox(fig.bbox)
                old_fig_size = fig.get_size_inches()
            fig.canvas.restore_region(bg)
            for i in range(24):
                charts[i] = charts[i][appendlength:] + tempcharts[i]
                tempcharts[i] = []
                plots[i].set_data(xvals, charts[i])
                if axes.flat[i] not in disabledaxes:
                	axes.flat[i].draw_artist(plots[i])
            fig.canvas.blit(fig.bbox)
            # fig.canvas.draw()
            fig.canvas.flush_events()
            framecount += frameratio
            #print("Time Since Start: %3.2f, Framecount: %5dk, Ideal: %5dk" % (time.time() - starttime, framecount, 48*(time.time()-starttime)))
            latencyText.delete("1.0", "1.50")
            latencyText.insert(INSERT, "Frame Difference: "+str(48*(time.time()-starttime) - framecount)+"k")
            
            
            
            count = 0
print(time.time() - starttime)
window.mainloop()


#TODO: Utilize numpy
