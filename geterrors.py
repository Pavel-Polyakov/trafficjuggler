from jnpr.junos import Device
from getpass import getpass
import re
import sys

def connect():
    host = raw_input('host: ')
    user = raw_input('username: ')
    passwd = getpass('password: ')
    dev = Device(host, user=user, passwd=passwd)
    try:
        print
        dev.open()
        print "Connected to %s (%s : JUNOS  %s)" % (dev.facts['hostname'], dev.facts['model'], dev.facts['version'])
        print
        return dev
    except Exception:
        print 'Does not connected. Please check your input'
        sys.exit()

def disconnect(dev):
    print
    dev.close()
    print "Disconnected"

def removeN(s):
    return re.sub('\n', '', s)

def getInterfaces(dev):
    interfaces = []
    interfacesComm = dev.display_xml_rpc('show interfaces extensive', format='xml')
    res = dev.execute(interfacesComm)
    pi = res.findall('physical-interface')
    for p in pi:
        interfaces.append(p)
        if p.findall('logical-interface'):
            for l in p.findall('logical-interface'):
                interfaces.append(l)
    return interfaces

def getInterfacesInfo(interfaces):
    info = []
    for port in interfaces:
        try:    name = removeN(port.find('name').text)
        except AttributeError:  name = 'wtf?'
        try:    status = removeN(port.find('oper-status').text)
        except AttributeError:  status = '-'
        try:    desc = removeN(port.find('description').text)
        except AttributeError:  desc = '-'
        try:    errs = removeN(port.find('input-error-list').find('input-errors').text)
        except AttributeError:  errs = '-'
        info.append({'name': name, 'status': status, 'description': desc, 'input-errors': errs})
    return info

def printResult(ports):
    out = '{0:<16s}\t{1:<6s}\t{2:<20s}\t{3:>12s}'
    print out.format('Interface', 'Link', 'Description', 'Input-errors')
    for port in ports:
        try:
            print out.format(port['name'], port['status'], port['description'], port['input-errors'])
        except Exception:
            pass

dev = connect()
interfaces = getInterfaces(dev)
interfacesInfo = getInterfacesInfo(interfaces)
printResult(interfacesInfo)
disconnect(dev)
