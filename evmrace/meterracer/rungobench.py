#!/usr/bin/python

import re
import subprocess
import nanodurationpy as durationpy
import csv
import time, datetime
import os
import shutil
import shlex

import prepgocode

# output paths should be mounted docker volumes
RESULT_CSV_OUTPUT_PATH = "/evmraceresults"

RESULT_CSV_FILENAME = "metering_precompile_benchmarks.csv"

GO_DIR = "/go-ethereum/core/vm/"




# go test -bench BenchmarkPrecompiledSha256 -benchtime 5s

# mv /meterracer/wasm_to_meter/*.go /meterracer/gofiles

# move .go files to go-ethereum directory
# mv ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go.backup
# cp /meterracer/gofiles/ewasm_precompile_ecadd.go ~/go/src/github.com/ethereum/go-ethereum/core/vm/

# mv ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go.backup


# cd ~/go/src/github.com/ethereum/go-ethereum/core/vm/
# go test -bench BenchmarkPrecompiledBn256Add -benchtime 5s

# mv ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go.backup ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go

"""
~/go/src/github.com/ethereum/go-ethereum/core/vm# go test -bench BenchmarkPrecompiledBn256Add -benchtime 5s
gas used: 612825
goos: linux
goarch: amd64
pkg: github.com/ethereum/go-ethereum/core/vm
BenchmarkPrecompiledBn256Add/chfast1-Gas=100000000-4            gas used: 349548
gas used: 349548
    1000           8031406 ns/op
gas used: 356404
BenchmarkPrecompiledBn256Add/chfast2-Gas=100000000-4            gas used: 356404
gas used: 356404
    1000           8251335 ns/op
gas used: 23435
BenchmarkPrecompiledBn256Add/cdetrio1-Gas=100000000-4           gas used: 23435
gas used: 23435
gas used: 23435
   20000            328686 ns/op
gas used: 23147
BenchmarkPrecompiledBn256Add/cdetrio2-Gas=100000000-4           gas used: 23147
gas used: 23147
gas used: 23147
   20000            326049 ns/op
gas used: 23314
BenchmarkPrecompiledBn256Add/cdetrio3-Gas=100000000-4           gas used: 23314
gas used: 23314
gas used: 23314
   20000            326394 ns/op
gas used: 21482
BenchmarkPrecompiledBn256Add/cdetrio4-Gas=100000000-4           gas used: 21482
gas used: 21482
gas used: 21482
   30000            285278 ns/op
gas used: 23435
BenchmarkPrecompiledBn256Add/cdetrio5-Gas=100000000-4           gas used: 23435
gas used: 23435
gas used: 23435
   20000            328430 ns/op
gas used: 48819
BenchmarkPrecompiledBn256Add/cdetrio6-Gas=100000000-4           gas used: 48819
gas used: 48819
   10000            915570 ns/op
gas used: 48819
BenchmarkPrecompiledBn256Add/cdetrio7-Gas=100000000-4           gas used: 48819
gas used: 48819
   10000            915399 ns/op
gas used: 48531
BenchmarkPrecompiledBn256Add/cdetrio8-Gas=100000000-4           gas used: 48531
gas used: 48531
   10000            900366 ns/op
gas used: 48819
BenchmarkPrecompiledBn256Add/cdetrio9-Gas=100000000-4           gas used: 48819
gas used: 48819
   10000            989002 ns/op
gas used: 48819
BenchmarkPrecompiledBn256Add/cdetrio10-Gas=100000000-4          gas used: 48819
gas used: 48819
   10000            928105 ns/op
gas used: 395494
BenchmarkPrecompiledBn256Add/cdetrio11-Gas=100000000-4          gas used: 395494
gas used: 395494
    1000           9184894 ns/op
gas used: 395494
BenchmarkPrecompiledBn256Add/cdetrio12-Gas=100000000-4          gas used: 395494
gas used: 395494
    1000           9657306 ns/op
gas used: 353550
BenchmarkPrecompiledBn256Add/cdetrio13-Gas=100000000-4          gas used: 353550
gas used: 353550
    1000           8900280 ns/op
gas used: 103803
BenchmarkPrecompiledBn256Add/cdetrio14-Gas=100000000-4          gas used: 103803
gas used: 103803
    3000           2247486 ns/op
PASS
ok      github.com/ethereum/go-ethereum/core/vm 155.573s
"""


GO_BENCHES = [
  'BenchmarkPrecompiledSha256',
  'BenchmarkPrecompiledBn256Add',
  'BenchmarkPrecompiledBn256ScalarMul',
  'BenchmarkPrecompiledBn256Pairing',
  # BenchmarkPrecompiledModExp
  # BenchmarkPrecompiledEcrecover
]



EWASM_PRECOMPILE_DEFS = [
  {
    "wasmfile": "ewasm_precompile_sha256.wasm.metered",
    "varname": "ewasmSha256HashCode",
    "gofile": "ewasm_precompile_sha256.go"
  },
  {
    "wasmfile": "ewasm_precompile_ecadd.wasm.metered",
    "varname": "ewasmEcaddCode",
    "gofile": "ewasm_precompile_ecadd.go"
  },
  {
    "wasmfile": "ewasm_precompile_ecmul.wasm.metered",
    "varname": "ewasmEcmulCode",
    "gofile": "ewasm_precompile_ecmul.go"
  },
  {
    "wasmfile": "ewasm_precompile_ecpairing.wasm.metered",
    "varname": "ewasmEcpairingCode",
    "gofile": "ewasm_precompile_ecpairing.go"
  }
#  {
#    "wasmfile": "ewasm_precompile_ecrecover.wasm.metered",
#    "varname": "ewasmEcrecoverCode",
#    "gofile": "ewasm_precompile_ecrecover.go"
#  },
#  {
#    "wasmfile": "ewasm_precompile_expmod.wasm.metered",
#    "varname": "ewasmExpmodCode",
#    "gofile": "ewasm_precompile_expmod.go"
#  }
]


GO_VM_PATH = "/go-ethereum/core/vm/"

WASM_FILE_DIR = "/meterracer/wasm_to_meter/"

def prepare_ewasm_go_file(go_bench_name, metered=False):
    precdef = EWASM_PRECOMPILE_DEFS[GO_BENCHES.index(go_bench_name)]

    wasmfile = precdef['wasmfile']
    varname = precdef['varname']
    gofile = precdef['gofile']
    if metered is True:
        wasmfile = wasmfile
    if metered is False:
        wasmfile = precdef['wasmfile'].replace(".metered", "")
    print("prepared ewasm go file with wasmfile:", wasmfile)
    prepgocode.prepare_go_file(wasmfiledir=WASM_FILE_DIR, wasmfile=wasmfile, varname=varname, gofile=gofile)
    return gofile


def do_go_precompile_bench(go_bench_cmd):
    go_cmd = shlex.split(go_bench_cmd)
    print("running go precompile benchmarks...\n{}".format(go_bench_cmd))

    raw_stdoutlines = []
    with subprocess.Popen(go_cmd, cwd=GO_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout: # b'\n'-separated lines
            print(line, end='')
            raw_stdoutlines.append(line)  # pass bytes as is
        p.wait()

    #stdoutlines = [line.decode('utf8') for line in raw_stdoutlines]
    # line.decode('utf8') crashes python.  AttributeError: 'str' object has no attribute 'decode'
    print("process finished.")
    return raw_stdoutlines


# parsing code from https://github.com/ethereum/benchmarking/blob/master/constantinople/scripts/postprocess_geth_v2.py
def parse_go_bench_output(stdoutlines, ismetered="unmetered"):
    #benchRegex = "Benchmark(Precompiled.*)-Gas=([\d]+)\S+\s+\d+\s+([\d\.]+) ns\/op"
    benchRegex = "Benchmark(Precompiled.*)-Gas=([\d]+)"
    #opRegexp = re.compile("Benchmark(Op.*)\S+\s+\d+\s+([\d\.]+) ns\/op") 
    nsOpRegex = "\d+\s+([\d\.]+) ns\/op"
    gasRegex = "gas used: ([\d]+)"

    # first match test name
    # then match gas used
    # then match ns/op, then append result and wait for next test name
    bench_tests = []
    test_name = ""
    gas_used = 0
    nanosecs = 0
    for line in stdoutlines:
        matchName = re.search(benchRegex, line)
        if matchName:
            test_name = matchName.group(1)
            nanosecs = 0

        matchGas = re.search(gasRegex, line)
        if matchGas:
            gas_used = matchGas.group(1)

        matchNanos = re.search(nsOpRegex, line)
        if matchNanos:
            nanosecs = matchNanos.group(1)

        if int(nanosecs) > 0 and int(gas_used) > 0 and test_name != "":
            bench_time = durationpy.from_str("{}ns".format(nanosecs))
            bench_tests.append({'name': "{}-{}".format(test_name, ismetered), 'gas': gas_used, 'time': bench_time.total_seconds()})
            print("parsed test result:", bench_tests[-1])
            gas_used = 0
            nanosecs = 0
            test_name = ""

    return bench_tests


def saveResults(precompile_benchmarks):
    # move existing csv file to backup-datetime-folder
    ts = time.time()
    date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    ts_folder_name = "backup-{}-{}".format(date_str, round(ts))
    dest_backup_path = os.path.join(RESULT_CSV_OUTPUT_PATH, ts_folder_name)
    result_file = os.path.join(RESULT_CSV_OUTPUT_PATH, RESULT_CSV_FILENAME)

    # back up existing result csv file
    if os.path.isfile(result_file):
        os.makedirs(dest_backup_path)
        shutil.move(result_file, dest_backup_path)
        print("existing {} moved to {}".format(RESULT_CSV_FILENAME, dest_backup_path))

    with open(result_file, 'w', newline='') as bench_result_file:
        fieldnames = ['test_name', 'gas', 'time']
        writer = csv.DictWriter(bench_result_file, fieldnames=fieldnames)
        writer.writeheader()
        for test_result in precompile_benchmarks:
            writer.writerow({"test_name" : test_result['name'], "gas" : test_result['gas'], "time" : test_result['time']})


def main():

    all_bench_results = []
    for bench_name in GO_BENCHES:
        bench_name_results = []
        print("benching unmetered and metered {}".format(bench_name))
        go_bench_cmd = "go test -timeout 1800s -bench {} -benchtime 2s".format(bench_name)
        # first benchmark unmetered wasm code
        print("doing unmetered first...")
        gofile = prepare_ewasm_go_file(bench_name, metered=False)
        gofilesrcpath = os.path.join(WASM_FILE_DIR, gofile)
        gofiledestpath = os.path.join(GO_VM_PATH, gofile)
        if os.path.isfile(gofiledestpath):
            os.remove(gofiledestpath)
        shutil.move(gofilesrcpath, GO_VM_PATH)
        unmetered_bench_output = do_go_precompile_bench(go_bench_cmd)
        unmetered_bench_results = parse_go_bench_output(unmetered_bench_output, ismetered="unmetered")
        #print("got unmetered precompile benchmarks:", unmetered_bench_results)

        # then benchmark metered wasm code
        print("now doing metered...")
        gofile = prepare_ewasm_go_file(bench_name, metered=True)
        gofilesrcpath = os.path.join(WASM_FILE_DIR, gofile)
        gofiledestpath = os.path.join(GO_VM_PATH, gofile)
        if os.path.isfile(gofiledestpath):
            os.remove(gofiledestpath)
        shutil.move(gofilesrcpath, GO_VM_PATH)
        metered_bench_output = do_go_precompile_bench(go_bench_cmd)
        metered_bench_results = parse_go_bench_output(metered_bench_output, ismetered="metered")
        #print("got metered precompile benchmarks:", metered_bench_results)

        bench_name_results = unmetered_bench_results + metered_bench_results
        #print("bench_name_results:", bench_name_results)
        all_bench_results.extend(bench_name_results)

    saveResults(all_bench_results)
    print("all_bench_results:", all_bench_results)

if __name__ == "__main__":
    main()
