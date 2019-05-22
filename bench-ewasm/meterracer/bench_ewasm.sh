#!/usr/bin/env bash

WASM_FILE_DIR=/ewasmfiles
WASM_METERED_DIR=/ewasmfilesmetered


# Compile rust to wasm
cd /evmrace/ewasm-code
# TODO: loop over dirs when we have more
echo "compiling ewasm code..."
cd mul256
cargo build --release --lib --target wasm32-unknown-unknown
# wasm file is in target/wasm32-unknown-unknown/release/mul256_wasm.wasm


# Install chisel
# need to remove before installing, otherwise "invalid argument" error likely to occur
echo "installing chisel..."
rm /root/.cargo/bin/chisel
cargo install --version 0.1.0 chisel

# Chisel wasm file
mkdir -p ${WASM_FILE_DIR}
cd ${WASM_FILE_DIR}
chisel /evmrace/ewasm-code/mul256/target/wasm32-unknown-unknown/release/mul256_wasm.wasm ./mul256.wasm


echo "building sentinel-rs branch inline-super-block..."
cd /root
git clone --single-branch --branch inline-super-block https://github.com/ewasm/sentinel-rs.git sentinel-inline-super-block
# .cargo/config sets default build target to wasm
rm sentinel-inline-super-block/.cargo/config
cd sentinel-inline-super-block/wasm-utils/cli
cargo build --bin wasm-gas
# built binary sentinel-inline-super-standalone/wasm-utils/target/debug/wasm-gas

echo "injecting metering into wasm files..."
mkdir -p ${WASM_METERED_DIR}
dest="${WASM_METERED_DIR}/mul256.wasm"
cd "${WASM_FILE_DIR}"
/root/sentinel-inline-super-block/wasm-utils/target/debug/wasm-gas ./mul256.wasm "$dest"


# checkout geth branch that uses statically linked hera
cd /root/go/src/github.com/ethereum/go-ethereum
git remote add ewasm https://github.com/ewasm/go-ethereum
git fetch ewasm
git checkout ewasm/evmc6-static-hera
[[ $(git log -1) =~ "46902ddbd1d618a2683474d8179ad4a67cbdeb40" ]] || { echo "couldnt checkout geth evmc6-static-hera branch!!"; exit 1; }


CSV_DIR=/evmraceresults
CSV_NAME=ewasm_benchmarks.csv
CSV_FILE=/evmraceresults/ewasm_benchmarks.csv

## backup existing csv file at output path..
if [ -f "$CSV_FILE" ]; then
  echo "backing up existing file at ${CSV_FILE}..."
  mkdir -p "${CSV_DIR}/backups"
  timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
  dest="${CSV_DIR}/backups/${timestamp}-${CSV_NAME}"
  mv "${CSV_FILE}" "${dest}"
fi

jsonfile=/evmrace/inputvectors/mul256-inputs.json
wasmfile=/ewasmfilesmetered/mul256.wasm

cd /meterracer
ewasmbenchcmd="python3 runherav8bench.py --testvectors=${jsonfile} --csvfile=${CSV_FILE} --testsuffix=\"\" --wasmfile=${wasmfile} --v8interp=yes"
echo "running command: ${ewasmbenchcmd}"
eval $ewasmbenchcmd

# python3 runherav8bench.py --testvectors=/evmrace/inputvectors/mul256-inputs.json --csvfile=/evmraceresults/ewasm_benchmarks.csv --testsuffix="" --wasmfile=/ewasmfilesmetered/mul256.wasm
