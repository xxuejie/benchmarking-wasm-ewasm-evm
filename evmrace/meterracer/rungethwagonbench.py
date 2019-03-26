#!/usr/bin/python

import os
import shutil
import shlex
import prepgethwagoncode
import wagonbenchcmd
import csv
import time, datetime

import argparse, sys

parser = argparse.ArgumentParser()

# hyphens in argument name are converted to underscores
parser.add_argument('--name_suffix', help='suffix for all test names (e.g. --name-suffix="metering-inline")')
parser.add_argument('--wasm_dir', help='full path of dir containing wasm files')
parser.add_argument('--csv_name', help='dir to save csv file')
parser.add_argument('--sha256', help='wasm file for sha256')
parser.add_argument('--bn128add', help='wasm file for bn128add')
parser.add_argument('--bn128mul', help='wasm file for bn128mul')
parser.add_argument('--bn128pairing', help='wasm file for bn128pairing')
parser.add_argument('--modexp', help='wasm file for modexp')
parser.add_argument('--ecrecover', help='wasm file for ecrecover')

args = vars(parser.parse_args())


# output path should be mounted docker volume
RESULT_CSV_OUTPUT_PATH = "/evmraceresults"

#RESULT_CSV_FILENAME = "metering_precompile_benchmarks.csv"

GO_VM_PATH = "/go-ethereum/core/vm/"

#python3 rungobench.py --wasm_dir="/meterracer/wasm_to_meter/" --name_suffix="no-metering" --sha256="sha256_unmetered.wasm"



GO_PRECOMPILE_NAMEDEFS = {
  "sha256": {
    "benchname": "BenchmarkPrecompiledSha256",
    "varname": "ewasmSha256HashCode",
    "gofile": "ewasm_precompile_sha256.go"
  },
  "bn128add": {
    "benchname": "BenchmarkPrecompiledBn256Add",
    "varname": "ewasmEcaddCode",
    "gofile": "ewasm_precompile_ecadd.go"
  },
  "bn128mul": {
    "benchname": "BenchmarkPrecompiledBn256ScalarMul",
    "varname": "ewasmEcmulCode",
    "gofile": "ewasm_precompile_ecmul.go"
  },
  "bn128pairing": {
    "benchname": "BenchmarkPrecompiledBn256Pairing",
    "varname": "ewasmEcpairingCode",
    "gofile": "ewasm_precompile_ecpairing.go"
  },
  "modexp": {
    "benchname": "BenchmarkPrecompiledModExp",
    "varname": "ewasmExpmodCode",
    "gofile": "ewasm_precompile_expmod.go"
  },
  "ecrecover": {
    "benchname": "BenchmarkPrecompiledEcrecover",
    "varname": "ewasmEcrecoverCode",
    "gofile": "ewasm_precompile_ecrecover.go"
  }
}


def prepare_ewasm_go_file(go_def_names, wasmdir, wasmfile):
  varname = go_def_names['varname']
  gofile = go_def_names['gofile']
  print("preparing ewasm go file with wasmfile:", wasmfile)
  prepgethwagoncode.prepare_go_file(wasmfiledir=wasmdir, wasmfile=wasmfile, varname=varname, gofile=gofile)
  return gofile


def saveResults(precompile_benchmarks, output_file_path, output_file_name):
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

  with open(result_file, 'w', newline='') as bench_result_file:
    fieldnames = ['test_name', 'gas', 'time']
    writer = csv.DictWriter(bench_result_file, fieldnames=fieldnames)
    writer.writeheader()
    for test_result in precompile_benchmarks:
      writer.writerow({"test_name" : test_result['name'], "gas" : test_result['gas'], "time" : test_result['time']})


## should take as input: wasm_file_name, test_name_suffix, 
# e.g. rungobench.py --sha256=sha256_metered_inline.wasm 

arg_names = list(args.keys())
arg_names = [n for n in arg_names if args[n] is not None]
arg_names.remove('name_suffix')
arg_names.remove('wasm_dir')
arg_names.remove('csv_name')

def main():
  test_name_suffix = args['name_suffix']
  wasm_file_dir = args['wasm_dir']
  csv_file_name = args['csv_name']
  #for name in arg_names:
  #  if args[name]:
  all_bench_results = []
  for precompile_name in arg_names:
    print("doing precompile:", precompile_name)

    wasm_file = args[precompile_name]
    prec_info = GO_PRECOMPILE_NAMEDEFS[precompile_name]

    gofile = prepare_ewasm_go_file(prec_info, wasm_file_dir, wasm_file)
    gofilesrcpath = os.path.join(wasm_file_dir, gofile)
    gofiledestpath = os.path.join(GO_VM_PATH, gofile)
    if os.path.isfile(gofiledestpath):
        os.remove(gofiledestpath)
    shutil.move(gofilesrcpath, GO_VM_PATH)

    bench_name_results = wagonbenchcmd.do_go_precompile_bench(GO_VM_PATH, prec_info['benchname'], test_name_suffix)
    print("got results from wagonbenchcmd:", bench_name_results)
    all_bench_results.extend(bench_name_results)


  saveResults(all_bench_results, RESULT_CSV_OUTPUT_PATH, csv_file_name)
  print("all_bench_results:", all_bench_results)


if __name__ == "__main__":
  main()



