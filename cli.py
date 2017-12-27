import json
import readchar
import sys
import datetime
import requests
import numpy

ping_count = 100

def ping(endpoint):
    if endpoint['type'] == 'hoopla':
        url = "http://" + endpoint["location"] + "/sync/ping"
        time = datetime.datetime.now()
        requests.get(url) #and throw it in the garbage
        time = datetime.datetime.now() - time
        return(time.total_seconds() * 1000)
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
    else:
        raise NotImplementedError

if __name__ == '__main__':

    endpoints = []
    with open("endpoints.json", 'r') as f:
        endpoints = json.load(f)
    print("Loaded endpoints:", [e["name"] for e in endpoints])
    
    while True:
        sys.stdout.write("\nCommands: Calibrate, Ping, Schedule, 0-9 (immediate) > ")
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
