

echo "installing chisel..."
cd /root
# chisel needed to make ewasm-precompiles
cargo install --version 0.1.0 chisel
# new version 0.2.0 not working

# chisel has broken before, when installed more than once
# it returns invalid argument

#root@cb198feb896c:~# /root/.cargo/bin/chisel --help
#Usage: /root/.cargo/bin/chisel in.wasm out.wasm

#root@cb198feb896c:~# ls -al /root/.cargo/bin/chisel
#-rwxr-xr-x 1 root root 2750288 Mar 26 22:24 /root/.cargo/bin/chisel


echo "compiling precompiles to wasm..."
cd /root

# for size optimized
# git clone --single-branch --branch no-usegas https://github.com/ewasm/ewasm-precompiles.git


# for nosizeopt
git clone --single-branch --branch no-sizeopt-no-usegas https://github.com/ewasm/ewasm-precompiles.git


cd ewasm-precompiles

#git checkout a89d44ca5b8687fdf84a1ae718a61fc10d05de22 # Dec 22 2018 - has version problem with subtle
#git checkout f5e87b039afc9dbe4d7251dbe3fcd4656f626e0f # Jan 25 2019 - has 30x slowdown with basic block metering
#git checkout 1a829a34df071f54800a4a1efd305e090633924e # Feb 13 2019 - use panic and not revert - still has slowdown
#git checkout 49ce56446f74fa3512499399c4d2edfcaff20911 # Feb 13 2019 - size optimizations

make
# built wasm files at ewasm-precompiles/target/wasm32-unknown-unknown/release/


declare -a precnames=("bn128add" "bn128mul" "bn128pairing" "sha256" "modexp" "ecrecover")
declare -a wasmfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_ecpairing" "ewasm_precompile_sha256" "ewasm_precompile_modexp" "ewasm_precompile_ecrecover")


WASM_FILE_DIR="/meterracer/wasm_to_meter/"

echo "copying wasm files to ${WASM_FILE_DIR}..."
cd /root/ewasm-precompiles/target/wasm32-unknown-unknown/release/
mkdir -p "${WASM_FILE_DIR}"

for filename in "${wasmfiles[@]}"
do
  cp "${filename}.wasm" "${WASM_FILE_DIR}"
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
cd "${WASM_FILE_DIR}"
for filename in "${wasmfiles[@]}"
do
  dest="${filename}_minified.wasm"
  /root/sentinel-minify-tool/wasm-utils/target/debug/wasm-minify "${filename}.wasm" "$dest"
done


echo "copying minified as unmetered..."
cd "${WASM_FILE_DIR}"
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

  cd "${WASM_FILE_DIR}"
  for filename in "${wasmfiles[@]}"
  do
    src="${filename}_minified.wasm"
    dest="${filename}_${meteringinjectiontypes[i]}.wasm"
    sentinelcmd="${sentinelbin} ${src} ${dest}"
    eval $sentinelcmd
  done

done


