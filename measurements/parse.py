#!/usr/bin/env python3

import sys
import requests
from ripe.atlas.sagan import DnsResult
import datetime

import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt

if len(sys.argv) < 2:
    print('Usage: parse.py MEASUREMENT_ID')
    sys.exit(1)

source = "https://atlas.ripe.net/api/v2/measurements/%s/results" % sys.argv[1]
response = requests.get(source).json()

results_by_probe = {}

for result in response:
    parsed_result = DnsResult(result)
    if parsed_result.responses[0].abuf is None:
        continue
    if parsed_result.responses[0].abuf.header.return_code != "NOERROR":
        continue
    pid = parsed_result.probe_id
    if pid not in results_by_probe:
        results_by_probe[pid] = {'x': [], 'y': []}

    results_by_probe[pid]['x'].append(datetime.datetime.fromtimestamp(parsed_result.created_timestamp))
    results_by_probe[pid]['y'].append(datetime.datetime.fromtimestamp(parsed_result.responses[0].abuf.answers[0].serial))

fig1 = plt.figure(figsize=(16,12))
for key, value in results_by_probe.items():
    #plt.scatter(value['x'], value['y'], label=key)
    plt.plot(value['x'], value['y'], label=key, marker='o')

plt.gcf().autofmt_xdate()
plt.xlabel('Time of measurement')
plt.ylabel('Time of SOA serial')
plt.legend()

fig1.savefig('%s.svg' % sys.argv[1], bbox_inches='tight')
fig1.savefig('%s.png' % sys.argv[1], bbox_inches='tight')

fig2 = plt.figure(figsize=(15,100))

probe_results = {}
i = 1
for res in response:
    res = DnsResult(res)
    if res.responses[0].abuf is None:
        continue
    if res.responses[0].abuf.header.return_code != "NOERROR":
        continue
    for val in res.responses:
        k = str(res.probe_id) + '-' + val.destination_address
        if k not in probe_results:
            probe_results[k] = {'x': [], 'y': [], 'diff': []}
            i += 1
        if val.abuf != None and len(val.abuf.answers) > 0:
            probe_results[k]['x'].append(datetime.datetime.fromtimestamp(res.created_timestamp))
            probe_results[k]['y'].append(datetime.datetime.fromtimestamp(val.abuf.answers[0].serial))
            probe_results[k]['diff'].append(int(val.abuf.answers[0].serial) - int(res.created_timestamp))

v = 1
for key, value in probe_results.items():
    v += 1
    plt.subplot(i, 1, v)
    plt.plot(value['x'], value['y'], label=key, marker='o')
    plt.gcf().autofmt_xdate()
    plt.xlabel('Time of measurement')
    plt.ylabel('Time of SOA serial')
    plt.legend()

fig2.savefig('%s-2.svg' % sys.argv[1], bbox_inches='tight')
fig2.savefig('%s-2.png' % sys.argv[1], bbox_inches='tight')

fig3 = plt.figure(figsize=(16,12))
v = 1
plots = []
labels = []
for key, value in probe_results.items():
    v += 1
    #plt.subplot(i, 1, v)
    #plt.stem(value['x'], value['diff'])
    plots.append(value['diff'])
    labels.append(key)
plt.boxplot(plots)
ax = plt.gca()
ax.set_xticklabels(labels)
plt.xticks(rotation=90)
#plt.yticks(list(plt.yticks()[0]) + [-86400])
plt.yticks([0, -20000, -40000, -60000, -80000, -86400])

fig3.savefig('%s-3.svg' % sys.argv[1], bbox_inches='tight')
fig3.savefig('%s-3.png' % sys.argv[1], bbox_inches='tight')
