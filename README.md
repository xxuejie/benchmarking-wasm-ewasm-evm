# WARNING: WORK-IN-PROGRESS

## Attempt to run at your own risk. These scripts are probably broken and won't work for you. The documentation below is out of date or incomplete. This warning will be removed once stable.

# benchmark wasm engines

Engines benchmarked: asmble (compiler), life (interpreter), life-polymerase (compiler), v8-interpreter, v8-liftoff, v8-turbofan, wabt (interp), wagon (interp), wasmi (interp), wasmtime (compiler), wavm (compiler). Measures instantiation time (decode/instantiate for interpreters, decode/instantiate/compile for compilers) and execution time.

1. Prepare "standalone" wasm files. Wasm modules should export one function, `main`, which takes no input arguments and returns no result (this is for maximum compatibility, as engines often don't support passing arguments to invoked functions without extra support from an embedder).
  * If you want run the same benchmarks as in the Ewasm benchmark report, see the section below (prepare wasm benchmark files).

2. build the `wasm-engines` docker container

```
$ cd enginerunner
$ docker build . -t wasm-engines
```

3. put your .wasm files in `wasmfiles` directory. File names will be used for `test_name` column in csv results.

4. run the `wasm-engines` docker container with ./wasmfiles and ./testresults as mounted volumes

```
## docker needs --security-opt because one of the engines (life or wasmer?) uses an uncommon syscall (userfaultfd??)

$ cd ..
$ docker run -it -v $(pwd)/../wasmfiles:/wasmfiles -v $(pwd)/../testresults:/testresults --security-opt seccomp=../enginerunner/dockerseccompprofile.json wasm-engines
```

5. inside the docker container, run the benchmark script

```
## move to directory with the engine runner script
$ cd /benchrunner

## need to use `python3.7`
$ python3.7 main.py |& tee wasm-run1.log
```

6. exit the docker container. benchmark results are in `./testresults`, one csv file per engine



# prepare wasm benchmark files
```
### use rust-code templates and inputvectors to compile standalone wasm files

## also compile and benchmark native rust exe's

```

# benchmark EVM engines and geth/parity precompiles
```
$ cd evmrace
$ docker build . -t evmrace
$ docker run -it --entrypoint=/bin/bash -v $(pwd)/evmwasmfiles:/evmwasmfiles -v $(pwd)/evmraceresults:/evmraceresults evmrace

### run geth native precompile benchmarks
## parse results and save to /evmraceresults/geth_precompile_benchmarks.csv
$ PYTHONIOENCODING=UTF-8 python3 precompileracer.py


$ PYTHONIOENCODING=UTF-8 python3 evmracer.py

# after running evmracer.py, standalone wasm files will be saved to /evmwasmfiles

## copy the test result csv files into a folder for analysis with the python notebook
# /evmraceresults/evm_benchmarks.csv
# /evmraceresults/geth_precompile_benchmarks.csv
```

# benchmark ewasm metering
```
### ewasm metering benchmarks
$ cd meterracer
$ ./meteringprep.sh
$ ./meteringinjector.sh
$ ./meteringherabencher.sh
$ ./meteringwagonbencher.sh
```

