#!/usr/bin/python

import os
import shutil
import shlex
import csv
import time, datetime
import json

import argparse, sys

parser = argparse.ArgumentParser()

# hyphens in argument name are converted to underscores
parser.add_argument('--precompilename', help='')
#Eparser.add_argument('--meteringtype', help='metering types for wasm file names, wasmfile_name_{meteringtype}.wasm')
#parser.add_argument('--testsuffixes', help='suffixes corresponding to meteringtypes, e.g. ["metered-super-block", ..]')
#parser.add_argument('--wasmfile', help='wasm file name for precompile implementation, matching pattern wasmfile_name_meteringtype.wasm')
parser.add_argument('--testsuffix', help='suffix for benchmark test case name')
parser.add_argument('--wasmfile', help='full path of wasm file to benchmark')
parser.add_argument('--testvectors', help='full path of json file with test vectors')
parser.add_argument('--csvfile', help='full path of csv file to save results')

args = vars(parser.parse_args())

GO_VM_PATH = "/go-ethereum/core/vm/"

HERA_ENGINES = ['wabt', 'binaryen', 'wavm']

# go test -v ./core/vm/runtime/... -run TestCallEwasm --vm.ewasm="/root/hera/build/src/libhera.so,benchmark=true,engine=binaryen" --ewasmfile="/meterracer/wasm_to_meter/ewasm_precompile_ecpairing_minified.wasm" --input="00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed275dc4a288d1afb3cbb1ac09187524c7db36395df7be3b99e673b13a075a65ec1d9befcd05a5323e6da4d435f3b617cdb3af83285c2df711ef39c01571827f9d" --expected="0000000000000000000000000000000000000000000000000000000000000001" 


def saveResults(benchmark_results, result_file):

  # should engine be concatenated into the test_name?  no - engine should be a different column
  # instantiate_time is name for compile time or parse/decode time
  fieldnames = ['engine', 'test_name', 'gas', 'total_time', 'instantiate_time', 'exec_time']

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
                        "test_name" : test_result['name'],
                        "gas" : test_result['gas'],
                        "total_time" : test_result['total_time'],
                        "instantiate_time": test_result['instantiate_time'],
                        "exec_time": test_result['exec_time']
                      })




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


# parsing code from https://github.com/ethereum/benchmarking/blob/master/constantinople/scripts/postprocess_geth_v2.py
def parse_go_bench_output(stdoutlines, testname, name_suffix="no-metering"):
  print("parsing go bench output for {}".format(testname))
  #benchRegex = "Benchmark(Precompiled.*)-Gas=([\d]+)\S+\s+\d+\s+([\d\.]+) ns\/op"
  benchRegex = "Benchmark(Precompiled.*)-Gas=([\d]+)"
  #opRegexp = re.compile("Benchmark(Op.*)\S+\s+\d+\s+([\d\.]+) ns\/op") 
  nsOpRegex = "\d+\s+([\d\.]+) ns\/op"
  gasRegex = "gas used: ([\d]+)"

  # FIXME: check for FAIL and skip test

  # first match test name
  # then match gas used
  # then match ns/op, then append result and wait for next test name
  bench_tests = []
  test_name = ""
  gas_used = -1
  nanosecs = 0
  for line in stdoutlines:
    print(line)
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


def doBenchInput(wasmfile, name_suffix, testname, input, expected):
  input_results = []
  for engine in HERA_ENGINES:
    go_bench_cmd =  "go test -v ./core/vm/runtime/... -run BenchmarkCallEwasm --benchtime 7s --vm.ewasm=\"/root/nofile,benchmark=true,engine={}\"".format(engine)
    go_bench_cmd = go_bench_cmd + " --ewasmfile=\"{}\" --input=\"{}\" --expected=\"{}\"".format(wasmfile, input, expected)
    bench_output = run_go_bench_cmd(go_bench_cmd)
    bench_results = parse_go_bench_output(bench_output, testname, name_suffix)
    input_results.extend(bench_results)

  return input_results



"""
arg_names = list(args.keys())
arg_names = [n for n in arg_names if args[n] is not None]
#arg_names.remove('name_suffix')
#arg_names.remove('wasm_dir')
#arg_names.remove('csv_name')
"""

def main():
  # TODO: use args['precompilename'] ?

  test_name_suffix = args['testsuffix']
  wasm_file= args['wasmfile']
  csv_file_name = args['csvfile']
  testvectorfile = args['testvectors']
  with open(testvectorfile, "r") as read_file:
    testvectors = json.load(read_file)


  bench_results_all_inputs = []
  for test in testvectors:
    #test['input'] test['expected'] test['name']
    bench_results = doBenchInput(wasm_file, ttest_name_suffix, est['name'], test['input'], test['expected'])
    bench_results_all_inputs.extend(bench_results)


"""
  # TODO: the backup must be done by the bash script.
  # here we have to assume an existing file is for the same run
  # move existing csv file to backup-datetime-folder
  ts = time.time()
  date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
  ts_folder_name = "backup-{}-{}".format(date_str, round(ts))
  dest_backup_path = os.path.join(output_file_path, ts_folder_name)
  result_file = os.path.join(output_file_path, output_file_name)
  # back up existing result csv file
  if os.path.isfile(result_file):
    os.makedirs(dest_backup_path)
    shutil.move(result_file, dest_backup_path)
    print("existing {} moved to {}".format(output_file_name, dest_backup_path))
"""

  saveResults(bench_results_all_inputs, csv_file_path)
  print("bench_results_all_inputs:", bench_results_all_inputs)


if __name__ == "__main__":
  main()



