from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as PLT
from matplotlib import dates
from statsmodels.nonparametric.smoothers_lowess import lowess

import StringIO
import time
from datetime import date, datetime

def getGraph(x,y):
    x_smooth,y_smooth = smoothXY(x,y,frac = 0.02)
    fig = getFigureByXY(x,y_smooth)
    response = makeImageResponseFromFigure(fig)
    return response

def getFigureByXY(x,y, ylabel='\nOutput, MBps'):
    fig = Figure(figsize=(16,6), dpi=80)
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(x, y, color='#337AB7')
    axis.fill_between(x,y, facecolor='#337AB7')
    axis.grid(True)
    axis.set_ylim(bottom=0)
    axis.set_ylabel(ylabel)
#    axis.set_xlabel('\n%s - %s' % (x[0],x[-1]))
    axis.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))
    axis.xaxis.set_major_locator(dates.HourLocator(byhour=range(0,24,1)))
    fig.autofmt_xdate()
    fig.set_facecolor('white')
    return fig

def smoothXY(x,y,frac = 0.025):
    x_unixtime = map(lambda k: time.mktime(k.timetuple()), x)
    xy_smooth = lowess(y, x_unixtime, frac = frac)
    y_smooth = xy_smooth[:,1]
    x_smooth = xy_smooth[:,0]
    return x_smooth,y_smooth

def makeImageResponseFromFigure(fig):
    canvas = FigureCanvas(fig)
    output = StringIO.StringIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response
