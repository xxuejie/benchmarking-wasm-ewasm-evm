#include "blake2b.h"

int char_to_int(char ch)
{
  if (ch >= '0' && ch <= '9') {
    return ch - '0';
  }
  if (ch >= 'a' && ch <= 'f') {
    return ch - 'a' + 10;
  }
  return -1;
}

int hex_to_bin(char* buf, size_t buf_len, const char* hex)
{
  int i = 0;

  for (; i < buf_len && hex[i * 2] != '\0' && hex[i * 2 + 1] != '\0'; i++) {
    int a = char_to_int(hex[i * 2]);
    int b = char_to_int(hex[i * 2 + 1]);

    if (a < 0 || b < 0) {
      return -1;
    }

    buf[i] = ((a & 0xF) << 4) | (b & 0xF);
  }

  if (i == buf_len && hex[i * 2] != '\0') {
    return -1;
  }
  return i;
}

#define CHECK_LEN(x) if ((x) <= 0) { return x; }

int main(int argc, char* argv[]) {
  if (argc != 3) {
    return -1;
  }

  char buffer1[10000];
  char buffer2[64];

  int len1 = hex_to_bin(buffer1, 10000, argv[1]);
  CHECK_LEN(len1);
  int len2 = hex_to_bin(buffer2, 64, argv[2]);
  if (len2 != 64) {
    return -2;
  }

  unsigned char hash[64];
  blake2b_state blake2b_ctx;
  blake2b_init(&blake2b_ctx, 64);
  blake2b_update(&blake2b_ctx, buffer1, len1);
  blake2b_final(&blake2b_ctx, hash, 64);

  /* for (int i = 0; i < 64; i++) { */
  /*   printf("%02x ", hash[i]); */
  /* } */
  /* printf("\n"); */

  if (memcmp(buffer2, hash, 64) != 0) {
    return -3;
  }

  return 0;
}
