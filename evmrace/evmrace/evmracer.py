#!/usr/bin/python

import jinja2, json, os, shutil
from functools import reduce

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
    go_cmd = "go test -bench Benchmark{} -benchtime 5s".format(benchname)
    gofile = "{}_test.go".format(benchname)

    # copy benchmark file
    srcfile = os.path.abspath(benchname) + "/" + gofile
    shutil.copy(srcfile, destdir)
    # fill go template

    # run go command
    print("running benchmark {}...".format(input['name']))
    go_process = Popen(go_cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
    go_process.wait(None)
    stdoutlines = [str(line, 'utf8') for line in go_process.stdout]
    print(("").join(stdoutlines), end="")


def fill_bench_templates(benchname, input):
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
             do_go_bench(benchname, input)




if __name__ == "__main__":
    main()