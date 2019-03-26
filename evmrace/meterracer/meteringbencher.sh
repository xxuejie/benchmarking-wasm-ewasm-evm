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



echo "compiling precompiles to wasm..."
cd /root
git clone --single-branch --branch no-usegas https://github.com/ewasm/ewasm-precompiles.git
cd ewasm-precompiles


#git checkout a89d44ca5b8687fdf84a1ae718a61fc10d05de22 # Dec 22 2018
#git checkout f5e87b039afc9dbe4d7251dbe3fcd4656f626e0f # Jan 25 2019
# ecrecover and modexp not ready yet
#git checkout 7443316a8d24b7e9434f65c1bb6df69eb2eee740 # Feb 13 2019

#git checkout a89d44ca5b8687fdf84a1ae718a61fc10d05de22 # Dec 22 2018 - has version problem with subtle
#git checkout f5e87b039afc9dbe4d7251dbe3fcd4656f626e0f # Jan 25 2019 - has 30x slowdown with basic block metering

git checkout 1a829a34df071f54800a4a1efd305e090633924e # Feb 13 2019 - use panic and not revert - still has slowdown

# git checkout 49ce56446f74fa3512499399c4d2edfcaff20911 # Feb 13 2019 - size optimizations

#git checkout 7443316a8d24b7e9434f65c1bb6df69eb2eee740 # Feb 13 2019


make
# built wasm files at ewasm-precompiles/target/wasm32-unknown-unknown/release/
# ewasm_precompile_ecadd.wasm
# ewasm_precompile_ecmul.wasm
# ewasm_precompile_ecpairing.wasm
# modexp needed too


declare -a precnames=("bn128add" "bn128mul" "bn128pairing" "sha256" "modexp" "ecrecover")
declare -a wasmfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_ecpairing" "ewasm_precompile_sha256" "ewasm_precompile_modexp" "ewasm_precompile_ecrecover")

#declare -a precnames=("bn128add" "bn128mul" "sha256")
#declare -a wasmfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_sha256")


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

cd /meterracer
csvname="metering_precompile_benchmarks_unmetered.csv"
rungocmd="python3 rungobench.py --wasm_dir=\"/meterracer/wasm_to_meter/\" --name_suffix=\"no-metering\" --csv_name=\"${csvname}\""
suffix="minified"
for i in "${!wasmfiles[@]}"
do
  precarg="--${precnames[i]}=\"${wasmfiles[i]}_minified.wasm\""
  rungocmd+=" ${precarg}"
done
echo "running command: ${rungocmd}"
eval $rungocmd




echo "building sentinel-rs branch inline-finish-with-gas..."
cd /root
git clone --single-branch --branch inline-finish-with-gas https://github.com/ewasm/sentinel-rs.git sentinel-inline-metering
# .cargo/config sets default build target to wasm
rm sentinel-inline-metering/.cargo/config
cd sentinel-inline-metering/wasm-utils/cli
cargo build --bin wasm-gas

echo "injecting inline metering into wasm files..."
cd /meterracer/wasm_to_meter
for filename in "${wasmfiles[@]}"
do
  src="${filename}_minified.wasm"
  dest="${filename}_inline_metered.wasm"
  /root/sentinel-inline-metering/wasm-utils/target/debug/wasm-gas "${filename}.wasm" "$dest"
done

cd /meterracer
csvname="metering_precompile_benchmarks_inline.csv"
rungocmd="python3 rungobench.py --wasm_dir=\"/meterracer/wasm_to_meter/\" --name_suffix=\"metered-inline\" --csv_name=\"${csvname}\""
#suffix="minified"
for i in "${!wasmfiles[@]}"
do
  precarg="--${precnames[i]}=\"${wasmfiles[i]}_inline_metered.wasm\""
  rungocmd+=" ${precarg}"
done
echo "running command: ${rungocmd}"
eval $rungocmd





echo "building sentinel-rs branch basicblock-metering..."
cd /root
git clone --single-branch --branch basicblock-metering https://github.com/ewasm/sentinel-rs.git sentinel-basicblock-metering
# .cargo/config sets default build target to wasm
rm sentinel-basicblock-metering/.cargo/config
cd sentinel-basicblock-metering/wasm-utils/cli
cargo build --bin wasm-gas

echo "injecting basic-block metering into wasm files..."
cd /meterracer/wasm_to_meter
for filename in "${wasmfiles[@]}"
do
  src="${filename}_minified.wasm"
  dest="${filename}_basicblock_metered.wasm"
  /root/sentinel-basicblock-metering/wasm-utils/target/debug/wasm-gas "${filename}.wasm" "$dest"
done

cd /meterracer
csvname="metering_precompile_benchmarks_basicblock.csv"
rungocmd="python3 rungobench.py --wasm_dir=\"/meterracer/wasm_to_meter/\" --name_suffix=\"metered-basic-block\" --csv_name=\"${csvname}\""
#suffix="minified"
for i in "${!wasmfiles[@]}"
do
  precarg="--${precnames[i]}=\"${wasmfiles[i]}_basicblock_metered.wasm\""
  rungocmd+=" ${precarg}"
done
echo "running command: ${rungocmd}"
eval $rungocmd




echo "building sentinel-rs branch superblock-metering..."
cd /root
git clone --single-branch --branch superblock-metering https://github.com/ewasm/sentinel-rs.git sentinel-superblock-metering
# .cargo/config sets default build target to wasm
rm sentinel-superblock-metering/.cargo/config
cd sentinel-superblock-metering/wasm-utils/cli
cargo build --bin wasm-gas

echo "injecting super-block metering into wasm files..."
cd /meterracer/wasm_to_meter
for filename in "${wasmfiles[@]}"
do
  src="${filename}_minified.wasm"
  dest="${filename}_superblock_metered.wasm"
  /root/sentinel-superblock-metering/wasm-utils/target/debug/wasm-gas "${filename}.wasm" "$dest"
done

cd /meterracer
csvname="metering_precompile_benchmarks_superblock.csv"
rungocmd="python3 rungobench.py --wasm_dir=\"/meterracer/wasm_to_meter/\" --name_suffix=\"metered-super-block\" --csv_name=\"${csvname}\""
#suffix="minified"
for i in "${!wasmfiles[@]}"
do
  precarg="--${precnames[i]}=\"${wasmfiles[i]}_superblock_metered.wasm\""
  rungocmd+=" ${precarg}"
done
echo "running command: ${rungocmd}"
eval $rungocmd





#python3 rungobench.py --wasm_dir="/meterracer/wasm_to_meter/" --name_suffix="no-metering" --sha256="ewasm_precompile_sha256_minified.wasm" --bn128add="ewasm_precompile_ecadd_minified.wasm" --bn128mul="ewasm_precompile_ecmul_minified.wasm" --bn128pairing="ewasm_precompile_ecpairing_minified.wasm" --modexp="ewasm_precompile_modexp_minified.wasm"


