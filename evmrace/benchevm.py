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

INPUT_VECTORS_DIR = "./inputvectors"

EVMONE_BUILD_DIR = "/root/evmone/build"

PARITY_EVM_DIR = "/root/parity/target/release"

CITA_EVM_DIR = "/root/cita-vm/target/release"

GETH_EVM_DIR = "/root/go/src/github.com/ethereum/go-ethereum/core/vm/runtime"


def saveResults(evm_benchmarks):
    result_file = os.path.join(RESULT_CSV_OUTPUT_PATH, "evm_benchmarks.csv")

    # move existing files to old-datetime-folder
    ts = time.time()
    date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    ts_folder_name = "{}-{}".format(date_str, round(ts))
    dest_backup_path = os.path.join(RESULT_CSV_OUTPUT_PATH, ts_folder_name)
    os.makedirs(dest_backup_path)
    #for file in glob.glob(r"{}/*.csv".format(RESULT_CSV_OUTPUT_PATH)):
    if os.path.isfile(result_file):
        print("backing up existing {}".format(result_file))
        shutil.move(result_file, dest_backup_path)
    print("existing csv files backed up to {}".format(dest_backup_path))
    # will always be a new file after this.
    # might move this backup routine to a bash script

    fieldnames = ['engine', 'test_name', 'total_time', 'gas_used']

    # write header if new file
    if not os.path.isfile(result_file):
        with open(result_file, 'w', newline='') as bench_result_file:
            writer = csv.DictWriter(bench_result_file, fieldnames=fieldnames)
            writer.writeheader()

    # append to existing file
    with open(result_file, 'a', newline='') as bench_result_file:
        writer = csv.DictWriter(bench_result_file, fieldnames=fieldnames)
        for row in evm_benchmarks:
            writer.writerow(row)


def get_geth_cmd(codefile, calldata, expected):
    cmd_str = "go test -v -bench BenchmarkEvmCode --codefile {} --input {} --expected {}".format(codefile, calldata, expected)
    return cmd_str


"""
runtime mbpro$ go test -v -bench BenchmarkEvmCode --codefile /root/bn128mul.evm --input 039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d98ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff --expected 0e9c28772a2a79561257f998c9c31e9b47bb592d54b6936bc00066453f50b27816c1cda062bd6cc07463ba71ff1d299223dd1bb9a6ac5cfe1d57a19c87a229e029a4b5947ed4dca6df8349674078a9b3ea3d06b4373d9d7a50866f3de054285d
=== RUN   TestDefaults
--- PASS: TestDefaults (0.00s)
=== RUN   TestEVM
--- PASS: TestEVM (0.00s)
=== RUN   TestExecute
--- PASS: TestExecute (0.00s)
=== RUN   TestCall
--- PASS: TestCall (0.00s)
=== RUN   ExampleExecute
--- PASS: ExampleExecute (0.00s)
codefile: /root/bn128mul.evm
code hex length: 29317
got return bytes: 0e9c28772a2a79561257f998c9c31e9b47bb592d54b6936bc00066453f50b27816c1cda062bd6cc07463ba71ff1d299223dd1bb9a6ac5cfe1d57a19c87a229e029a4b5947ed4dca6df8349674078a9b3ea3d06b4373d9d7a50866f3de054285d
gasUsed: 47561
goos: darwin
goarch: amd64
pkg: github.com/ethereum/go-ethereum/core/vm/runtime
BenchmarkEvmCode-12    	codefile: /root/bn128mul.evm
code hex length: 29317
got return bytes: 0e9c28772a2a79561257f998c9c31e9b47bb592d54b6936bc00066453f50b27816c1cda062bd6cc07463ba71ff1d299223dd1bb9a6ac5cfe1d57a19c87a229e029a4b5947ed4dca6df8349674078a9b3ea3d06b4373d9d7a50866f3de054285d
gasUsed: 47561
codefile: /root/bn128mul.evm
code hex length: 29317
got return bytes: 0e9c28772a2a79561257f998c9c31e9b47bb592d54b6936bc00066453f50b27816c1cda062bd6cc07463ba71ff1d299223dd1bb9a6ac5cfe1d57a19c87a229e029a4b5947ed4dca6df8349674078a9b3ea3d06b4373d9d7a50866f3de054285d
gasUsed: 47561
    1000	   1363188 ns/op
PASS
ok  	github.com/ethereum/go-ethereum/core/vm/runtime	2.847s
"""

def do_geth_bench(geth_cmd):
    print("running geth-evm benchmark...\n{}\n".format(geth_cmd))
    geth_cmd = shlex.split(geth_cmd)
    stdoutlines = []
    with subprocess.Popen(geth_cmd, cwd=GETH_EVM_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout: # b'\n'-separated lines
            print(line, end='')
            stdoutlines.append(line)  # pass bytes as is
        p.wait()

    nsOpRegex = "\d+\s+([\d]+) ns\/op"
    gasregex = "gasUsed: (\d+)"
    # maybe --benchmark_format=json is better so dont have to parse "36.775k"
    time_line = stdoutlines[-3]
    gas_line = stdoutlines[-4]
    time_match = re.search(nsOpRegex, time_line)
    time = durationpy.from_str("{}ns".format(time_match.group(1)))
    gas_match = re.search(gasregex, gas_line)
    gasused = gas_match.group(1)
    return {'gas_used': gasused, 'time': time.total_seconds()}


def get_parity_cmd(codefile, calldata, expected):
    cmd_str = "./parity-evm --code-file {} --input {} --expected {} ".format(codefile, calldata, expected)
    return cmd_str

"""
~/parity# ./target/release/parity-evm --code-file ./bn128mul.evm --input 039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d98ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff --expected "0e9c28772a2a79561257f998c9c31e9b47bb592d54b6936bc00066453f50b27816c1cda062bd6cc07463ba71ff1d299223dd1bb9a6ac5cfe1d57a19c87a229e029a4b5947ed4dca6df8349674078a9b3ea3d06b4373d9d7a50866f3de054285d"
code_hex length: 29317
return_data: "0e9c28772a2a79561257f998c9c31e9b47bb592d54b6936bc00066453f50b27816c1cda062bd6cc07463ba71ff1d299223dd1bb9a6ac5cfe1d57a19c87a229e029a4b5947ed4dca6df8349674078a9b3ea3d06b4373d9d7a50866f3de054285d"
gas used: 47561
code avg run time: 12.059442ms
"""

def do_parity_bench(parity_cmd):
    print("running parity-evm benchmark...\n{}\n".format(parity_cmd))
    parity_cmd = shlex.split(parity_cmd)
    stdoutlines = []
    with subprocess.Popen(parity_cmd, cwd=PARITY_EVM_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout: # b'\n'-separated lines
            print(line, end='')
            stdoutlines.append(line)  # pass bytes as is
        p.wait()

    timeregex = "code avg run time: ([\d\w\.]+)"
    gasregex = "gas used: (\d+)"
    # maybe --benchmark_format=json is better so dont have to parse "36.775k"
    time_line = stdoutlines[-1]
    gas_line = stdoutlines[-2]
    time_match = re.search(timeregex, time_line)
    time = durationpy.from_str(time_match.group(1))
    gas_match = re.search(gasregex, gas_line)
    gasused = gas_match.group(1)
    return {'gas_used': gasused, 'time': time.total_seconds()}


def get_cita_cmd(codefile, calldata, expected):
    cmd_str = "./cita-evm --code-file {} --input {} --expected {} ".format(codefile, calldata, expected)
    return cmd_str

"""
~/cita-vm# ./target/release/cita-evm --code-file /evmrace/evmcode/bn128_mul_weierstrudel.hex --input 039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d98ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff --expected "0e9c28772a2a79561257f998c9c31e9b47bb592d54b6936bc00066453f50b27816c1cda062bd6cc07463ba71ff1d299223dd1bb9a6ac5cfe1d57a19c87a229e029a4b5947ed4dca6df8349674078a9b3ea3d06b4373d9d7a50866f3de054285d"
code_hex length: 29316
gas_used: 75089
code avg run time: 16.695968ms
"""

def do_cita_bench(cita_cmd):
    print("running cita-evm benchmark...\n{}\n".format(cita_cmd))
    cita_cmd = shlex.split(cita_cmd)
    stdoutlines = []
    with subprocess.Popen(cita_cmd, cwd=CITA_EVM_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout: # b'\n'-separated lines
            print(line, end='')
            stdoutlines.append(line)  # pass bytes as is
        p.wait()

    timeregex = "code avg run time: ([\d\w\.]+)"
    gasregex = "gas_used: (\d+)"
    time_line = stdoutlines[-1]
    gas_line = stdoutlines[-2]
    time_match = re.search(timeregex, time_line)
    time = durationpy.from_str(time_match.group(1))
    gas_match = re.search(gasregex, gas_line)
    gasused = gas_match.group(1)
    return {'gas_used': gasused, 'time': time.total_seconds()}





def get_evmone_cmd(codefile, calldata, expected):
    cmd_str = "bin/evmone-bench {} {} {} --benchmark_color=false --benchmark_filter=external_evm_code --benchmark_min_time=7".format(codefile, calldata, expected)
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

    timeregex = "external_evm_code\s+(\d+) us"
    gasregex = "gas_used=([\d\.\w]+)"
    # maybe --benchmark_format=json is better so dont have to parse "36.775k"
    benchline = stdoutlines[-1]
    time_match = re.search(timeregex, benchline)
    us_time = durationpy.from_str("{}us".format(time_match.group(1)))
    gas_match = re.search(gasregex, benchline)
    gasused = gas_match.group(1)
    return {'gas_used': gasused, 'time': us_time.total_seconds()}


def main():
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
        file_name = "{}-inputs.json".format(inputsfilename)
        inputs_file_path = os.path.join(INPUT_VECTORS_DIR, file_name)
        with open(inputs_file_path) as f:
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

                evmone_result = {}
                evmone_result['engine'] = "evmone"
                evmone_result['test_name'] = test_name
                evmone_result['total_time'] = evmone_bench_result['time']
                evmone_result['gas_used'] = evmone_bench_result['gas_used']
                evm_benchmarks.append(evmone_result)

                parity_bench_cmd = get_parity_cmd(codefilepath, calldata, expected)
                parity_bench_result = do_parity_bench(parity_bench_cmd)
                parity_result = {}
                parity_result['engine'] = "parity-evm"
                parity_result['test_name'] = test_name
                parity_result['total_time'] = parity_bench_result['time']
                parity_result['gas_used'] = parity_bench_result['gas_used']
                evm_benchmarks.append(parity_result)

                geth_bench_cmd = get_geth_cmd(codefilepath, calldata, expected)
                geth_bench_result = do_geth_bench(geth_bench_cmd)
                geth_result = {}
                geth_result['engine'] = "geth-evm"
                geth_result['test_name'] = test_name
                geth_result['total_time'] = geth_bench_result['time']
                geth_result['gas_used'] = geth_bench_result['gas_used']
                evm_benchmarks.append(geth_result)

                cita_bench_cmd = get_cita_cmd(codefilepath, calldata, expected)
                cita_bench_result = do_cita_bench(cita_bench_cmd)
                cita_result = {}
                cita_result['engine'] = "cita-evm"
                cita_result['test_name'] = test_name
                cita_result['total_time'] = cita_bench_result['time']
                cita_result['gas_used'] = cita_bench_result['gas_used']
                evm_benchmarks.append(cita_result)

                print("done with input:", test_name)

        print("done benching: ", benchname)

    print("got evm_benchmarks:", evm_benchmarks)

    saveResults(evm_benchmarks)

if __name__ == "__main__":
    main()