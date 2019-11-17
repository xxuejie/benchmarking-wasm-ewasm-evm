#include "bn256g2.hpp"

using intx::uint256;
using intx::from_string;

using ckb::IX;
using ckb::IY;

#define CHECK_LEN(x) if ((x) <= 0) { return x; }

int main(int argc, char* argv[]) {
  if (argc != 10) {
    return -1;
  }

  uint256 s = from_string<uint256>(argv[1]);
  uint256 pt1[2][2], r[2][2], expected[2][2];
  pt1[IX][IX] = from_string<uint256>(argv[2]);
  pt1[IX][IY] = from_string<uint256>(argv[3]);
  pt1[IY][IX] = from_string<uint256>(argv[4]);
  pt1[IY][IY] = from_string<uint256>(argv[5]);

  expected[IX][IX] = from_string<uint256>(argv[6]);
  expected[IX][IY] = from_string<uint256>(argv[7]);
  expected[IY][IX] = from_string<uint256>(argv[8]);
  expected[IY][IY] = from_string<uint256>(argv[9]);

  ckb::ec_twist_mul(s, pt1, r);

  if (r[IX][IX] != expected[IX][IX] ||
      r[IX][IY] != expected[IX][IY] ||
      r[IY][IX] != expected[IY][IX] ||
      r[IY][IY] != expected[IY][IY]) {
    return -2;
  }

  return 0;
}
