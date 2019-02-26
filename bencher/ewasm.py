#!/usr/bin/python

from project.BenchTestGenerator import BenchTestGenerator
from project.WasmVMBencher import WasmVMBencher
from project.settings import vm_descriptors
from project.TestDescriptor import TestDescriptor

import click
import csv
import logging
import sys
import os


WASM_FILE_PATH = '/wasmfiles'

BLACKLIST = ['ecpairing.wasm', 'guido-fuzzer-find-2-norotates.wasm', 'guido-fuzzer-find-1.wasm', 'guido-fuzzer-find-2.wasm']

def getTestDescriptors():
    test_descriptors = {}
    for filename in os.listdir(WASM_FILE_PATH):
        if filename.endswith(".wasm") and filename not in BLACKLIST:
            test_descriptors[filename[:-5]] = WASM_FILE_PATH + "/" + filename
    return test_descriptors


def save_test_results(out_dir, results):
    # TODO: move existing files to old-datetime-folder
    for vm in results:
        with open(os.path.join(out_dir, vm + ".csv"), 'w', newline='') as bench_result_file:
            fieldnames = ['test_name', 'elapsed_time', 'compile_time', 'exec_time']
            writer = csv.DictWriter(bench_result_file, fieldnames=fieldnames)
            writer.writeheader()

            for test_name, result_records in results[vm].items():
                for record in result_records:
                    writer.writerow({"test_name" : test_name, "elapsed_time" : record.time, "compile_time" : record.compile_time, "exec_time" : record.exec_time})


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    logger = logging.getLogger("wasm_bench_logger")

    vm_bencher = WasmVMBencher()
    test_descriptors = getTestDescriptors()
    test_results = vm_bencher.run_tests(test_descriptors, vm_descriptors)
    print("ewasm.py test_results:")
    print(test_results)
    save_test_results("/testresults", test_results)


if __name__ == '__main__':
    main()
