#!/usr/bin/env bash


# checkout geth branch that uses statically linked hera
cd /root/go/src/github.com/ethereum/go-ethereum
git remote add ewasm https://github.com/ewasm/go-ethereum
git fetch ewasm
git checkout ewasm/evmc6-static-hera
[[ $(git log -1) =~ "46902ddbd1d618a2683474d8179ad4a67cbdeb40" ]] || { echo "couldnt checkout geth evmc6-static-hera branch!!"; exit 1; }

# TODO: make sure hera static libs are there


#### *** note if wasm files are size optimized or not

WASM_PATH="/meterracer/wasm_to_meter/"

# output path should be mounted docker volume
OUTPUT_PATH="/evmraceresults"
OUTPUT_FILE_NAME="hera-v8-metering-nosizeopt-benchmarks.csv"

CSV_FILE="${OUTPUT_PATH}/${OUTPUT_FILE_NAME}"


# full set
#declare -a functionfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_ecpairing" "ewasm_precompile_modexp" "ewasm_precompile_sha256" "ewasm_precompile_ecrecover")
#declare -a functionnames=("bn128_add" "bn128_mul" "bn128_pairing" "modexp" "sha256" "ecrecover")

# small set for testing
declare -a functionfiles=("ewasm_precompile_modexp" "ewasm_precompile_sha256" "ewasm_precompile_ecrecover")
declare -a functionnames=("modexp" "sha256" "ecrecover")

declare -a meteringtypes=("unmetered" "basicblock" "superblock" "inlinebasic" "inlinesuper")
declare -a meteringsuffixes=("no-metering" "metered-basic-block" "metered-super-block" "metered-inline-basic" "metered-inline-super")



## backup existing csv file at output path..
if [ -f "$CSV_FILE" ]; then
  echo "backing up existing file at ${CSV_FILE}..."
  mkdir -p "${OUTPUT_PATH}/backups"
  timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
  dest="${OUTPUT_PATH}/backups/${timestamp}-${OUTPUT_FILE_NAME}"
  mv "${CSV_FILE}" "${dest}"
fi


cd /meterracer
for i in "${!functionnames[@]}"
do
  echo "start benchmarking ${functionnames[i]} all metering types on geth hera..."
  jsonfile="/evmrace/inputvectors/${functionnames[i]}-inputs.json"
  for j in "${!meteringtypes[@]}"
  do
    echo "benchmarking ${functionnames[i]} for metered type ${meteringtypes[j]} on geth hera..."
    wasmfile="${WASM_PATH}${functionfiles[i]}_${meteringtypes[j]}.wasm"

    gethherabenchcmd="python3 runherav8bench.py --testvectors=${jsonfile} --csvfile=${CSV_FILE} --testsuffix=\"${meteringsuffixes[j]}\" --wasmfile=${wasmfile}"
    echo "running command: ${gethherabenchcmd}"
    eval $gethherabenchcmd
  done
  echo "done benchmarking ${functionnames[i]} all metering types on geth hera."
done

# python3 rungethherabench.py --testsuffix --wasmfile --testvectors --csvfile 


