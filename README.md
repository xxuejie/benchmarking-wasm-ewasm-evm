
# benchmark wasm engines

1. Prepare "standalone" wasm files. Wasm modules should export one function, `main`, which takes no input arguments and returns no result (this is for maximum compatibility with engines, which often don't support passing arguments to invoked functions).

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
$ docker run -it -v $(pwd)/wasmfiles:/wasmfiles -v $(pwd)/testresults:/testresults --security-opt seccomp=./enginerunner/dockerseccompprofile.json wasm-engines
```

5. inside the docker container, run the benchmark script

```
## need to use `python3.7`
$ python3.7 main.py |& tee wasm-run1.log
```

6. exit the docker container. benchmark results are in `./testresults`, one csv file per engine



# benchmark EVM, native, and prepare standalone wasm files

```
$ cd evmrace
$ docker build . -t evmrace
$ docker run -it --entrypoint=/bin/bash -v $(pwd)/evmwasmfiles:/evmwasmfiles -v $(pwd)/evmraceresults:/evmraceresults evmrace

### run geth native precompile benchmarks
## parse results and save to /evmraceresults/geth_precompile_benchmarks.csv
$ PYTHONIOENCODING=UTF-8 python3 precompileracer.py

### use rust-code templates to compile standalone wasm files with input vectors from /evmrace/inputvectors
## also compile and benchmark native rust exe's
## if a ./evmrace/evmrace/$benchmark folder has a *_test.go file, we have EVM bytecode.
## for those, benchmark using the geth EVM. TODO: also benchmark using evmone


$ PYTHONIOENCODING=UTF-8 python3 evmracer.py

# after running evmracer.py, standalone wasm files will be saved to /evmwasmfiles
# exit the docker container, copy wasm files to /wasmfiles, for benchmarking with `wasm-engines`

## copy the test result csv files into a folder for analysis with the python notebook
# /evmraceresults/native_benchmarks.csv
# /evmraceresults/evm_benchmarks.csv
# /evmraceresults/geth_precompile_benchmarks.csv
```

```
### ewasm metering benchmarks
$ cd meterracer
$ ./meteringprep.sh
$ ./meteringinjector.sh
$ ./meteringherabencher.sh
$ ./meteringwagonbencher.sh
```

