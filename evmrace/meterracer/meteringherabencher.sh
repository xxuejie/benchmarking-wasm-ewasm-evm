#!/usr/bin/env bash


# go test -v ./core/vm/runtime/... -run TestCallEwasm --vm.ewasm="/root/hera/build/src/libhera.so,benchmark=true,engine=binaryen" --ewasmfile="/meterracer/wasm_to_meter/ewasm_precompile_ecpairing_minified.wasm" --input="00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed275dc4a288d1afb3cbb1ac09187524c7db36395df7be3b99e673b13a075a65ec1d9befcd05a5323e6da4d435f3b617cdb3af83285c2df711ef39c01571827f9d" --expected="0000000000000000000000000000000000000000000000000000000000000001" 



# TODO: checkout geth branch that uses statically linked hera


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


