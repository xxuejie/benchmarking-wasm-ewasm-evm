#!/usr/bin/python

import json, re
import subprocess
import nanodurationpy as durationpy
import csv
import time
import datetime
import os
import shutil
import shlex


RESULT_CSV_OUTPUT_PATH = "/evmraceresults"


EVM_CODE_DIR = "/evmrace/evmcode"

EVMONE_BUILD_DIR = "/root/evmone/build"


def saveResults(evm_benchmarks):
    # move existing files to old-datetime-folder
    ts = time.time()
    date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    ts_folder_name = "{}-{}".format(date_str, round(ts))
    dest_backup_path = os.path.join(RESULT_CSV_OUTPUT_PATH, ts_folder_name)
    os.makedirs(dest_backup_path)
    for file in glob.glob(r"{}/*.csv".format(RESULT_CSV_OUTPUT_PATH)):
        print("backing up existing {}".format(file))
        shutil.move(file, dest_backup_path)
    print("existing csv files backed up to {}".format(dest_backup_path))

    evm_file = "{}/evm_benchmarks.csv".format(RESULT_CSV_OUTPUT_PATH)
    with open(evm_file, 'w', newline='') as bench_result_file:
        fieldnames = ['test_name', 'elapsed_time', 'gas_used']
        writer = csv.DictWriter(bench_result_file, fieldnames=fieldnames)
        writer.writeheader()
        for test_name, test_results in evm_benchmarks.items():
            writer.writerow({"test_name" : test_name, "elapsed_time" : test_results['time'], "gas_used" : test_results['gasUsed']})


def get_evmone_cmd(codefile, calldata, expected):
    cmd_str = "test/evmone-bench {} {} {} --benchmark_color=false --benchmark_filter=bench_evm_code --benchmark_min_time=7".format(codefile, calldata, expected)
    return cmd_str


"""
~/evmone/build# test/evmone-bench sha1code.hex 1605782b00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000006010203040506 5d211bad8f4ee70e16c7d343a838fc344a1ed961000000000000000000000000 --benchmark_filter=bench_evm_code
argv[0] = test/evmone-bench
argv[1] = sha1code.hex
argv[2] = 1605782b00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000006010203040506
argv[3] = 5d211bad8f4ee70e16c7d343a838fc344a1ed961000000000000000000000000
argv[4] = --benchmark_filter=bench_evm_code
hex code length:3107
calldata size:74
expected:5d211bad8f4ee70e16c7d343a838fc344a1ed961000000000000000000000000
2019-04-10 15:57:52
Running test/evmone-bench
Run on (4 X 2294.68 MHz CPU s)
CPU Caches:
  L1 Data 32K (x2)
  L1 Instruction 32K (x2)
  L2 Unified 256K (x2)
  L3 Unified 51200K (x2)
----------------------------------------------------------------------
Benchmark               Time           CPU Iterations UserCounters...
----------------------------------------------------------------------
bench_evm_code        152 us        152 us       4694 gas_rate=241.788M/s gas_used=36.775k
"""

def do_evmone_bench(evmone_cmd):
    print("running evmone benchmark...\n{}\n".format(evmone_cmd))
    evmone_cmd = shlex.split(evmone_cmd)
    stdoutlines = []
    with subprocess.Popen(evmone_cmd, cwd=EVMONE_BUILD_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout: # b'\n'-separated lines
            print(line, end='')
            stdoutlines.append(line)  # pass bytes as is
        p.wait()

    timeregex = "bench_evm_code\s+(\d+) us"
    gasregex = "gas_used=([\d\.\w]+)"
    # maybe --benchmark_format=json is better so dont have to parse "36.775k"
    benchline = stdoutlines[-1]
    time_match = re.search(timeregex, benchline)
    us_time = durationpy.from_str("{}us".format(time_match.group(1)))
    gas_match = re.search(gasregex, benchline)
    gasused = gas_match.group(1)
    return {'gas_used': gasused, 'time': us_time.total_seconds()}




def main():
    #evmcodefiles = []
    #for filename in os.listdir('./evmcode'):
    #    if filename.endswith(".hex"):
    #        evmcodefiles.append(filename)
    evmcodefiles = [fname for fname in os.listdir(EVM_CODE_DIR) if fname.endswith(".hex")]
    evm_benchmarks = []
    for codefile in evmcodefiles:
        print("start benching: ", codefile)
        codefilepath = os.path.join(EVM_CODE_DIR, codefile)
        benchname = codefile.replace(".hex", "")
        inputsfilename = benchname
        shift_suffix = ""
        if benchname.endswith("_shift"):
            inputsfilename = benchname.replace("_shift", "")
            shift_suffix = "-shiftopt"
        if benchname.endswith("_weierstrudel"):
            inputsfilename = inputsfilename
        else:
            inputsfilename = inputsfilename + "_evmone"
        with open("inputvectors/{}-inputs.json".format(inputsfilename)) as f:
            bench_inputs = json.load(f)
            for input in bench_inputs:
                print("bench input:", input['name'])
                calldata = input['input']
                expected = input['expected']
                evmone_bench_cmd = get_evmone_cmd(codefilepath, calldata, expected)
                evmone_bench_result = do_evmone_bench(evmone_bench_cmd)
                test_name = input['name'] + shift_suffix
                # evm_benchmarks[input['name']] = evmone_bench_result
                print("got evmone_bench_result:", evmone_bench_result)

                bench_result = {}
                bench_result['engine'] = "evmone"
                bench_result['test_name'] = test_name
                bench_result['time'] = evmone_bench_result['time']
                bench_result['gas_used'] = evmone_bench_result['gas_used']
                evm_benchmarks.append(bench_result)

                print("done with input:", test_name)

        print("done benching: ", benchname)

    print("got evm_benchmarks:", evm_benchmarks)

    #saveResults(evm_benchmarks)

if __name__ == "__main__":
    main()