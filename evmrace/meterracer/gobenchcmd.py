#!/usr/bin/python

import re
import subprocess
import nanodurationpy as durationpy
import os
import shutil
import shlex


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



def do_go_bench_cmd(go_bench_cmd, go_dir):
    go_cmd = shlex.split(go_bench_cmd)
    print("running go precompile benchmark...\n{}".format(go_bench_cmd))

    raw_stdoutlines = []
    with subprocess.Popen(go_cmd, cwd=go_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout: # b'\n'-separated lines
            print(line, end='')
            raw_stdoutlines.append(line)  # pass bytes as is
        p.wait()

    print("process finished.")
    return raw_stdoutlines


# parsing code from https://github.com/ethereum/benchmarking/blob/master/constantinople/scripts/postprocess_geth_v2.py
def parse_go_bench_output(stdoutlines, name_suffix="no-metering"):
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
    gas_used = -1
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

        if int(nanosecs) > 0 and int(gas_used) >= 0 and test_name != "":
            bench_time = durationpy.from_str("{}ns".format(nanosecs))
            bench_tests.append({'name': "{}-{}".format(test_name, name_suffix), 'gas': gas_used, 'time': bench_time.total_seconds()})
            print("parsed test result:", bench_tests[-1])
            gas_used = -1
            nanosecs = 0
            test_name = ""

    return bench_tests


def do_go_precompile_bench(go_dir, bench_name, name_suffix):
    go_bench_cmd = "go test -timeout 1800s -bench {} -benchtime 7s".format(bench_name)
    bench_output = do_go_bench_cmd(go_bench_cmd, go_dir)
    bench_results = parse_go_bench_output(bench_output, name_suffix=name_suffix)
    return bench_results

