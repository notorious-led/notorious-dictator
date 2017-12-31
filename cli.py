import json
import readchar
import sys
import datetime
import requests
import numpy
import socket
import select
from time import sleep

ping_count = 100

def ping(endpoint):
    if endpoint['type'] == 'hoopla':
        url = "http://" + endpoint["location"] + "/sync/ping"
        time = datetime.datetime.now()
        requests.get(url) #and throw it in the garbage
        time = datetime.datetime.now() - time
        return(time.total_seconds() * 1000)
    elif endpoint['type'] == 'glowup-over-tcp':
        sleep(0.05)

        host = endpoint["location"].split(':')[0]
        port = int(endpoint["location"].split(':')[1])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.setblocking(0)

        time = datetime.datetime.now()
        ready = select.select([sock], [], [], 5)
        sock.send(bytes('m\r\n', 'ascii'))
        if ready[0]:
            data = sock.recv(4096)
        sock.close()

        if bytes('*************', 'ascii') in data:
            time = datetime.datetime.now() - time
            return(time.total_seconds() * 1000)
        else:
            return 250
    else:
        raise NotImplementedError

def calibrate(endpoint):
    ping(endpoint) #Throw away one ping. It could be delayed due to DNS/ARP resolution or some other reason
    pings = []
    for _ in range(ping_count):
        pings.append(ping(endpoint))

    #reject outliers.
    stdev = numpy.std(pings)
    mean = numpy.mean(pings)
    pings2 = [p for p in pings if p > mean-stdev and p < mean+stdev]
    return numpy.median(pings2)

def send_rtt(endpoint):
    if endpoint['type'] == 'hoopla':
        url = "http://" + endpoint["location"] + "/sync/rtt"
        requests.post(url, data = { 'rtt': str(endpoint["rtt"]) })
    elif endpoint['type'] == 'glowup-over-tcp':
        host = endpoint["location"].split(':')[0]
        port = int(endpoint["location"].split(':')[1])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.send(bytes('rtt ' + str(endpoint['rtt']) + '\r\n', 'ascii'))
        sock.close()
    else:
        raise NotImplementedError

if __name__ == '__main__':

    endpoints = []
    with open("endpoints.json", 'r') as f:
        endpoints = json.load(f)
    print("Loaded endpoints:", [e["name"] for e in endpoints])
    
    while True:
        sys.stdout.write("\nCommands: Calibrate, Ping, Send, 0-9 (immediate) > ")
        sys.stdout.flush()
    
        ch = readchar.readkey()[0]
        print(ch)
    
        if ord(ch) < 5:
            print("Bye")
            sys.exit(0)
        elif ch.lower() == 'c':
            for endpoint in endpoints:
                sys.stdout.write("Calibrating " + endpoint["name"] + ": ")
                sys.stdout.flush()
                endpoint["rtt"] = calibrate(endpoint)
                sys.stdout.write(str(endpoint["rtt"]) + ", sending: ")
                sys.stdout.flush()
                send_rtt(endpoint)
                sys.stdout.write("done.\n")
        elif ch.lower() == 'p':
            for endpoint in endpoints:
                sys.stdout.write("Ping " + endpoint["name"] + ": ")
                sys.stdout.flush()
                print(ping(endpoint))
        elif ch.lower() == 's':
            thing = input("Send what? ")
            for endpoint in endpoints:
                host = endpoint["location"].split(':')[0]
                port = int(endpoint["location"].split(':')[1])
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((host, port))
                sock.send(bytes(thing + '\r\n', 'ascii'))
                sock.close()
                
