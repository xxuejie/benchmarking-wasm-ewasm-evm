FROM ubuntu:18.04

# https://github.com/kuralabs/docker-python3-dev/blob/master/Dockerfile

# System deps
RUN apt-get update
RUN apt-get install -y software-properties-common git sudo build-essential wget curl nano \
    autoconf automake cmake libtool llvm-6.0 make ninja-build unzip zlib1g-dev texinfo


# Install Python stack
RUN apt-get update \
    && apt-get --yes --no-install-recommends install \
        python3 python3-dev \
        python3-pip python3-venv python3-wheel python3-setuptools \
        build-essential \
        python-dev \
        graphviz git openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Install Go 1.11
RUN add-apt-repository ppa:longsleep/golang-backports && apt-get update && apt-get install -y golang-go

# Install Clang 8 (needed for life -polymerase)
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    apt-add-repository "deb http://apt.llvm.org/bionic/ llvm-toolchain-bionic-8 main" && \
    apt-get update && apt-get install -y clang-8 lldb-8 lld-8

RUN ln -s /usr/bin/clang-8 /usr/bin/clang && \
    ln -s /usr/bin/clang++-8 /usr/bin/clang++


RUN apt-get clean autoclean
RUN apt-get autoremove -y


# enable go modules: https://github.com/golang/go/wiki/Modules
RUN export GO111MODULE=on

WORKDIR /engines

# install life
RUN git clone https://github.com/perlin-network/life
RUN cd life && go mod vendor
RUN cd life && go build


# install wagon
#RUN git clone https://github.com/go-interpreter/wagon
#RUN cd wagon/cmd/wasm-run && go build


# install rust
RUN curl https://sh.rustup.rs -sSf | \
    sh -s -- --default-toolchain stable -y && . $HOME/.cargo/env
ENV PATH=/root/.cargo/bin:$PATH

RUN rustup default 1.31.0


# install wasmi
RUN git clone https://github.com/paritytech/wasmi.git --recursive
#RUN cd wasmi && cargo build --release
RUN cd wasmi && cargo test --release


# install wavm
RUN git clone --single-branch --branch bench-compile-time https://github.com/cdetrio/WAVM
RUN mkdir wavm-build
RUN cd wavm-build && cmake -G Ninja ../WAVM -DCMAKE_BUILD_TYPE=RelWithDebInfo
RUN cd wavm-build && ninja



# install binaryen
#RUN git clone https://github.com/WebAssembly/binaryen.git
#RUN cd binaryen && cmake . && make


# install wasmer
# download wasmer binary
#RUN curl https://get.wasmer.io -sSfL | sh
#RUN /bin/bash -c "source /root/.wasmer/wasmer.sh"
# build wasmer from source
# latest wasmer release 0.1.4 is currently broken with recent rustc versions. use 1.31.0

# wasmer bench-release 0.1.4 has segmentation violation with 1.32.0
#RUN rustup default 1.32.0

RUN rustup default 1.31.1

#RUN git clone --single-branch --branch bench-compile-time https://github.com/cdetrio/wasmer.git
RUN git clone --single-branch --branch bench-release https://github.com/cdetrio/wasmer.git
#RUN cd wasmer && cargo install --path .
RUN cd wasmer && cargo build --release


# install wabt
RUN git clone --recursive --single-branch --branch bench-times https://github.com/cdetrio/wabt.git
RUN mkdir wabt/build && cd wabt/build && cmake .. && make


# install wagon
RUN git clone --single-branch --branch bench-times https://github.com/cdetrio/wagon
RUN cd wagon/cmd/wasm-run && go build


# install nodejs
#RUN mkdir node
RUN mkdir -p node
RUN cd node && curl -fsSLO --compressed https://nodejs.org/dist/v11.10.0/node-v11.10.0-linux-x64.tar.gz
RUN cd node && tar -xvf node-v11.10.0-linux-x64.tar.gz -C /usr/local/ --strip-components=1 --no-same-owner
#RUN ln -s /usr/local/bin/node /usr/local/bin/nodejs
RUN cd node && ln -s /usr/local/bin/node ./node
COPY node-timer.js ./node/node-timer.js


RUN pip3 install click durationpy


COPY ./wasmfiles /wasmfiles
COPY ./engine-bench /engine-bench
RUN mkdir -p /testresults

WORKDIR /engine-bench

CMD /bin/bash

