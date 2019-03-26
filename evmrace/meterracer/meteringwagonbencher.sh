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

[[ $(git log -1) =~ "31c3d4d08dee98a740d0c0db3b76fb0b54cf9c57" ]] || { echo "couldnt checkout geth ewasm-metering-bench branch!!"; exit 1; }


# output path should be mounted docker volume
OUTPUT_PATH="/evmraceresults"
OUTPUT_FILE_NAME="geth-wagon-metering-nosizeopt-benchmarks.csv"
CSV_FILE="${OUTPUT_PATH}/${OUTPUT_FILE_NAME}"


echo "installing chisel..."
cd /root
# chisel needed to make ewasm-precompiles
cargo install --version 0.1.0 chisel
# new version 0.2.0 not working



echo "compiling precompiles to wasm..."
cd /root

# for size optimized
# git clone --single-branch --branch no-usegas https://github.com/ewasm/ewasm-precompiles.git
# OUTPUT_FILE_NAME="geth-wagon-metering-size-optimized-benchmarks.csv"
# CSV_FILE="${OUTPUT_PATH}/${OUTPUT_FILE_NAME}"

# for nosizeopt
git clone --single-branch --branch no-sizeopt-no-usegas https://github.com/ewasm/ewasm-precompiles.git
OUTPUT_FILE_NAME="geth-wagon-metering-nosizeopt-benchmarks.csv"
CSV_FILE="${OUTPUT_PATH}/${OUTPUT_FILE_NAME}"

cd ewasm-precompiles

#git checkout a89d44ca5b8687fdf84a1ae718a61fc10d05de22 # Dec 22 2018 - has version problem with subtle
#git checkout f5e87b039afc9dbe4d7251dbe3fcd4656f626e0f # Jan 25 2019 - has 30x slowdown with basic block metering
#git checkout 1a829a34df071f54800a4a1efd305e090633924e # Feb 13 2019 - use panic and not revert - still has slowdown
#git checkout 49ce56446f74fa3512499399c4d2edfcaff20911 # Feb 13 2019 - size optimizations

make
# built wasm files at ewasm-precompiles/target/wasm32-unknown-unknown/release/


#declare -a precnames=("bn128add" "bn128mul" "bn128pairing" "sha256" "modexp" "ecrecover")
#declare -a wasmfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_ecpairing" "ewasm_precompile_sha256" "ewasm_precompile_modexp" "ewasm_precompile_ecrecover")

# small set for testing
declare -a precnames=("bn128add" "bn128mul" "sha256")
declare -a wasmfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_sha256")


# WASM_FILE_DIR = "/meterracer/wasm_to_meter"

echo "moving wasm files to /meterracer/wasm_to_meter..."
cd /root/ewasm-precompiles/target/wasm32-unknown-unknown/release/
mkdir -p /meterracer/wasm_to_meter

for filename in "${wasmfiles[@]}"
do
  mv "${filename}.wasm" /meterracer/wasm_to_meter/
done



echo "building sentinel-rs branch minify-tool..."
cd /root
git clone --single-branch --branch minify-tool https://github.com/ewasm/sentinel-rs.git sentinel-minify-tool
# .cargo/config sets default build target to wasm
rm sentinel-minify-tool/.cargo/config
cd sentinel-minify-tool/wasm-utils/cli
cargo build --bin wasm-minify
# built binary sentinel-rs/wasm-utils/target/debug/wasm-minify

echo "minifying wasm files..."
cd /meterracer/wasm_to_meter
for filename in "${wasmfiles[@]}"
do
  dest="${filename}_minified.wasm"
  /root/sentinel-minify-tool/wasm-utils/target/debug/wasm-minify "${filename}.wasm" "$dest"
done


echo "copying minified as unmetered..."
cd /meterracer/wasm_to_meter
for filename in "${wasmfiles[@]}"
do
  src="${filename}_minified.wasm"
  dest="${filename}_unmetered.wasm"
  cp "$src" "$dest"
done



declare -a sentinelrepobranches=("basicblock-metering" "superblock-metering" "inline-basic-block" "inline-super-block")
declare -a sentineldirs=("sentinel-basicblock-metering" "sentinel-superblock-metering" "sentinel-inlinebasic-metering" "sentinel-inlinesuper-metering")

# build metering injectors

for i in "${!sentinelrepobranches[@]}"
do
  echo "building sentinel-rs branch ${sentinelrepobranches[i]}..."
  cd /root
  git clone --single-branch --branch ${sentinelrepobranches[i]} https://github.com/ewasm/sentinel-rs.git ${sentineldirs[i]}
  # .cargo/config sets default build target to wasm
  rm ${sentineldirs[i]}/.cargo/config
  cd ${sentineldirs[i]}/wasm-utils/cli
  cargo build --bin wasm-gas
done


declare -a meteringinjectiontypes=("basicblock" "superblock" "inlinebasic" "inlinesuper")

# inject metering into minified wasm files

for i in "${!meteringinjectiontypes[@]}"
do
  echo "injecting ${meteringinjectiontypes[i]} metering into wasm files..."
  sentinelbin="/root/${sentineldirs[i]}/wasm-utils/target/debug/wasm-gas"

  cd /meterracer/wasm_to_meter
  for filename in "${wasmfiles[@]}"
  do
    src="${filename}_minified.wasm"
    dest="${filename}_${meteringinjectiontypes[i]}.wasm"
    sentinelcmd="${sentinelbin} ${src} ${dest}"
    eval $sentinelcmd
  done

done




# run benchmarks on unmetered and metered wasm files

declare -a meteredfiletypes=("unmetered" "basicblock" "superblock" "inlinebasic" "inlinesuper")
declare -a meteringsuffixes=("no-metering" "metered-basic-block" "metered-super-block" "metered-inline-basic" "metered-inline-super")

# backup existing result file
if [ -f "$CSV_FILE" ]; then
  echo "backing up existing file at ${CSV_FILE}..."
  mkdir -p "${OUTPUT_PATH}/backups"
  timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
  dest="${OUTPUT_PATH}/backups/${timestamp}-${OUTPUT_FILE_NAME}"
  mv "${CSV_FILE}" "${dest}"
fi


for i in "${!meteredfiletypes[@]}"
do
  echo "benchmarking ${meteredfiletypes[i]} on geth wagon..."

  cd /meterracer
  csvname="${CSV_FILE}"
  rungocmd="python3 rungethwagonbench.py --wasm_dir=\"/meterracer/wasm_to_meter/\" --name_suffix=\"${meteringsuffixes[i]}\" --csv_name=\"${csvname}\""

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

