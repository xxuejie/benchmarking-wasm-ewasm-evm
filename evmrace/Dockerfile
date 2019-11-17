FROM ubuntu:18.04

# https://github.com/kuralabs/docker-python3-dev/blob/master/Dockerfile

# System deps
RUN apt-get update
RUN apt-get install -y software-properties-common git sudo build-essential wget curl nano \
    autoconf automake cmake libtool make unzip zlib1g-dev texinfo \
    gcc musl-dev


# Install Python stack
RUN apt-get update \
    && apt-get --yes --no-install-recommends install \
        python3 python3-dev \
        python3-pip python3-venv python3-wheel python3-setuptools \
        build-essential \
        python-dev \
        graphviz git openssh-client \
    && rm -rf /var/lib/apt/lists/*


# install rust
RUN curl https://sh.rustup.rs -sSf | \
    sh -s -- --default-toolchain stable -y && . $HOME/.cargo/env
ENV PATH=/root/.cargo/bin:$PATH
RUN rustup default nightly-2019-01-15

RUN rustup target add wasm32-unknown-unknown


# Install Go 1.11
RUN add-apt-repository ppa:longsleep/golang-backports && apt-get update && apt-get install -y golang-go



# install geth
RUN go get -u -v github.com/ethereum/go-ethereum
# RUN cd /root/go/src/github.com/ethereum/go-ethereum && git checkout v1.8.23
RUN cd /root/go/src/github.com/ethereum/go-ethereum && git remote add cdetrio https://github.com/cdetrio/go-ethereum.git
RUN cd /root/go/src/github.com/ethereum/go-ethereum && git fetch cdetrio
RUN cd /root/go/src/github.com/ethereum/go-ethereum && git checkout evm-code-bencher
RUN ln -s /root/go/src/github.com/ethereum/go-ethereum /go-ethereum
# cd /go-ethereum/core/vm/runtime && go test -bench BenchmarkEvmCode -benchtime 5s


# install python modules needed for benchmarking script
RUN pip3 install durationpy jinja2 pandas
# dont alias python to python3 because it will break apt (assumes python is python2)


# install evmone
WORKDIR /root
RUN git clone --recursive --single-branch --branch bench-evm-codes https://github.com/cdetrio/evmone
RUN cd evmone && mkdir build
RUN cd evmone/build && cmake .. -DEVMONE_TESTING=ON
RUN cd evmone/build && cmake --build . -- -j
# /root/evmone/build/bin/evmone-bench


# install parity-evm
RUN git clone --recursive --single-branch --branch evm-code-bencher https://github.com/cdetrio/parity
RUN cd parity/evmbin && cargo build --release
# /root/parity/target/release/parity-evm

# deps required to build full parity for native precompile benchmarks
RUN apt-get update
RUN apt-get install -y libudev-dev
# cd /root/parity/ && cargo bench -p ethcore


# install cita-vm
RUN git clone --single-branch --branch evm-bencher https://github.com/xxuejie/cita-vm
RUN cd cita-vm/evmbin && cargo build --release
# /root/cita-vm/target/release/cita-evm


WORKDIR /
RUN mkdir -p /evmraceresults
RUN mkdir /evmrace
COPY ./benchevm.py /evmrace
COPY ./nanodurationpy.py /evmrace
COPY ./benchparityprecompiles.py /evmrace
COPY ./benchgethprecompiles.py /evmrace
COPY ./inputvectors /evmrace/inputvectors
COPY ./evmcode /evmrace/evmcode

WORKDIR /evmrace

CMD /bin/bash
