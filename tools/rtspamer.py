# -*- coding: utf-8 -*-
from rtkit.resource import RTResource
from rtkit.authenticators import CookieAuthenticator
from getpass import getpass
from urllib2 import urlopen
from lxml import etree
import re

def createResource():
    user = raw_input('user: ')
    passwd = getpass('password: ')
    resource = RTResource('http://rt.ihome.ru/REST/1.0/', user, passwd, CookieAuthenticator)
    return resource

def getEMail(clientname):
    response = urlopen('http://ibase.ihome.ru/woolly/getmail.php?netname=%s' % clientname)
    tree = etree.parse(response)
    mail = tree.xpath('string(//email)')
    return mail

def createTicket(resource,mail,queue,subject):
    content = {
            'content': {
                'Requestor': mail,
                'Queue': queue,
                'Subject': subject
                }
            }
    response = resource.post(path='ticket/new', payload=content)
    ticketid = re.sub('.*\/','',response.parsed[0][0][1])
    return ticketid

def sendMail(resource,ticketid,piece):
    content = {
            'content': {
                'Action': 'correspond',
                'Text': """Здравствуйте.

Обратили внимание, что не все BGP сессии с вами подняты. Просьба поднять неактивные сессии.

%s

С уважением, Павел Поляков
NOC iHome | W-IX
+7 (495) 988-60-11""" % piece 
                }
            }
    response = resource.post(path='ticket/%s/comment' % ticketid, payload=content)
    print response

def createDict(source):
    clientstexts = source.split('\n\n')
    clients = []
    for text in clientstexts:
        client = {}
        clientname = re.search('[a-z]+',text).group(0)
        client['name'] = clientname
        client['text'] = text
        clients.append(client)
    for client in clients:
        mail = getEMail(client['name'])
        client['mail'] = mail
    return clients

if __name__ == "__main__":

    src = """193.106.112.37  sevencom    56889   1   8 days  Up  3/0
    193.106.112.37          2   8 days  Down    0/0

    193.106.112.82  attelecom   204128  1   10 days Down    0/0
    193.106.112.82          2   84 days Up  1/489189
    """

    WIX = '4'
    IHOME = '3'

    clients = createDict(src)
    for client in clients:
        ticketid = rt.createTicket(res,client['mail'],WIX,'%s | Поднятие BGP сессий' % client['name'])
        client['ticketid'] = ticketid

    for client in clients:
        rt.sendMail(res,client['ticketid'],client['text'])
