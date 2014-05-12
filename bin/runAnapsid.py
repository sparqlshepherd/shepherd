#!/usr/bin/env python
'''
Created on Jan 14, 2011
Script to execute Anapsid.
Use signal 12 to terminate the script and obtain the results until that moment

@maintainer: Simon Castillo
@author: Maribel Acosta
@author: Gabriela Montoya

Last modification: June, 2013.
'''

import getopt
import sys, os, signal
import string
from multiprocessing import Process, Queue, active_children, Manager
from time import time
from ANAPSID.Planner import Plan
from ANAPSID.Planner.Plan import contactSource, contactProxy
from ANAPSID.Decomposer import decomposer

def runQuery(query_file, endpoint_file, buffer_size, simulated, res,
             decomposition, p, oo, a, wc, k, endpointType):
    if simulated:
        contact = contactProxy
    else:
        contact = contactSource
    query = open(query_file).read()
    pos = string.rfind(query_file, "/")
    qu = query_file[pos+1:]
    pos2 = string.rfind(qu, ".")
    if pos2 > -1:
        qu = qu[:pos2]
    global qname
    global t1
    global tn
    global c1
    global cn
    global dt
    global pt
    c1 = 0
    cn = 0
    t1 = -1
    tn = -1
    dt = -1
    global time1
    qname = qu
    time1 = time()

    if oo: # if the query is in Sparql 1.1
       new_query = decomposer.makePlan2(query, p)
    else:
       new_query = decomposer.makePlan(query, endpoint_file, decomposition, p, contact)

    dt = time() - time1

    if (p == "d") or (k == "y"): # to show the decomposition or the plan
       print str(new_query)
       return
    elif (k == "c"): # to show the input for rdf3x
       print str(new_query.show2())
       return

    if (new_query == None): # if the query could not be answered by the endpoints
        time2 = time() - time1
        t1 = time2
        tn = time2
        pt= time2
        printInfo()
        return

    plan = Plan.createPlan(new_query, a, wc, buffer_size, contact, endpointType)

    pt = time() - time1
    #print 'creando procesos'
    p2 = Process(target=plan.execute, args=(res,))
    p2.start()
    p3 = Process(target=conclude, args=(res,p2))
    p3.start()
    signal.signal(12, onSignal1)

    while True:
        if not p2.is_alive() and p3.is_alive():
           try:
             os.kill(p3.pid, 9)
           except OSError as ex:
             continue
           break
        elif p2.is_alive() and not p3.is_alive():
           try:
             os.kill(p2.pid, 9)
           except Exception as ex:
             continue
           break
        elif not p2.is_alive() and not p3.is_alive():
           break

def conclude(res, p2):
    signal.signal(12, onSignal2)
    global t1
    global tn
    global c1
    global cn
    ri = res.get()

    if (ri == "EOF"):
       time2 = time() - time1
       t1 = time2
       tn = time2
       printInfo()
       return

    while (ri != "EOF"):

        cn = cn + 1
        if cn == 1:
            time2=time() - time1
            t1 = time2
            c1 = 1
        #time2 = time()
        #print time2 - time1, ri
        #print ri
        ri = res.get(True)
        #print ri
    printInfo()


def printInfo():
    global tn
    if tn == -1:
       tn = time() - time1
    print 'anapsid,%s,%f,%f,%d' % (qname, t1,tn, cn)
    # l = (qname + "\t" + str(dt) + "\t" + str(pt) + "\t" + str(t1) + "\t"
    #      + str(tn) + "\t" + str(c1) + "\t" + str(cn))
    # print l

def onSignal1(s, stackframe):
    #print 'entre en Signal1'
    cs = active_children()
    for c in cs:
      try:
        os.kill(c.pid, s)
      except OSError as ex:
        continue
    sys.exit(s)

def onSignal2(s, stackframe):
    printInfo()
    sys.exit(s)

def usage():
    usage_str = ("Usage: {program} -e <endpoints_file> -q <query_file> -b "
                 +"<buffer_size> -s <simulated> -p <plan> -o <sparql1.1> -d "
                 +"<decomposition> -a <adaptive> -k <special> "
                 +"-w <withoutCounts>\n where \n<simulated>, "
                 +"<adaptive> <sparql1.1> and <withoutCounts> is one in [True, "
                 +"False], \n<plan> is one in [b, ll, naive, d] (bushy plan, "
                 +"left linear plan, naive binary tree plan, only decompose), "
                 +"\n<decomposition> is one in [EG, SSGS, SSGM] (Exclusive "
                 +"Groups, Star Shaped Group Single Endpoint, Star Shaped "
                 +"Group Multiple Endpoints) and \n<special> is one in [y, c] "
                 +"(y is for showing the plan, and c is for decomposicion "
                 +"without using service operator, and using UNION to indicate "
                 +"joins.\n")
    print usage_str.format(program = sys.argv[0]),

def get_options(argv):
    try:
        opts, args = getopt.getopt(argv, "h:e:q:b:s:p:o:d:a:k:w:t:")
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    endpointfile = None
    queryfile = None
    buffersize = 16384
    simulated = True
    plan = "b"
    one_point_one = False
    decomposition = "SSGS"
    adaptive = True
    withoutCounts = False
    k = "n"
    endpointType = 'V'

    for opt, arg in opts:
        if opt == "-h":
            usage()
            sys.exit()
        elif opt == "-e":
            endpointfile = arg
        elif opt == "-q":
            queryfile = arg
        elif opt == "-b":
            buffersize = int(arg)
        elif opt == "-s":
            simulated = arg == "True"
        elif opt == "-d":
            decomposition = arg
        elif opt == "-p":
            plan = arg
        elif opt == "-k":
            k = arg
        elif opt == "-o":
            one_point_one = arg == "True"
        elif opt == "-a":
            adaptive = arg == "True"
        elif opt == "-w":
            withoutCounts = arg == "True"
        elif opt == '-t':
            endpointType = arg

    if (not endpointfile and not one_point_one) or not queryfile:
        usage()
        sys.exit(1)
    return (endpointfile, queryfile, buffersize, simulated,
            decomposition, plan, one_point_one, adaptive, withoutCounts, k, endpointType)

def main(argv):
    # manager = Manager()
    # res = manager.Queue()
    res = Queue()
    time1 = time()
    (endpoint, query, buffersize, simulated,
     decomposition, plan, oo, a, wc, k, endpointType)          = get_options(argv[1:])
    try:
       runQuery(query, endpoint, buffersize, simulated, res,
             decomposition, plan, oo, a, wc, k, endpointType)
    except Exception as ex:
       print ex

if __name__ == '__main__':
    main(sys.argv)
