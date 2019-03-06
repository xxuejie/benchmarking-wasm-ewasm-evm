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


# download geth
RUN go get -u -v github.com/ethereum/go-ethereum
RUN cd /root/go/src/github.com/ethereum/go-ethereum && git checkout v1.8.23
RUN ln -s /root/go/src/github.com/ethereum/go-ethereum /go-ethereum
#COPY ./sha1_test.go /go-ethereum/core/vm/runtime/sha_test.go
#RUN cd /go-ethereum/core/vm/runtime && go test -bench BenchmarkSHA1 -benchtime 5s


# install evmone
RUN git clone --recursive https://github.com/chfast/evmone
RUN cd evmone && mkdir build
RUN cd evmone/build && cmake .. -DEVMONE_TESTING=ON
RUN cd evmone/build && cmake --build . -- -j
# /root/evmone/build/test/evmone-bench

# install python modules needed for benchmarking script
RUN pip3 install durationpy jinja2 pandas
# TODO: alias python to python3

RUN mkdir -p /evmraceresults
COPY ./evmrace /evmrace
WORKDIR /evmrace

CMD /bin/bash