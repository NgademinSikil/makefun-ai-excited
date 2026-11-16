// ai-excited-01 entry: "WOW! Koi" — a luminous koi leaping out of a neon
// ocean toward a blazing synthwave sun, drawn to excite the AI judge.
//
// The image is the original generative artwork in entry.png beside this
// file (drawn procedurally by generate_entry.py in this repository).
// This program only copies those exact bytes to the output directory,
// so both runs write byte-identical output. Node standard library only,
// no network, no randomness, no environment dependence.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, 'entry.png');
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const target = join(outDir, 'entry.png');

if (!existsSync(source)) {
  throw new Error(`entry image missing: ${source}`);
}

const bytes = readFileSync(source);
if (bytes.length === 0 || bytes.length > 1048576) {
  throw new Error(`entry image has unexpected size: ${bytes.length} bytes`);
}
// PNG magic: 89 50 4E 47 0D 0A 1A 0A
const magic = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
if (!magic.every((b, i) => bytes[i] === b)) {
  throw new Error('entry.png is not a PNG file');
}

mkdirSync(outDir, { recursive: true });
writeFileSync(target, bytes);

const written = readFileSync(target);
if (!written.equals(bytes)) {
  throw new Error('verification failed: written bytes differ from source');
}
console.log(`wrote ${target} (${bytes.length} bytes)`);
