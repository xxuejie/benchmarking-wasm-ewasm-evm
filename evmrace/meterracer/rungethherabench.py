#!/usr/bin/python

import os
import shutil
import shlex
import csv
import time, datetime
import json
import re
import subprocess
import nanodurationpy as durationpy

import argparse, sys

parser = argparse.ArgumentParser()
# hyphens in argument name are converted to underscores
parser.add_argument('--testsuffix', help='suffix for benchmark test case name')
parser.add_argument('--wasmfile', help='full path of wasm file to benchmark')
parser.add_argument('--testvectors', help='full path of json file with test vectors')
parser.add_argument('--csvfile', help='full path of csv file to save results')
args = vars(parser.parse_args())

GO_VM_PATH = "/root/go/src/github.com/ethereum/go-ethereum"

HERA_ENGINES = ['wabt', 'binaryen', 'wavm']

#TEST_TIMES = {
#  ''
#}

# go test -v ./core/vm/runtime/... -bench BenchmarkCallEwasm --vm.ewasm="/root/hera/build/src/libhera.so,benchmark=true,engine=wabt" --ewasmfile="/meterracer/wasm_to_meter/ewasm_precompile_ecmul_unmetered.wasm" --input="070a8d6a982153cae4be29d434e8faef8a47b274a053f5a4ee2a6c9c13c31e5c031b8ce914eba3a9ffb989f9cdd5b0f01943074bf4f0f315690ec3cec6981afc30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd46" --expected="025a6f4181d2b4ea8b724290ffb40156eb0adb514c688556eb79cdea0752c2bb2eff3f31dea215f1eb86023a133a996eb6300b44da664d64251d05381bb8a02e" 


def saveResults(benchmark_results, result_file):

  # should engine be concatenated into the test_name?  no - engine should be a different column
  # instantiate_time is name for compile time or parse/decode time
  fieldnames = ['engine', 'test_name', 'total_time', 'compile_time', 'exec_time']

  if not os.path.isfile(result_file):
    # write header if new file
    with open(result_file, 'w', newline='') as bench_result_file:
      writer = csv.DictWriter(bench_result_file, fieldnames=fieldnames)
      writer.writeheader()

  # append to existing file
  with open(result_file, 'a', newline='') as bench_result_file:
    writer = csv.DictWriter(bench_result_file, fieldnames=fieldnames)
    for test_result in benchmark_results:
      writer.writerow({
                        "engine": test_result['engine'],
                        "test_name" : test_result['test_name'],
                        #"gas" : test_result['gas'],
                        "total_time" : test_result['total_time'],
                        "compile_time": test_result['compile_time'],
                        "exec_time": test_result['exec_time']
                      })


"""
~/go/src/github.com/ethereum/go-ethereum# go test -v ./core/vm/runtime/... -bench BenchmarkCallEwasm --vm.ewasm="/root/hera/build/src/libhera.so,benchmark=true,engine=wabt" --ewasmfile="/meterracer/wasm_to_meter/ewasm_precompile_ecmul_unmetered.wasm" --input="070a8d6a982153cae4be29d434e8faef8a47b274a053f5a4ee2a6c9c13c31e5c031b8ce914eba3a9ffb989f9cdd5b0f01943074bf4f0f315690ec3cec6981afc30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd46" --expected="025a6f4181d2b4ea8b724290ffb40156eb0adb514c688556eb79cdea0752c2bb2eff3f31dea215f1eb86023a133a996eb6300b44da664d64251d05381bb8a02e"
=== RUN   TestDefaults
--- PASS: TestDefaults (0.00s)
=== RUN   TestEVM
--- PASS: TestEVM (0.00s)
--- PASS: TestExecute (0.00s)
=== RUN   TestCall
--- PASS: TestCall (0.00s)
=== RUN   ExampleExecute
--- PASS: ExampleExecute (0.00s)
ewasmfile: /meterracer/wasm_to_meter/ewasm_precompile_ecmul_unmetered.wasm
evmc/bindings/go/evmc/evmc.go Load...
doing evmc_load..
assuming got handle to main program...
case C.EVMC_LOADER_SUCCESS
called C.evmc_create_hera_wrapper...
have instance...
returning instance...
Time [us]: 52262 = 4467 + 47794
got return bytes: 025a6f4181d2b4ea8b724290ffb40156eb0adb514c688556eb79cdea0752c2bb2eff3f31dea215f1eb86023a133a996eb6300b44da664d64251d05381bb8a02e
goos: linux
goarch: amd64
pkg: github.com/ethereum/go-ethereum/core/vm/runtime
BenchmarkCallEwasm-4    ewasmfile: /meterracer/wasm_to_meter/ewasm_precompile_ecmul_unmetered.wasm
Time [us]: 46845 = 2335 + 44509
Time [us]: 47053 = 2695 + 44358
Time [us]: 50477 = 2607 + 47870
Time [us]: 46749 = 2475 + 44274
Time [us]: 48535 = 2160 + 46375
Time [us]: 48005 = 3192 + 44813
Time [us]: 45550 = 2021 + 43529
Time [us]: 48307 = 2147 + 46159
Time [us]: 47698 = 2429 + 45269
Time [us]: 47538 = 2258 + 45280
Time [us]: 57195 = 2449 + 54746
Time [us]: 48642 = 2449 + 46193
Time [us]: 51318 = 2311 + 49007
Time [us]: 48854 = 2148 + 46706
Time [us]: 47330 = 2387 + 44942
Time [us]: 48032 = 2300 + 45732
Time [us]: 46139 = 2563 + 43576
Time [us]: 47659 = 2423 + 45235
Time [us]: 46701 = 2635 + 44066
Time [us]: 45779 = 2382 + 43396
Time [us]: 46179 = 2373 + 43805
Time [us]: 45666 = 2076 + 43589
Time [us]: 47696 = 2019 + 45677
Time [us]: 52181 = 2117 + 50064
Time [us]: 51554 = 2352 + 49201
Time [us]: 47319 = 2227 + 45092
Time [us]: 46048 = 2094 + 43954
Time [us]: 53341 = 2279 + 51062
Time [us]: 49082 = 2778 + 46304
Time [us]: 50262 = 2199 + 48063
got return bytes: 025a6f4181d2b4ea8b724290ffb40156eb0adb514c688556eb79cdea0752c2bb2eff3f31dea215f1eb86023a133a996eb6300b44da664d64251d05381bb8a02e
      30          48629905 ns/op
PASS
ok      github.com/ethereum/go-ethereum/core/vm/runtime 1.567s
"""


# parsing code from https://github.com/ethereum/benchmarking/blob/master/constantinople/scripts/postprocess_geth_v2.py
def parse_go_bench_output(stdoutlines, testname):
  print("parsing go bench output for {}".format(testname))
  benchRegex = "Time \[us\]: (\d+) = (\d+) \+ (\d+)"

  # we dont care about the nsop except as an averaged total
  # might be good to double check and compare against average total printed by hera
  #nsOpRegex = "\d+\s+([\d\.]+) ns\/op"
  #gasRegex = "gas used: ([\d]+)"

  # FIXME: check for FAIL and skip test

  bench_tests = []
  for line in stdoutlines:
    matchTimes = re.search(benchRegex, line)
    if matchTimes:
      total_time = matchTimes.group(1)
      compile_time = matchTimes.group(2)
      exec_time = matchTimes.group(3)

      total_time = durationpy.from_str("{}us".format(total_time))
      compile_time = durationpy.from_str("{}us".format(compile_time))
      exec_time = durationpy.from_str("{}us".format(exec_time))

      bench_run = {
        'total_time': total_time.total_seconds(),
        'compile_time': compile_time.total_seconds(),
        'exec_time': exec_time.total_seconds()
      }
      bench_tests.append(bench_run)

  print("parsed bench results:", bench_tests)
  return bench_tests


def run_go_bench_cmd(go_bench_cmd):
  go_cmd = shlex.split(go_bench_cmd)
  print("running go precompile benchmark...\n{}".format(go_bench_cmd))

  raw_stdoutlines = []
  with subprocess.Popen(go_cmd, cwd=GO_VM_PATH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True) as p:
    for line in p.stdout: # b'\n'-separated lines
      print(line, end='')
      raw_stdoutlines.append(line)  # pass bytes as is
    p.wait()

  print("process finished.")
  return raw_stdoutlines


def doBenchInput(wasmfile, testname, input, expected):
  input_results = []
  for engine in HERA_ENGINES:
    #go_bench_cmd =  "go test -v ./core/vm/runtime/... -bench BenchmarkCallEwasm --benchtime 7s --vm.ewasm=\"/root/nofile,benchmark=true,engine={}\"".format(engine)
    # use default benchtime because for fast ones we get too much output from hera on stdout
    go_bench_cmd =  "go test -v ./core/vm/runtime/... -bench BenchmarkCallEwasm --vm.ewasm=\"/root/nofile,benchmark=true,engine={}\"".format(engine)
    go_bench_cmd = go_bench_cmd + " --ewasmfile=\"{}\" --input=\"{}\" --expected=\"{}\"".format(wasmfile, input, expected)
    bench_output = run_go_bench_cmd(go_bench_cmd)
    bench_runs = parse_go_bench_output(bench_output, testname)
    bench_results = []
    for run in bench_runs:
      bench_test = {
        'engine': engine,
        'test_name': testname,
        'total_time': run['total_time'],
        'compile_time': run['compile_time'],
        'exec_time': run['exec_time']
      }
      bench_results.append(bench_test)

    input_results.extend(bench_results)

  return input_results


def main():
  test_name_suffix = args['testsuffix']
  wasm_file= args['wasmfile']
  csv_file_path = args['csvfile']
  testvectorfile = args['testvectors']
  with open(testvectorfile, "r") as read_file:
    testvectors = json.load(read_file)

  bench_results_all_inputs = []
  for i, test in enumerate(testvectors):
    print("benchmarking input {} of {}: {}".format(i, len(testvectors), test['name']))
    #test['name'] test['input'] test['expected']
    # test['name'] == "bn128_mul-chfast2"
    test_name = "{}-{}".format(test['name'], test_name_suffix)
    # "bn128_mul-chfast2-metered-basic-block"
    bench_results = doBenchInput(wasm_file, test_name, test['input'], test['expected'])
    bench_results_all_inputs.extend(bench_results)

  # backup of existing csv file is done by the bash script
  # here we assume an existing file is for the same run
  saveResults(bench_results_all_inputs, csv_file_path)
  print("bench_results_all_inputs:", bench_results_all_inputs)


if __name__ == "__main__":
  main()



