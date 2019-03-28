
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

### DO THIS STEP MANUALLY.  chisel keeps messing up.
# modify makefile to output _chiseled.wasm files


#git checkout a89d44ca5b8687fdf84a1ae718a61fc10d05de22 # Dec 22 2018 - has version problem with subtle
#git checkout f5e87b039afc9dbe4d7251dbe3fcd4656f626e0f # Jan 25 2019 - has 30x slowdown with basic block metering
#git checkout 1a829a34df071f54800a4a1efd305e090633924e # Feb 13 2019 - use panic and not revert - still has slowdown
#git checkout 49ce56446f74fa3512499399c4d2edfcaff20911 # Feb 13 2019 - size optimizations

make
# built wasm files at ewasm-precompiles/target/wasm32-unknown-unknown/release/

