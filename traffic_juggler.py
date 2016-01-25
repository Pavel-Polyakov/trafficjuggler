from flask import Flask, render_template, request
from mpls import *

def formattedRoute(route):
    match = re.compile('(?<=\.\d\d$)')
    route = " - ".join(match.sub(' ', str(x)) for x in route)
    return route

def convertToGbps(value):
    return str(round(float(value)/1000,2))+"Gbps"

def resolveHost(value,neigbors):
    ip = re.sub('to ','',value)
    if ip in [x['ip'] for x in neigbors]:
        description = next(x['description'] for x in neigbors if x['ip']==ip)
    return re.sub(ip,description,value)

app = Flask(__name__)

@app.route('/')
def index():
#    router.parse(executor,zapi)
    router = loaditems('m9-r0')

    hosts = [{'ip': x} for x in router.lsplist.getAllHostsSortedByOutput()]
    for host in hosts:
        host['name'] = next(x['description'] for x in router.neighbors if x['ip'] == host['ip'])
        host['sumbandwidth'] = str(router.lsplist.getLSPByHost(host['ip']).getSumBandwidth())+'m'
        host['lsplist'] = [x.__dict__ for x in router.lsplist.getLSPByHost(host['ip']).sortByOutput()]
        host['sumoutput'] = convertToGbps(router.lsplist.getLSPByHost(host['ip']).getSumOutput())
        host['rbandwidth'] = str(router.lsplist.getAverageRBandwidthByHost(host['ip']))+"m"

    interfaces = [x.__dict__ for x in router.intlist.sortByOutput()]
    for interface in interfaces:
        speed = re.sub('Gbps','000',interface['speed'])
        output = interface['output']
        #TODO: move get of utilization to object
        try: utilization = int(round(output/float(speed)*100,2))
        except Exception: utilization = 0
        output = convertToGbps(output)
        interface['output'] = output
        interface['utilization'] = utilization
        interface['lsplist'] = [x.__dict__ for x in router.lsplist.getLSPByInterface(interface['name']).sortByOutput()]

    #I don't understand why it works, but for now I left it here
    for lsp in [x.__dict__ for x in router.lsplist]:
        lsp['path'] = formattedRoute(lsp['path'])
        if lsp['output'] != 'None' and lsp['output'] != 'Down':
            lsp['output'] = convertToGbps(lsp['output'])
        lsp['to'] = resolveHost(lsp['to'],router.neighbors)




    return render_template('index.html', interfaces=interfaces, hosts=hosts)

if __name__ == '__main__':
    HOST = 'm9-r0'
#    zapi = getZApi()
#    executor = mExecutor(HOST)
#    router = mRouter(HOST)
    app.run(
        host = "127.0.0.1",
        debug = True
    )
