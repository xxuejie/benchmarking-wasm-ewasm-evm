#!/usr/bin/env bash


# go test -v ./core/vm/runtime/... -bench BenchmarkCallEwasm --vm.ewasm="/root/hera/build/src/libhera.so,benchmark=true,engine=wabt" --ewasmfile="/meterracer/wasm_to_meter/ewasm_precompile_ecmul_unmetered.wasm" --input="070a8d6a982153cae4be29d434e8faef8a47b274a053f5a4ee2a6c9c13c31e5c031b8ce914eba3a9ffb989f9cdd5b0f01943074bf4f0f315690ec3cec6981afc30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd46" --expected="025a6f4181d2b4ea8b724290ffb40156eb0adb514c688556eb79cdea0752c2bb2eff3f31dea215f1eb86023a133a996eb6300b44da664d64251d05381bb8a02e" 



# checkout geth branch that uses statically linked hera
cd /root/go/src/github.com/ethereum/go-ethereum
git fetch ewasm
git checkout ewasm/evmc6-static-hera
[[ $(git log -1) =~ "e2453bb4c59fc0894c7d0ddfbc5dd1a2be2c3c57" ]] || { echo "couldnt checkout geth evmc6-static-hera branch!!"; exit 1; }

# TODO: make sure hera static libs are there


#declare -a functionfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_ecpairing" "ewasm_precompile_sha256" "ewasm_precompile_modexp" "ewasm_precompile_ecrecover")
#declare -a functionnames=("bn128add" "bn128mul" "bn128pairing" "sha256" "modexp" "ecrecover")

declare -a functionfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_ecpairing" "ewasm_precompile_modexp")
declare -a functionnames=("bn128_add" "bn128_mul" "bn128_pairing" "modexp")

declare -a meteringtypes=("unmetered" "basicblock" "superblock" "inlinebasic" "inlinesuper")
declare -a meteringsuffixes=("no-metering" "metered-basic-block" "metered-super-block" "metered-inline-basic" "metered-inline-super")


#/evmrace/bn128_add/bn128_add-inputs.json
#/evmrace/bn128_mul/bn128_mul-inputs.json
#/evmrace/bn128_pairing/bn128_pairing-inputs.json
#/evmrace/modexp/modexp-inputs.json

# TODO: copy sha256 inputs into json file
# TODO: copy ecrecover inputs into json file 




# output path should be mounted docker volume
OUTPUT_PATH="/evmraceresults"
OUTPUT_FILE_NAME="geth-hera-metering-benchmarks.csv"

CSV_FILE="${OUTPUT_PATH}/${OUTPUT_FILE_NAME}"

## TODO: check for existing csv file at output path..
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
  jsonfile="/evmrace/${functionnames[i]}/${functionnames[i]}-inputs.json"
  for j in "${!meteringtypes[@]}"
  do
    echo "benchmarking ${functionnames[i]} for metered type ${meteringtypes[j]} on geth hera..."
    wasmfile="/meterracer/wasm_to_meter/${functionfiles[i]}_${meteringtypes[j]}.wasm"

    gethherabenchcmd="python3 rungethherabench.py --testvectors=${jsonfile} --csvfile=${CSV_FILE} --testsuffix=\"${meteringsuffixes[j]}\" --wasmfile=${wasmfile}"
    echo "running command: ${gethherabenchcmd}"
    eval $gethherabenchcmd
  done
  echo "done benchmarking ${functionnames[i]} all metering types on geth hera."
done

# python3 rungethherabench.py --testsuffix --wasmfile --testvectors --csvfile 


