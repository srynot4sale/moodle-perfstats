#!/bin/python

import collections
import datetime
import os, os.path
import re
import sys

# Some constants
maxlines = 0
interesting = 30


# Total number of perf records
totallinecount = 0
pagecounts = {}

# Time of first/last perf record
earliestsecond = None
lastsecond = None

# Page processing time
pagetimespent = {}
totalpagetimespent = {}
totaltimespent = 0
peakprocessingtime = (0, '')

# Perf records per second
hitspersecond = {}
peakhits = 0

# Error recording
errorcounts = {}

# Bad record count
badrecords = 0



# Start
lineregex = re.compile(r'^\[(([0-9]+-[A-Za-z]+-2014) ([0-9:]{8}))\] (.*)$')
messageregex = re.compile(r'^PERF\: ([^ ]+) time: ([0-9\.]+)s memory_total: .*$')

dir = 'logs/'
for filename in os.listdir(dir):
    with open(os.path.join(dir, filename), 'r') as f:
        for line in f:
            if not len(line.strip()):
                continue

            try:
                res = lineregex.match(line)

                if res:
                    message = res.group(4)
                    perfline = messageregex.match(message)

                    if perfline:
                        second = res.group(1)
                        day  = res.group(2)
                        time = res.group(3)

                        url = perfline.group(1)
                        timespent = float(perfline.group(2))

                        # Sort out start/finish seconds in log
                        timestamp = datetime.datetime.strptime(second, "%d-%b-%Y %H:%M:%S")
                        if earliestsecond == None or earliestsecond > timestamp:
                            earliestsecond = timestamp
                        if lastsecond == None or lastsecond < timestamp:
                            lastsecond = timestamp

                        # Calculate hits/second
                        if second not in hitspersecond.keys():
                            hitspersecond[second] = 0
                        hitspersecond[second] += 1

                        if hitspersecond[second] > peakhits:
                            peakhits = hitspersecond[second]

                        # Calculate processing times
                        totaltimespent += timespent
                        if timespent > peakprocessingtime[0]:
                            peakprocessingtime = (timespent, url)

                        if url not in totalpagetimespent.keys():
                            totalpagetimespent[url] = 0
                        totalpagetimespent[url] += timespent

                        if url not in pagetimespent.keys():
                            pagetimespent[url] = 0
                        if timespent > pagetimespent[url]:
                            pagetimespent[url] = timespent

                        if url not in pagecounts.keys():
                            pagecounts[url] = 0
                        pagecounts[url] += 1
                    else:
                        if message not in errorcounts.keys():
                            errorcounts[message] = 0
                        errorcounts[message] += 1
                        continue
                else:
                    badrecords += 1
                    continue

            except:
                print("Unexpected error:", sys.exc_info()[0])
                print(line)
                continue

            totallinecount += 1
            if maxlines and totallinecount >= maxlines:
                break


seconds = lastsecond - earliestsecond
averagehitspersecond = float(totallinecount) / seconds.total_seconds()
averagetimespent = totaltimespent / totallinecount

print("Total line count: %d" % totallinecount)
print("Total bad records: %d" % badrecords)
print()
print("Average hits/second: %f" % averagehitspersecond)
print("Peak hits/second: %d" % peakhits)
print()
print("Average processing time: %fs" % averagetimespent)
print("Peak processing time: %fs (%s)" % (peakprocessingtime[0], peakprocessingtime[1]))
print()
print("Unique URLs: %d" % len(pagetimespent))

print()
print("Busiest seconds")
d = collections.Counter(hitspersecond)
for k, v in d.most_common(15):
    print ('%d:\t%s' % (v, k))

print()
print("Most common errors")
d = collections.Counter(errorcounts)
for k, v in d.most_common(15):
    print ('%d:\t%s' % (v, k))

print()
print("Slowest pages (url, maxtime, visit count, % of time spent processing)")
d = collections.Counter(pagetimespent)
for k, v in d.most_common(15):
    percent = (totalpagetimespent[k] / totaltimespent) * 100
    print ('%s:\t%f\t%d\t%f%%' % (k, v, pagecounts[k], percent))
