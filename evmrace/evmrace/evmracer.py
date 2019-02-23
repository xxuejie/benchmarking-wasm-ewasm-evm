#!/usr/bin/python

import jinja2, json, os, shutil
from functools import reduce
import subprocess

def get_rust_bytes(hex_str):
    tmp = map(''.join, zip(*[iter(hex_str)]*2))
    tmp = map(lambda x: int(x, 16), tmp)
    tmp = map(lambda x: '{}u8'.format(x), tmp)
    tmp = reduce(lambda x, y: x+', '+y, tmp)
    return '[ '+tmp+' ]'

"""
def fill_template(template_file, args):
    templateLoader = jinja2.FileSystemLoader(os.path.dirname(template_file))
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(os.path.split(template_file)[1])
    outputText = template.render(args)  # this is where to put args to the template renderer
    return outputText
"""

def do_go_bench(benchname, input):
    #COPY ./sha1_test.go /go-ethereum/core/vm/runtime/sha_test.go
    #RUN cd /go-ethereum/core/vm/runtime && go test -bench BenchmarkSHA1 -benchtime 5s
    destdir = "/go-ethereum/core/vm/runtime/"
    # first letter must be capitalized
    goBenchName = benchname[:1].upper() + benchname[1:]
    go_cmd = "go test -bench Benchmark{} -benchtime 5s".format(goBenchName)
    gofile = "{}_test.go".format(benchname)

    # fill go template

    with open("./" + benchname + "/" + gofile) as file_:
        template = jinja2.Template(file_.read())
        filledgo = template.render(input=input['input'], expected=input['expected'])

    gofileout = "{}/{}_filled_test.go".format(os.path.abspath(benchname), benchname)

    with open(gofileout, 'w') as outfile:
        outfile.write(filledgo)

    # copy benchmark file
    shutil.copy(gofileout, destdir)

    # run go command
    print("running go benchmark {}...\n{}".format(input['name'], go_cmd))
    go_process = subprocess.Popen(go_cmd, cwd=destdir, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
    go_process.wait(None)
    stdoutlines = [str(line, 'utf8') for line in go_process.stdout]
    print(("").join(stdoutlines), end="")
    """
    running benchmark sha1-10808-bits...
    gasUsed: 1543776
    goos: linux
    goarch: amd64
    pkg: github.com/ethereum/go-ethereum/core/vm/runtime
    BenchmarkSha1-4         gasUsed: 1543776
    gasUsed: 1543776
         200          44914864 ns/op
    PASS
    ok      github.com/ethereum/go-ethereum/core/vm/runtime 13.472s
    """


def bench_rust_binary(rustdir, native_exec):
    print("running rust native {}...\n{}".format(input['name']), native_exec)
    for i in range(1,10):
      rust_process = subprocess.Popen(native_exec, cwd=rustdir, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
      rust_process.wait(None)
      stdoutlines = [str(line, 'utf8') for line in rust_process.stdout]
      print(("").join(stdoutlines), end="")


def do_rust_bench(benchname, input):
    #rustsrc = "{}/rust-code/src/bench.rs".format(os.path.abspath(benchname))
    rustsrc = "{}/rust-code".format(os.path.abspath(benchname))

    filldir = os.path.abs("rust-code-filled")
    if not os.path.exists(filldir):
        os.mkdir(filldir)

    shutil.copytree(rustsrc, filldir)
    rusttemplate = "{}/src/bench.rs".format(filldr)

    input_len = len(input['input']) / 2
    input_str = "let input: [u8; {}] = {};".format(input_len, get_rust_bytes(input['input']))
    expected_len = len(input['expected']) / 2
    expected_str = "let expected: [u8; {}] = {};".format(expected_len, get_rust_bytes(input['expected']))

    with open(rusttemplate) as file_:
        template = jinja2.Template(file_.read())
        # "let input: [u8; 2737] = [ 84u8, 173u8, 9u8, ... ];"
        filledrust = template.render(input=input_str, expected=expected_str)

    rustfileout = "{}/src/bench.rs".format(filldir, benchname)
    with open(rustfileout, 'w') as outfile:
        outfile.write(filledrust)

    # compile rust code
    rust_native_cmd = "cargo build --release --bin {}_native".format(input['name'])
    print("compiling rust native {}...\n{}".format(input['name'], rust_native_cmd))
    rust_process = subprocess.Popen(rust_native_cmd, cwd=filldir, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
    rust_process.wait(None)
    stdoutlines = [str(line, 'utf8') for line in rust_process.stdout]
    print(("").join(stdoutlines), end="")
    # native binary is at ./target/release/sha1_native

    rust_wasm_cmd = "cargo build --release --lib --target wasm32-unknown-unknown"
    print("compiling rust wasm {}...\n{}".format(input['name'], rust_wasm_cmd))
    rust_process = subprocess.Popen(rust_wasm_cmd, cwd=filldir, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
    rust_process.wait(None)
    stdoutlines = [str(line, 'utf8') for line in rust_process.stdout]
    print(("").join(stdoutlines), end="")
    # wasm is at ./target/wasm32-unknown-unkown/release/sha1_wasm.wasm

    # run rust binary
    bench_rust_binary(filldir, "./target/release/{}_native".format(benchname))


#def fill_bench_templates(benchname, input):
    # rust is in ./{benchname}/rust-code/src/bench.rs
    # go is in ./{benchname}/{benchname}_test.go
    #cargo build --release --bin sha1_native
    #cargo build --release --lib --target wasm32-unknown-unknown
    


def main():
    benchdirs = [dI for dI in os.listdir('./') if os.path.isdir(os.path.join('./',dI))]

    for benchname in benchdirs:
       with open("{}/{}-inputs.json".format(benchname, benchname)) as f:
           bench_inputs = json.load(f)
           for input in bench_inputs:
             #input['name']
             #input['input']
             #input['expected']
             #do_go_bench(benchname, input)
             do_rust_bench(benchname, input)




if __name__ == "__main__":
    main()