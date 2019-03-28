

## This script expects files to have _chiseled.wasm name.
# the precompile Makefile must be modified manually.

declare -a precnames=("bn128add" "bn128mul" "bn128pairing" "sha256" "modexp" "ecrecover")
declare -a wasmfiles=("ewasm_precompile_ecadd" "ewasm_precompile_ecmul" "ewasm_precompile_ecpairing" "ewasm_precompile_sha256" "ewasm_precompile_modexp" "ewasm_precompile_ecrecover")


WASM_FILE_DIR="/meterracer/wasm_to_meter/"

echo "copying wasm files to ${WASM_FILE_DIR}..."
cd /root/ewasm-precompiles/target/wasm32-unknown-unknown/release/
mkdir -p "${WASM_FILE_DIR}"

for filename in "${wasmfiles[@]}"
do
  cp "${filename}_chiseled.wasm" "${WASM_FILE_DIR}"
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
  /root/sentinel-minify-tool/wasm-utils/target/debug/wasm-minify "${filename}_chiseled.wasm" "$dest"
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


