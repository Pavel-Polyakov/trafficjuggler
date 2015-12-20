from flask import Flask, render_template, request
from mpls import *

def formattedRoute(route):
    match = re.compile('(?<=\.\d\d$)')
    route = " - ".join(match.sub(' ', str(x)) for x in route)
    return route  

def convertToGbps(value):
    return str(round(float(value)/1000,2))+"Gbps"


app = Flask(__name__)

@app.route('/')
def index():
    host.parse(executor,zapi)
#    host = loaditems('m9-r0')
    
    interfaces = [x.__dict__ for x in host.intlist.sortByOutput()]
    for interface in interfaces:
        speed = re.sub('Gbps','000',interface['speed'])
        output = interface['output']                           
        try: utilization = int(round(output/float(speed)*100,2))
        except Exception: utilization = 0
        output = convertToGbps(output)

        interface['output'] = output
        interface['utilization'] = utilization 
        interface['lsplist'] = [x.__dict__ for x in host.lsplist.getLSPByInterface(interface['name']).sortByOutput()]
      
        for lsp in interface['lsplist']:
            lsp['path'] = formattedRoute(lsp['path'])
            if lsp['output'] != 'None' and lsp['output'] != 'Down':
                lsp['output'] = convertToGbps(lsp['output'])

    return render_template('index.html', interfaces=interfaces)

if __name__ == '__main__':
    HOST = 'm9-r0'
    zapi = getZApi()
    executor = mExecutor(HOST)
    host = mRouter(HOST)
    app.run(
        host = "0.0.0.0",
        debug = True
    )


