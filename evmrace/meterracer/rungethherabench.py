#!/usr/bin/python

import os
import shutil
import shlex
import csv
import time
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


NODE_BIN_PATH = "/root/node"
NODE_BENCHING_SCRIPT = "/meterracer/metering-bench-v8.js"

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
$ node --experimental-wasm-bigint metering-bench-v8.js /meterracer/wasm_to_meter/ewasm_precompile_ecmul_unmetered.wasm "039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d98ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" "00a1a234d08efaa2616607e31eca1980128b00b415c845ff25bba3afcb81dc00242077290ed33906aeb8e42fd98c41bcb9057ba03421af3f2d08cfc441186024"
instantiate: 61.675ms
exec: 3.225ms
gas used: 26880219n
useGas calls: 2
"""

def parse_node_v8_output(stdoutlines):
    #print("parsing node v8 bench output for {}".format(testname))
    instantiateRegex = "instantiate: ([\w\.]+)"
    execRegex = "exec: ([\w\.]+)"
    #gasRegex = "gas used: ([\d]+)"

    # TODO: check for fail

    compile_line = stdoutlines[-4]
    exec_line = stdoutlines[-3]
    compile_match = re.search(instantiateRegex, compile_line)
    exec_match = re.search(execRegex, exec_line)
    compile_time = compile_match.group(1)
    exec_time = exec_match.group(1)
    compile_time = durationpy.from_str(compile_time)
    exec_time = durationpy.from_str(exec_time)
    total_time = compile_time.total_seconds() + exec_time.total_seconds()

    bench_run = {
      'total_time': total_time,
      'compile_time': compile_time.total_seconds(),
      'exec_time': exec_time.total_seconds()
    }

    return bench_run



def run_node_v8_cmd(wasmfile, input, expected):
  node_v8_bench_cmd = "{} --experimental-wasm-bigint --liftoff --no-wasm-tier-up {} {} \"{}\" \"{}\"".format(NODE_BIN_PATH, NODE_BENCHING_SCRIPT, wasmfile, input, expected)
  print("running node v8 benchmark...\n{}".format(node_v8_bench_cmd))
  node_cmd = shlex.split(node_v8_bench_cmd)
  raw_stdoutlines = []
  with subprocess.Popen(node_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True) as p:
    for line in p.stdout: # b'\n'-separated lines
      print(line, end='')
      raw_stdoutlines.append(line)  # pass bytes as is
    p.wait()

  return raw_stdoutlines


def do_node_v8_bench(wasmfile, input, expected):
  node_bench_results = []
  # get time to do one run
  start_time = time.time()
  output = run_node_v8_cmd(wasmfile, input, expected)
  end_time = time.time()
  result = parse_node_v8_output(output)
  node_bench_results.append(result)

  duration = end_time - start_time
  # calculate number of runs in 60 seconds
  repetitions = round(60 / duration)
  if repetitions < 3:
    repetitions = 3 # minimum
  if repetitions > 50:
    repetitions = 50 # maximum

  for i in range(repetitions - 1):
    print("run {} of {} for node v8...".format(i + 2, repetitions))
    run_output = run_node_v8_cmd(wasmfile, input, expected)
    run_result = parse_node_v8_output(run_output)
    node_bench_results.append(run_result)

  return node_bench_results


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
Time [us]: 5248 (instantiation: 2136, execution: 3112)
got return bytes: 025a6f4181d2b4ea8b724290ffb40156eb0adb514c688556eb79cdea0752c2bb2eff3f31dea215f1eb86023a133a996eb6300b44da664d64251d05381bb8a02e
goos: linux
goarch: amd64
pkg: github.com/ethereum/go-ethereum/core/vm/runtime
BenchmarkCallEwasm-4    ewasmfile: /meterracer/wasm_to_meter/ewasm_precompile_ecmul_unmetered.wasm
Time [us]: 4917 (instantiation: 2069, execution: 2847)
Time [us]: 4856 (instantiation: 2127, execution: 2729)
Time [us]: 5221 (instantiation: 2463, execution: 2758)
Time [us]: 4907 (instantiation: 2234, execution: 2673)
Time [us]: 5002 (instantiation: 2336, execution: 2665)
Time [us]: 5056 (instantiation: 2220, execution: 2836)
Time [us]: 5225 (instantiation: 2198, execution: 3027)
Time [us]: 4957 (instantiation: 2247, execution: 2710)
Time [us]: 5072 (instantiation: 2207, execution: 2864)
Time [us]: 5186 (instantiation: 2297, execution: 2889)
Time [us]: 4891 (instantiation: 2122, execution: 2768)
Time [us]: 5077 (instantiation: 2300, execution: 2777)
Time [us]: 5021 (instantiation: 2227, execution: 2794)
Time [us]: 4872 (instantiation: 2189, execution: 2683)
Time [us]: 5337 (instantiation: 2381, execution: 2955)
Time [us]: 5143 (instantiation: 2470, execution: 2673)
Time [us]: 4904 (instantiation: 2176, execution: 2727)
Time [us]: 5286 (instantiation: 2334, execution: 2951)
Time [us]: 5156 (instantiation: 2524, execution: 2632)
Time [us]: 5199 (instantiation: 2501, execution: 2697)
Time [us]: 5176 (instantiation: 2295, execution: 2880)
Time [us]: 5260 (instantiation: 2138, execution: 3121)
Time [us]: 4765 (instantiation: 2218, execution: 2546)
Time [us]: 5078 (instantiation: 2165, execution: 2913)
Time [us]: 5360 (instantiation: 2334, execution: 3026)
got return bytes: 025a6f4181d2b4ea8b724290ffb40156eb0adb514c688556eb79cdea0752c2bb2eff3f31dea215f1eb86023a133a996eb6300b44da664d64251d05381bb8a02e
      30          48629905 ns/op
PASS
ok      github.com/ethereum/go-ethereum/core/vm/runtime 1.567s
"""


def parse_go_bench_output(stdoutlines, testname):
  print("parsing go bench output for {}".format(testname))
  benchRegex = "Time \[us\]: (\d+) \(instantiation\: (\d+)\, execution: (\d+)\)"

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
    print("doing engine: {}".format(engine))
    #go_bench_cmd =  "go test -v ./core/vm/runtime/... -bench BenchmarkCallEwasm --benchtime 7s --vm.ewasm=\"/root/nofile,benchmark=true,engine={}\"".format(engine)
    # use default benchtime because for fast ones we get too much output from hera on stdout
    # TODO: if engine is wavm, run for longer time
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
    # all runs in bench_results
    input_results.extend(bench_results)
  # all hera engines done
  # do node v8
  
  node_v8_runs = do_node_v8_bench(wasmfile, input, expected)
  node_results = []
  for run in node_v8_runs:
    node_bench_run = {
      'engine': 'v8-liftoff',
      'test_name': testname,
      'total_time': run['total_time'],
      'compile_time': run['compile_time'],
      'exec_time': run['exec_time']
    }
    node_results.append(node_bench_run)
  # done with node
  print("got node results:", node_results)
  input_results.extend(node_results)
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



