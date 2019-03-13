#!/usr/bin/python

import os

header = """// Copyright 2019 The go-ethereum Authors
// This file is part of the go-ethereum library.
//
// The go-ethereum library is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// The go-ethereum library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with the go-ethereum library. If not, see <http://www.gnu.org/licenses/>.

package vm

"""


def prepare_go_file(wasmfiledir="wasm_to_meter/", wasmfile="", varname="", gofile=""):
  num_arr = []
  infilewasm = os.path.join(wasmfiledir, wasmfile)
  with open(infilewasm, "rb") as fin:
    while True:
      current_byte = fin.read(1)
      if (not current_byte):
        break
      val = ord(current_byte)
      num_arr.append(str(val))

  outfilego = os.path.join(wasmfiledir, gofile)
  fout = open(outfilego, 'w')
  fout.write(header)
  fout.write("var {} = []byte{{".format(varname))
  fout.write((", ").join(num_arr))
  fout.write("}")

