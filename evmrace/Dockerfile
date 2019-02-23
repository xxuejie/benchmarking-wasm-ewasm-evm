FROM ubuntu:18.04

# https://github.com/kuralabs/docker-python3-dev/blob/master/Dockerfile

# System deps
RUN apt-get update
RUN apt-get install -y software-properties-common git sudo build-essential wget curl nano \
    autoconf automake cmake libtool make unzip zlib1g-dev texinfo \
    gcc musl-dev


# Install Go 1.11
RUN add-apt-repository ppa:longsleep/golang-backports && apt-get update && apt-get install -y golang-go


# download geth
RUN go get -u -v github.com/ethereum/go-ethereum
RUN cd /root/go/src/github.com/ethereum/go-ethereum && git checkout v1.8.23
RUN ln -s /root/go/src/github.com/ethereum/go-ethereum /go-ethereum
#COPY ./sha1_test.go /go-ethereum/core/vm/runtime/sha_test.go
#RUN cd /go-ethereum/core/vm/runtime && go test -bench BenchmarkSHA1 -benchtime 5s


COPY ./evmrace /evmrace
WORKDIR /evmrace

CMD /bin/bash