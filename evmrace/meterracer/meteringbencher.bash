#!/usr/bin/env bash

echo "getting wagon and switching to branch restart-vm..."
mkdir -p /root/go
cd /root/go
go get github.com/go-interpreter/wagon
cd src/github.com/go-interpreter/wagon
git remote add gballet https://github.com/gballet/wagon.git
git fetch gballet
git checkout vm-restart

#RUN cd /root/go/src/github.com/ethereum/go-ethereum && git checkout v1.8.23
#RUN ln -s /root/go/src/github.com/ethereum/go-ethereum /go-ethereum

echo "getting go-ethereum and switching to branch ewasm-metering-bench..."
cd /root/go
go get github.com/ethereum/go-ethereum
cd src/github.com/ethereum/go-ethereum
git remote add cdetrio https://github.com/cdetrio/go-ethereum.git
git fetch cdetrio
git checkout ewasm-metering-bench


echo "installing chisel..."
cd /root
# chisel needed to make ewasm-precompiles
cargo install chisel


echo "building sentinel-rs branch gas-bin-util..."
cd /root
git clone --single-branch --branch gas-bin-util https://github.com/ewasm/sentinel-rs.git
cd sentinel-rs/wasm-utils/cli
cargo build --bin wasm-gas
# built binary sentinel-rs/wasm-utils/target/debug/wasm-gas



echo "compiling precompiles to wasm..."
cd /root
git clone https://github.com/ewasm/ewasm-precompiles.git
cd ewasm-precompiles
#git checkout a89d44ca5b8687fdf84a1ae718a61fc10d05de22 # Dec 22 2018
git checkout f5e87b039afc9dbe4d7251dbe3fcd4656f626e0f # Jan 25 2019
# ecrecover and modexp not ready yet
#git checkout 7443316a8d24b7e9434f65c1bb6df69eb2eee740 # Feb 13 2019
make
# built wasm files at ewasm-precompiles/target/wasm32-unknown-unknown/release/
# ewasm_precompile_ecadd.wasm
# ewasm_precompile_ecmul.wasm
# ewasm_precompile_ecpairing.wasm
# modexp needed too



declare -a wasmfiles=("ewasm_precompile_ecadd.wasm" "ewasm_precompile_ecmul.wasm" "ewasm_precompile_ecpairing.wasm" "ewasm_precompile_sha256.wasm")

# WASM_FILE_DIR = "/meterracer/wasm_to_meter"

echo "moving wasm files to /root/wasm_to_meter..."
cd /root/ewasm-precompiles/target/wasm32-unknown-unknown/release/
mkdir -p /meterracer/wasm_to_meter

for i in "${wasmfiles[@]}"
do
  mv "$i" /meterracer/wasm_to_meter/
done


# TODO: minify wasm files using https://github.com/ewasm/sentinel-rs/tree/minify-tool


#
# Do things in python from here??
#

echo "injecting metering into wasm files..."
cd /meterracer/wasm_to_meter
for i in "${wasmfiles[@]}"
do
  dest="$i.metered"
  /root/sentinel-rs/wasm-utils/target/debug/wasm-gas "$i" "$dest"
done



#cd /meterracer
#python3 metered_to_go.py



#mkdir -p gofiles
#mv /meterracer/wasm_to_meter/*.go /meterracer/gofiles

# move .go files to go-ethereum directory
# mv ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go.backup
# cp /meterracer/gofiles/ewasm_precompile_ecadd.go ~/go/src/github.com/ethereum/go-ethereum/core/vm/

# cd ~/go/src/github.com/ethereum/go-ethereum/core/vm/
# go test -v -bench BenchmarkPrecompiledBn256Add -benchtime 5s

# mv ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go.backup ~/go/src/github.com/ethereum/go-ethereum/core/vm/ewasm_precompile_ecadd.go
