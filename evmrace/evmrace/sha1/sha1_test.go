// based on go-ethereum/core/vm/runtime/runtime_test.go

package runtime

import (
	"strings"
	"testing"
	"fmt"
	
	"github.com/ethereum/go-ethereum/accounts/abi"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/state"
	"github.com/ethereum/go-ethereum/core/vm"
	"github.com/ethereum/go-ethereum/ethdb"
)


/*
// derived from https://github.com/ensdomains/solsha1/blob/master/contracts/SHA1.sol
// deployed ENS code at: https://etherscan.io/address/0x4e89a683dade995736457bde623e75f5840c2d34#code

// compiled with solc version:0.5.4+commit.9549d8ff.Emscripten.clang with optimizer enabled

pragma solidity ^0.5.1;

contract SHA1 {

    function sha1(bytes memory data) public pure returns(bytes20 ret) {
        assembly {
            // Get a safe scratch location
            let scratch := mload(0x40)

            // Get the data length, and point data at the first byte
            let len := mload(data)
            data := add(data, 32)

            // Find the length after padding
            let totallen := add(and(add(len, 1), 0xFFFFFFFFFFFFFFC0), 64)
            switch lt(sub(totallen, len), 9)
            case 1 { totallen := add(totallen, 64) }

            let h := 0x6745230100EFCDAB890098BADCFE001032547600C3D2E1F0

            function readword(ptr, off, count) -> result {
                result := 0
                if lt(off, count) {
                    result := mload(add(ptr, off))
                    count := sub(count, off)
                    if lt(count, 32) {
                        let mask := not(sub(exp(256, sub(32, count)), 1))
                        result := and(result, mask)
                    }
                }
            }

            for { let i := 0 } lt(i, totallen) { i := add(i, 64) } {
                mstore(scratch, readword(data, i, len))
                mstore(add(scratch, 32), readword(data, add(i, 32), len))

                // If we loaded the last byte, store the terminator byte
                switch lt(sub(len, i), 64)
                case 1 { mstore8(add(scratch, sub(len, i)), 0x80) }

                // If this is the last block, store the length
                switch eq(i, sub(totallen, 64))
                case 1 { mstore(add(scratch, 32), or(mload(add(scratch, 32)), shl(3, len))) }

                // Expand the 16 32-bit words into 80
                for { let j := 64 } lt(j, 128) { j := add(j, 12) } {
                    let temp := xor(xor(mload(add(scratch, sub(j, 12))), mload(add(scratch, sub(j, 32)))), xor(mload(add(scratch, sub(j, 56))), mload(add(scratch, sub(j, 64)))))
                    temp := or(and(shl(1, temp), 0xFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFE), and(shr(31, temp), 0x0000000100000001000000010000000100000001000000010000000100000001))
                    mstore(add(scratch, j), temp)
                }
                for { let j := 128 } lt(j, 320) { j := add(j, 24) } {
                    let temp := xor(xor(mload(add(scratch, sub(j, 24))), mload(add(scratch, sub(j, 64)))), xor(mload(add(scratch, sub(j, 112))), mload(add(scratch, sub(j, 128)))))
                    temp := or(and(shl(2, temp), 0xFFFFFFFCFFFFFFFCFFFFFFFCFFFFFFFCFFFFFFFCFFFFFFFCFFFFFFFCFFFFFFFC), and(shr(30, temp), 0x0000000300000003000000030000000300000003000000030000000300000003))
                    mstore(add(scratch, j), temp)
                }

                let x := h
                let f := 0
                let k := 0
                for { let j := 0 } lt(j, 80) { j := add(j, 1) } {
                    switch div(j, 20)
                    case 0 {
                        // f = d xor (b and (c xor d))
                        f := xor(shr(80, x), shr(40, x))
                        f := and(shr(120, x), f)
                        f := xor(shr(40, x), f)
                        k := 0x5A827999
                    }
                    case 1{
                        // f = b xor c xor d
                        f := xor(shr(120, x), shr(80, x))
                        f := xor(shr(40, x), f)
                        k := 0x6ED9EBA1
                    }
                    case 2 {
                        // f = (b and c) or (d and (b or c))
                        f := or(shr(120, x), shr(80, x))
                        f := and(shr(40, x), f)
                        f := or(and(shr(120, x), shr(80, x)), f)
                        k := 0x8F1BBCDC
                    }
                    case 3 {
                        // f = b xor c xor d
                        f := xor(shr(120, x), shr(80, x))
                        f := xor(shr(40, x), f)
                        k := 0xCA62C1D6
                    }
                    // temp = (a leftrotate 5) + f + e + k + w[i]
                    let temp := and(shr(187, x), 0x1F)
                    temp := or(and(shr(155, x), 0xFFFFFFE0), temp)
                    temp := add(f, temp)
                    temp := add(and(x, 0xFFFFFFFF), temp)
                    temp := add(k, temp)
                    temp := add(shr(224, mload(add(scratch, shl(2, j)))), temp)
                    //x := or(div(x, 0x10000000000), mul(temp, 0x10000000000000000000000000000000000000000))
                    x := or(shr(40, x), shl(160, temp))
                    x := or(and(x, 0xFFFFFFFF00FFFFFFFF000000000000FFFFFFFF00FFFFFFFF), shl(80, or(and(shr(50, x), 0xC0000000), and(shr(82, x), 0x3FFFFFFF))))
                }

                h := and(add(h, x), 0xFFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF00FFFFFFFF)
            }
            ret := shl(96, or(or(or(or(and(shr(32, h), 0xFFFFFFFF00000000000000000000000000000000), and(shr(24, h), 0xFFFFFFFF000000000000000000000000)), and(shr(16, h), 0xFFFFFFFF0000000000000000)), and(shr(8, h), 0xFFFFFFFF00000000)), and(h, 0xFFFFFFFF)))
        }
        
    }
}

*/


func BenchmarkSha1_plain(b *testing.B) {
	var definition = `[{"constant":true,"inputs":[{"name":"data","type":"bytes"}],"name":"sha1","outputs":[{"name":"ret","type":"bytes20"}],"payable":false,"stateMutability":"pure","type":"function"}]`;

	var code = common.Hex2Bytes("608060405234801561001057600080fd5b5060043610610047577c010000000000000000000000000000000000000000000000000000000060003504631605782b811461004c575b600080fd5b6100f26004803603602081101561006257600080fd5b81019060208101813564010000000081111561007d57600080fd5b82018360208201111561008f57600080fd5b803590602001918460018302840111640100000000831117156100b157600080fd5b91908080601f016020809104026020016040519081016040528093929190818152602001838380828437600092019190915250929550610114945050505050565b604080516bffffffffffffffffffffffff199092168252519081900360200190f35b60006040518251602084019350604067ffffffffffffffc0600183011601600982820310600181146101455761014c565b6040820191505b50776745230100efcdab890098badcfe001032547600c3d2e1f061019f565b600083831015610198575080820151928290039260208410156101985760001960208590036101000a0119165b9392505050565b60005b82811015610565576101b584828961016b565b85526101c584602083018961016b565b6020860152604081850310600181146101dd576101e6565b60808286038701535b50604083038114600181146101fa57610208565b602086018051600887021790525b5060405b608081101561029057858101603f19810151603719820151601f19830151600b198401516002911891909218189081027ffffffffefffffffefffffffefffffffefffffffefffffffefffffffefffffffe1663800000009091047c010000000100000001000000010000000100000001000000010000000116179052600c0161020c565b5060805b61014081101561031957858101607f19810151606f19820151603f198301516017198401516004911891909218189081027ffffffffcfffffffcfffffffcfffffffcfffffffcfffffffcfffffffcfffffffc1663400000009091047c030000000300000003000000030000000300000003000000030000000316179052601801610294565b508160008060005b605081101561053b57601481048015610351576001811461038d57600281146103c757600381146104065761043c565b6501000000000085046a0100000000000000000000860481186f01000000000000000000000000000000870416189350635a827999925061043c565b6501000000000085046f0100000000000000000000000000000086046a0100000000000000000000870418189350636ed9eba1925061043c565b6a010000000000000000000085046f010000000000000000000000000000008604818117650100000000008804169116179350638f1bbcdc925061043c565b6501000000000085046f0100000000000000000000000000000086046a010000000000000000000087041818935063ca62c1d692505b50601f770800000000000000000000000000000000000000000000008504168063ffffffe073080000000000000000000000000000000000000087041617905080840190508063ffffffff86160190508083019050807c0100000000000000000000000000000000000000000000000000000000600484028c0151040190507401000000000000000000000000000000000000000081026501000000000086041794506a0100000000000000000000633fffffff6a040000000000000000000087041663c00000006604000000000000880416170277ffffffff00ffffffff000000000000ffffffff00ffffffff861617945050600181019050610321565b5050509190910177ffffffff00ffffffff00ffffffff00ffffffff00ffffffff16906040016101a2565b506c0100000000000000000000000063ffffffff821667ffffffff000000006101008404166bffffffff0000000000000000620100008504166fffffffff000000000000000000000000630100000086041673ffffffff00000000000000000000000000000000640100000000870416171717170294505050505091905056fea165627a7a723058209b8907beefa8788cefc9b87aab1aa045aa08b0534449e5e0664be20e54e004fc0029")

	abi, err := abi.JSON(strings.NewReader(definition))
	if err != nil {
		b.Fatal(err)
	}

	// sha1 test vectors from https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/secure-hashing#shavs
	// FIPS 180-4 "SHA Test Vectors for Hashing Byte-Oriented Messages"

	input := common.Hex2Bytes("{{input}}")
	// contract returns padded bytes "a94d7bf363f32a5a5b6e9f71b2edaa3f2ae31a61000000000000000000000000"
	expected := "{{expected}}000000000000000000000000"

	calldata, err := abi.Pack("sha1", input)

	if err != nil {
		b.Fatal(err)
	}

	var cfg = new(Config)
	setDefaults(cfg)
	cfg.State, _ = state.New(common.Hash{}, state.NewDatabase(ethdb.NewMemDatabase()))

	var (
		address = common.BytesToAddress([]byte("contract"))
		vmenv   = NewEnv(cfg)
		sender  = vm.AccountRef(cfg.Origin)
	)

	cfg.State.CreateAccount(address)
	cfg.State.SetCode(address, code)

	var (
		ret  []byte
		exec_err  error
		leftOverGas uint64
	)
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ret, leftOverGas, exec_err = vmenv.Call(sender, address, calldata, cfg.GasLimit, cfg.Value)
	}
	b.StopTimer()

	gasUsed := cfg.GasLimit - leftOverGas

	if exec_err != nil {
		b.Error(exec_err)
		return
	}
	if common.Bytes2Hex(ret) != expected {
		b.Error(fmt.Sprintf("Expected %v, got %v", expected, common.Bytes2Hex(ret)))
		return
	}
	fmt.Println("gasUsed:", gasUsed)

}
