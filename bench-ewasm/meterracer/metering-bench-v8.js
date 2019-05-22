var args = process.argv.slice(2);
//console.log('args:', args);
var wasmfile = args[0];
var input = args[1];
var expected = args[2];

if (args.length < 3) {
  console.log('missing an arg!');
  process.exit(1);
}

//console.log('---- reading wasm file..')
const readAsBinary = filename => {
if (typeof process === 'object' && typeof require === 'function') {
    const binary = require('fs').readFileSync(filename);
    return !binary.buffer ? new Uint8Array(binary) : binary;
} else
    return typeof readbuffer === 'function'
        ? new Uint8Array(readbuffer(filename))
        : read(filename, 'binary');
};

const wasmBytes = readAsBinary(wasmfile)

//console.log('---- wasm file read.')

let totalGasUsed = BigInt(0);
let useGasCalls = 0;
let exported_mem;

const inputHex = input;
const inputBytes = new Uint8Array(Math.ceil(inputHex.length / 2));

function getCallDataSize() {
  // console.log('returning call data size:', inputBytes.length);
  return inputBytes.length;
}

function useGas(a) {
  //console.log('useGas a:', a)
  totalGasUsed = totalGasUsed + a;
  useGasCalls = useGasCalls + 1;
}

function callDataCopy(resultOffset, dataOffset, length) {
  //console.log('callDataCopy:', resultOffset, dataOffset, length)

  const copyBytes = new Uint8Array(length);

  for (var i = 0; i < length; i++) copyBytes[i] = parseInt(inputHex.substr((dataOffset*2)+(i*2), 2), 16);

  const asBytes = new Uint8Array(exported_mem.buffer, resultOffset, length+1);
  asBytes.set(copyBytes);
}

function revert (dataOffset, dataLength) {
  console.log('revert dataOffset, dataLength', dataOffset, dataLength)
}

function finish (dataOffset, dataLength) {
  //console.log('finish', dataOffset, dataLength)

  const returnBytes = new Uint8Array(exported_mem.buffer, dataOffset, dataLength);

  let convertedBack = '';
  for (var i = 0; i < dataLength; i++) {
    if (returnBytes[i] < 16) convertedBack += '0';
    convertedBack += returnBytes[i].toString(16);
  }
  //console.log('gas left:', gasGlobal.value);
  //console.log('gas used:', totalGasUsed);
  //console.log('useGas calls:', useGasCalls);

  //console.log('as hex:', convertedBack);
  if (convertedBack !== expected) {
    console.error('Expected: ' + expected + '   got: '  + convertedBack);
    throw "incorrect return val!"
  }

  throw "finished normally!";
}


const imports = {
    ethereum: {
        'getCallDataSize': getCallDataSize,
        'useGas': useGas,
        'callDataCopy': callDataCopy,
        'finish': finish,
        'revert': revert
    },
    env: {}
};

imports.env.memory = new WebAssembly.Memory({ initial: 10 })

console.time('instantiate');
WebAssembly.instantiate(wasmBytes, imports)
  .then(r => {
    exported_mem = r.instance.exports.memory;
    gasGlobal = r.instance.exports['gas_global'];
    console.timeEnd('instantiate');
    console.time('exec');
    try {
      const mainreturn = r.instance.exports.main();
      console.timeEnd('exec');
      //console.log('---- main returned:', mainreturn);
    } catch (e) {
      console.timeEnd('exec');
      if (e == "finished normally!") {
        console.log('gas used:', totalGasUsed);
        console.log('useGas calls:', useGasCalls);
      } else {
        console.log('caught error:', e)
      }
    }
  });
