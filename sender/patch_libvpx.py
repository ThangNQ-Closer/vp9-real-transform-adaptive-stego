#!/usr/bin/env python3
import os
import shutil
import sys

PATCH_MARK = "VP9_REAL_TRANSFORM_ADAPTIVE_STEGO_PATCH"

C_HELPER = r"""
/* VP9_REAL_TRANSFORM_ADAPTIVE_STEGO_PATCH: teaching-only transform-domain hook. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct Vp9StegoSample {
  int coeff_index;
  int coeff_value;
  int abs_value;
  int eligible;
} Vp9StegoSample;

typedef struct Vp9StegoEntry {
  long sequence_id;
  int frame;
  int block;
  int plane;
  int coeff_index;
  int old_coeff;
  int new_coeff;
  int embedded_bit;
} Vp9StegoEntry;

static int vp9_stego_inited = 0;
static int vp9_stego_mode = 0;  /* 0 off, 1 log, 2 embed */
static int vp9_stego_threshold = 3;
static int vp9_stego_payload_bits[32768];
static int vp9_stego_payload_bit_count = 0;
static int vp9_stego_payload_bit_pos = 0;
static char vp9_stego_payload_text[4096];
static char vp9_stego_log_path[512];
static char vp9_stego_coeff_log_path[512];
static long vp9_stego_sequence = 0;

static long vp9_stego_total_coeff_seen = 0;
static long vp9_stego_nonzero_coeff_seen = 0;
static long vp9_stego_eligible_coeff_seen = 0;
static Vp9StegoSample vp9_stego_samples[256];
static int vp9_stego_sample_count = 0;

static int vp9_stego_embedded_bits = 0;
static int vp9_stego_modified_coeffs = 0;
static int vp9_stego_skipped_zero = 0;
static int vp9_stego_skipped_dc = 0;
static int vp9_stego_skipped_small = 0;
static int vp9_stego_skipped_parity_already_match = 0;
static int vp9_stego_zero_to_nonzero = 0;
static int vp9_stego_nonzero_to_zero = 0;
static int vp9_stego_dc_modified = 0;
static Vp9StegoEntry vp9_stego_entries[8192];
static int vp9_stego_entry_count = 0;

static int vp9_stego_abs_int(int v) { return v < 0 ? -v : v; }
static int vp9_stego_sign_int(int v) { return v < 0 ? -1 : 1; }

static void vp9_stego_add_byte_bits(unsigned int b) {
  int i;
  for (i = 7; i >= 0; --i) {
    if (vp9_stego_payload_bit_count < (int)(sizeof(vp9_stego_payload_bits) / sizeof(vp9_stego_payload_bits[0]))) {
      vp9_stego_payload_bits[vp9_stego_payload_bit_count++] = (b >> i) & 1;
    }
  }
}

static void vp9_stego_load_payload(void) {
  const char *path = getenv("VP9_STEGO_MESSAGE");
  FILE *f = NULL;
  size_t n = 0;
  size_t i;
  if (path && path[0]) f = fopen(path, "rb");
  if (f) {
    n = fread(vp9_stego_payload_text, 1, sizeof(vp9_stego_payload_text) - 1, f);
    fclose(f);
    while (n > 0 && (vp9_stego_payload_text[n - 1] == '\n' || vp9_stego_payload_text[n - 1] == '\r')) n--;
    vp9_stego_payload_text[n] = '\0';
  } else {
    strcpy(vp9_stego_payload_text, "KHOA ATTT PTIT");
    n = strlen(vp9_stego_payload_text);
  }
  for (i = 0; i < 4; ++i) {
    unsigned int b = (unsigned int)((n >> (8 * (3 - i))) & 0xff);
    vp9_stego_add_byte_bits(b);
  }
  for (i = 0; i < n; ++i) vp9_stego_add_byte_bits((unsigned char)vp9_stego_payload_text[i]);
}

static void vp9_stego_write_json_string(FILE *f, const char *s) {
  const unsigned char *p = (const unsigned char *)s;
  fputc('"', f);
  while (*p) {
    if (*p == '"' || *p == '\\') {
      fputc('\\', f);
      fputc(*p, f);
    } else if (*p >= 32 && *p < 127) {
      fputc(*p, f);
    }
    p++;
  }
  fputc('"', f);
}

static void vp9_stego_finish(void) {
  int i;
  FILE *f;
  if (!vp9_stego_inited) return;
  if (vp9_stego_mode == 1) {
    f = fopen(vp9_stego_coeff_log_path, "wb");
    if (!f) return;
    fprintf(f, "{\n");
    fprintf(f, "  \"total_coeff_seen\": %ld,\n", vp9_stego_total_coeff_seen);
    fprintf(f, "  \"nonzero_coeff_seen\": %ld,\n", vp9_stego_nonzero_coeff_seen);
    fprintf(f, "  \"eligible_coeff_seen\": %ld,\n", vp9_stego_eligible_coeff_seen);
    fprintf(f, "  \"sample_entries\": [\n");
    for (i = 0; i < vp9_stego_sample_count; ++i) {
      fprintf(f, "    {\"coeff_index\": %d, \"coeff_value\": %d, \"abs_value\": %d, \"eligible\": %s}%s\n",
              vp9_stego_samples[i].coeff_index,
              vp9_stego_samples[i].coeff_value,
              vp9_stego_samples[i].abs_value,
              vp9_stego_samples[i].eligible ? "true" : "false",
              (i + 1 == vp9_stego_sample_count) ? "" : ",");
    }
    fprintf(f, "  ]\n}\n");
    fclose(f);
  } else if (vp9_stego_mode == 2) {
    f = fopen(vp9_stego_log_path, "wb");
    if (!f) return;
    fprintf(f, "{\n  \"payload\": ");
    vp9_stego_write_json_string(f, vp9_stego_payload_text);
    fprintf(f, ",\n");
    fprintf(f, "  \"payload_bits\": %d,\n", vp9_stego_payload_bit_count);
    fprintf(f, "  \"embedded_bits\": %d,\n", vp9_stego_embedded_bits);
    fprintf(f, "  \"modified_coeffs\": %d,\n", vp9_stego_modified_coeffs);
    fprintf(f, "  \"skipped_zero\": %d,\n", vp9_stego_skipped_zero);
    fprintf(f, "  \"skipped_dc\": %d,\n", vp9_stego_skipped_dc);
    fprintf(f, "  \"skipped_small\": %d,\n", vp9_stego_skipped_small);
    fprintf(f, "  \"skipped_parity_already_match\": %d,\n", vp9_stego_skipped_parity_already_match);
    fprintf(f, "  \"zero_to_nonzero\": %d,\n", vp9_stego_zero_to_nonzero);
    fprintf(f, "  \"nonzero_to_zero\": %d,\n", vp9_stego_nonzero_to_zero);
    fprintf(f, "  \"dc_modified\": %d,\n", vp9_stego_dc_modified);
    fprintf(f, "  \"entries\": [\n");
    for (i = 0; i < vp9_stego_entry_count; ++i) {
      Vp9StegoEntry *e = &vp9_stego_entries[i];
      fprintf(f, "    {\"sequence_id\": %ld, \"frame\": %d, \"block\": %d, \"plane\": %d, \"coeff_index\": %d, \"old_coeff\": %d, \"new_coeff\": %d, \"embedded_bit\": %d}%s\n",
              e->sequence_id, e->frame, e->block, e->plane, e->coeff_index,
              e->old_coeff, e->new_coeff, e->embedded_bit,
              (i + 1 == vp9_stego_entry_count) ? "" : ",");
    }
    fprintf(f, "  ]\n}\n");
    fclose(f);
  }
}

static void vp9_stego_init_once(void) {
  const char *mode;
  const char *v;
  if (vp9_stego_inited) return;
  vp9_stego_inited = 1;
  mode = getenv("VP9_STEGO_MODE");
  if (mode && strcmp(mode, "log") == 0) vp9_stego_mode = 1;
  else if (mode && strcmp(mode, "embed") == 0) vp9_stego_mode = 2;
  else vp9_stego_mode = 0;
  v = getenv("VP9_STEGO_THRESHOLD");
  if (v && atoi(v) > 0) vp9_stego_threshold = atoi(v);
  v = getenv("VP9_STEGO_LOG");
  strncpy(vp9_stego_log_path, (v && v[0]) ? v : "embed_log.json", sizeof(vp9_stego_log_path) - 1);
  v = getenv("VP9_STEGO_COEFF_LOG");
  strncpy(vp9_stego_coeff_log_path, (v && v[0]) ? v : "coeff_log.json", sizeof(vp9_stego_coeff_log_path) - 1);
  if (vp9_stego_mode == 2) vp9_stego_load_payload();
  atexit(vp9_stego_finish);
}

static int vp9_stego_mid_index(int coeff_index) {
  return coeff_index >= 3 && coeff_index <= 9;
}

static void vp9_stego_process_qcoeff(tran_low_t *qcoeff, int eob, int plane, int block) {
  int i;
  static const int mid_coeffs[7] = {3, 4, 5, 6, 7, 8, 9};
  vp9_stego_init_once();
  if (vp9_stego_mode == 0 || !qcoeff || eob <= 0) return;
  if (vp9_stego_mode == 1) {
    for (i = 0; i < eob; ++i) {
      int v = (int)qcoeff[i];
      int av = vp9_stego_abs_int(v);
      int eligible = (i != 0 && vp9_stego_mid_index(i) && v != 0 && av >= vp9_stego_threshold);
      vp9_stego_total_coeff_seen++;
      if (v != 0) vp9_stego_nonzero_coeff_seen++;
      if (eligible) vp9_stego_eligible_coeff_seen++;
      if (vp9_stego_sample_count < (int)(sizeof(vp9_stego_samples) / sizeof(vp9_stego_samples[0]))) {
        vp9_stego_samples[vp9_stego_sample_count].coeff_index = i;
        vp9_stego_samples[vp9_stego_sample_count].coeff_value = v;
        vp9_stego_samples[vp9_stego_sample_count].abs_value = av;
        vp9_stego_samples[vp9_stego_sample_count].eligible = eligible;
        vp9_stego_sample_count++;
      }
    }
    return;
  }
  vp9_stego_skipped_dc++;
  for (i = 0; i < 7 && vp9_stego_payload_bit_pos < vp9_stego_payload_bit_count; ++i) {
    int ci = mid_coeffs[i];
    int oldv;
    int av;
    int bit;
    int newv;
    if (ci >= eob) {
      vp9_stego_skipped_zero++;
      continue;
    }
    oldv = (int)qcoeff[ci];
    if (oldv == 0) {
      vp9_stego_skipped_zero++;
      continue;
    }
    av = vp9_stego_abs_int(oldv);
    if (av < vp9_stego_threshold) {
      vp9_stego_skipped_small++;
      continue;
    }
    bit = vp9_stego_payload_bits[vp9_stego_payload_bit_pos];
    if ((av % 2) == bit) {
      vp9_stego_skipped_parity_already_match++;
      vp9_stego_embedded_bits++;
      vp9_stego_payload_bit_pos++;
      continue;
    }
    newv = oldv - vp9_stego_sign_int(oldv);
    if (newv == 0) {
      vp9_stego_nonzero_to_zero++;
      continue;
    }
    if (oldv == 0 && newv != 0) vp9_stego_zero_to_nonzero++;
    qcoeff[ci] = (tran_low_t)newv;
    if (ci == 0) vp9_stego_dc_modified++;
    vp9_stego_modified_coeffs++;
    vp9_stego_embedded_bits++;
    if (vp9_stego_entry_count < (int)(sizeof(vp9_stego_entries) / sizeof(vp9_stego_entries[0]))) {
      Vp9StegoEntry *e = &vp9_stego_entries[vp9_stego_entry_count++];
      e->sequence_id = vp9_stego_sequence++;
      e->frame = -1;
      e->block = block;
      e->plane = plane;
      e->coeff_index = ci;
      e->old_coeff = oldv;
      e->new_coeff = newv;
      e->embedded_bit = bit;
    }
    vp9_stego_payload_bit_pos++;
  }
}
"""

def patch_tokenize(path):
    with open(path, "r") as f:
        data = f.read()
    if PATCH_MARK in data:
        print("patch already present in " + path)
        return False
    marker = '#include "vp9/encoder/vp9_tokenize.h"\n'
    if marker not in data:
        raise SystemExit("include marker not found in " + path)
    data = data.replace(marker, marker + "\n" + C_HELPER + "\n", 1)
    target = "  const tran_low_t *qcoeff = BLOCK_OFFSET(p->qcoeff, block);\n"
    if target not in data:
        raise SystemExit("qcoeff marker not found in " + path)
    inject = target + "  vp9_stego_process_qcoeff((tran_low_t *)qcoeff, eob, plane, block);\n"
    data = data.replace(target, inject, 1)
    shutil.copy2(path, path + ".pre-vp9-stego")
    with open(path, "w") as f:
        f.write(data)
    print("patched " + path)
    return True

def main():
    root = os.path.abspath("libvpx")
    if len(sys.argv) > 1:
        root = os.path.abspath(sys.argv[1])
    tok = os.path.join(root, "vp9", "encoder", "vp9_tokenize.c")
    if not os.path.exists(tok):
        raise SystemExit("cannot find " + tok + "; run build_libvpx.sh or place libvpx source first")
    patch_tokenize(tok)
    print("Patch strategy: vp9/encoder/vp9_tokenize.c after transform+quantization, before token emission.")
    print("Modes: VP9_STEGO_MODE=off|log|embed; logs use coeff_log.json/embed_log.json.")

if __name__ == "__main__":
    main()
