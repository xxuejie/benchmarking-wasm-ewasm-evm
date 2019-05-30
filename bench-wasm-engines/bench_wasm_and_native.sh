#!/usr/bin/env bash

# first compile standalone wasm files from rust code, and benchmark native rust
# later, benchmark the standalone wasm files in all the wasm engines


# output path should be mounted docker volumes
# /testresults

WASM_FILE_DIR=/wasmfiles
CSV_RESULTS=/testresults/native_benchmarks.csv
RUST_CODE_DIR=./rust-code
INPUT_VECTORS_DIR=./inputvectors

python3.7 benchnativerust_prepwasm.py --wasmoutdir="${WASM_FILE_DIR}" --csvresults="${CSV_RESULTS}" --rustcodedir="${RUST_CODE_DIR}" --inputvectorsdir="${INPUT_VECTORS_DIR}"



# minify standalone wasm files before benching them.

WASM_MINIFIED_DIR=/wasmfilesminified

echo "building sentinel-rs branch minify-tool..."
cd /root
git clone --single-branch --branch minify-tool https://github.com/ewasm/sentinel-rs.git sentinel-minify-tool
# .cargo/config sets default build target to wasm
rm sentinel-minify-tool/.cargo/config
cd sentinel-minify-tool/wasm-utils/cli
cargo build --bin wasm-minify
# built binary sentinel-rs/wasm-utils/target/debug/wasm-minify

echo "minifying wasm files..."
mkdir -p ${WASM_MINIFIED_DIR}
cd "${WASM_FILE_DIR}"
for filename in *.wasm
do
  dest="${WASM_MINIFIED_DIR}/${filename}"
  /root/sentinel-minify-tool/wasm-utils/target/debug/wasm-minify "${filename}" "$dest"
done




python3.7 main.py --wasmdir="/wasmfilesminified" --csvfile="/testresults/standalone_wasm_results.csv" |& tee wasm-engines-run1.log
