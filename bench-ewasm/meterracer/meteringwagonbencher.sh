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

[[ $(git log -1) =~ "48698e396e92c10041bddeee02122a79d0173709" ]] || { echo "couldnt checkout geth ewasm-metering-bench branch!!"; exit 1; }

#### *** note if wasm files are size optimized or not

# output path should be mounted docker volume
OUTPUT_PATH="/evmraceresults"
OUTPUT_FILE_NAME="geth-wagon-metering-nosizeopt-benchmarks.csv"
CSV_FILE="${OUTPUT_PATH}/${OUTPUT_FILE_NAME}"


WASM_PATH="/meterracer/wasm_to_meter/"


# backup existing result file
if [ -f "$CSV_FILE" ]; then
  echo "backing up existing file at ${CSV_FILE}..."
  mkdir -p "${OUTPUT_PATH}/backups"
  timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
  dest="${OUTPUT_PATH}/backups/${timestamp}-${OUTPUT_FILE_NAME}"
  mv "${CSV_FILE}" "${dest}"
fi


#declare -a precnames=("bn128add" "bn128mul" "bn128pairing" "sha256" "modexp" "ecrecover")
#declare -a wasmfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_ecpairing" "ewasm_precompile_sha256" "ewasm_precompile_modexp" "ewasm_precompile_ecrecover")

# small set for testing
declare -a precnames=("bn128add" "bn128mul" "sha256")
declare -a wasmfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_sha256")


declare -a meteredfiletypes=("unmetered" "basicblock" "superblock" "inlinebasic" "inlinesuper")
declare -a meteringsuffixes=("no-metering" "metered-basic-block" "metered-super-block" "metered-inline-basic" "metered-inline-super")

# run benchmarks on unmetered and metered wasm files

for i in "${!meteredfiletypes[@]}"
do
  echo "benchmarking ${meteredfiletypes[i]} on geth wagon..."

  cd /meterracer
  csvname=${CSV_FILE}
  rungocmd="python3 rungethwagonbench.py --wasm_dir=\"${WASM_PATH}\" --name_suffix=\"${meteringsuffixes[i]}\" --csv_name=\"${csvname}\""

  for j in "${!wasmfiles[@]}"
  do
    precarg="--${precnames[j]}=\"${wasmfiles[j]}_${meteredfiletypes[i]}.wasm\""
    rungocmd+=" ${precarg}"
  done

  # the blank line before or after the eval is needed, or bash breaks
  echo "running command: ${rungocmd}"
  eval $rungocmd

done




# python3 rungobench.py --wasm_dir="/meterracer/wasm_to_meter/" --name_suffix="no-metering" --sha256="ewasm_precompile_sha256_minified.wasm" --bn128add="ewasm_precompile_ecadd_minified.wasm" --bn128mul="ewasm_precompile_ecmul_minified.wasm" --bn128pairing="ewasm_precompile_ecpairing_minified.wasm" --modexp="ewasm_precompile_modexp_minified.wasm"

