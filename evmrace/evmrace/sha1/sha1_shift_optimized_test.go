package runtime

import (
	"strings"
	"testing"
	"fmt"
	"math/big"
	
	"github.com/ethereum/go-ethereum/accounts/abi"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/state"
	"github.com/ethereum/go-ethereum/core/vm"
	"github.com/ethereum/go-ethereum/ethdb"
	"github.com/ethereum/go-ethereum/params"
)


/*
// derived from https://github.com/ensdomains/solsha1/blob/master/contracts/SHA1.sol
// compiled with solc version:0.5.4+commit.9549d8ff.Emscripten.clang with optimizer enabled
// hand optimized to replace div and mul with shr and shl

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


func BenchmarkSha1_shift_optimized(b *testing.B) {
	var definition = `[{"constant":true,"inputs":[{"name":"data","type":"bytes"}],"name":"sha1","outputs":[{"name":"ret","type":"bytes20"}],"payable":false,"stateMutability":"pure","type":"function"}]`;

	var code = common.Hex2Bytes("608060405234801561001057600080fd5b506004361061002b5760003560e01c80631605782b14610030575b600080fd5b6100d66004803603602081101561004657600080fd5b81019060208101813564010000000081111561006157600080fd5b82018360208201111561007357600080fd5b8035906020019184600183028401116401000000008311171561009557600080fd5b91908080601f0160208091040260200160405190810160405280939291908181526020018383808284376000920191909152509295506100f8945050505050565b604080516bffffffffffffffffffffffff199092168252519081900360200190f35b60006040518251602084019350604067ffffffffffffffc06001830116016009828203106001811461012957610130565b6040820191505b50776745230100efcdab890098badcfe001032547600c3d2e1f0610183565b60008383101561017c5750808201519282900392602084101561017c5760001960208590036101000a0119165b9392505050565b60005b8281101561045c5761019984828961014f565b85526101a984602083018961014f565b6020860152604081850310600181146101c1576101ca565b60808286038701535b50604083038114600181146101de576101ee565b8460031b60208701511760208701525b5060405b608081101561027157858101603f19810151603719820151601f19830151600b1984015118911818600181901b7ffffffffefffffffefffffffefffffffefffffffefffffffefffffffefffffffe16601f9190911c7c010000000100000001000000010000000100000001000000010000000116179052600c016101f2565b5060805b6101408110156102f557858101607f19810151606f19820151603f1983015160171984015118911818600281901b7ffffffffcfffffffcfffffffcfffffffcfffffffcfffffffcfffffffcfffffffc16601e9190911c7c030000000300000003000000030000000300000003000000030000000316179052601801610275565b508160008060005b60508110156104325760148104801561032d576001811461034e576002811461036d5760038114610391576103ac565b602885901c605086901c8118607887901c16189350635a82799992506103ac565b8460501c8560781c189350838560281c189350636ed9eba192506103ac565b605085901c607886901c818117602888901c169116179350638f1bbcdc92506103ac565b8460501c8560781c189350838560281c18935063ca62c1d692505b50601f8460bb1c168063ffffffe086609b1c1617905080840190508063ffffffff86160190508083019050808260021b8b015160e01c0190508060a01b8560281c179450633fffffff8560521c1663c00000008660321c161760501b77ffffffff00ffffffff000000000000ffffffff00ffffffff8616179450506001810190506102fd565b5050509190910177ffffffff00ffffffff00ffffffff00ffffffff00ffffffff1690604001610186565b5063ffffffff811667ffffffff000000008260081c166bffffffff00000000000000008360101c166fffffffff0000000000000000000000008460181c1673ffffffff000000000000000000000000000000008560201c161717171760601b94505050505091905056fea165627a7a72305820227af8b272b9b0e3d345f580ebcde55f50e3e8b7ecafabffcadb92e55e4de68e0029")

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
	cfg.ChainConfig = &params.ChainConfig{
		ChainID:        big.NewInt(1),
		HomesteadBlock: new(big.Int),
		DAOForkBlock:   new(big.Int),
		DAOForkSupport: false,
		EIP150Block:    new(big.Int),
		EIP155Block:    new(big.Int),
		EIP158Block:    new(big.Int),
		ByzantiumBlock:  big.NewInt(0),
		ConstantinopleBlock: big.NewInt(0),
	}
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
