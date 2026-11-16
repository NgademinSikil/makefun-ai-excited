// ai-excited-01 entry: "WOW! Koi"
//
// A luminous koi leaping out of a neon ocean toward a blazing synthwave
// sun — drawn to excite the AI judge. The artwork lives in entry.png
// next to this file (painted procedurally by generate_entry.py); this
// program's only job is to place those exact bytes at /output/entry.png.
//
// Deterministic by construction: the same input bytes always produce the
// same output bytes. Node standard library only — no network, no clock,
// no randomness, no environment dependence beyond the output directory.
//
// Local equivalent of the grader's run:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const MAX_IMAGE_BYTES = 1048576; // the bounty cap: 1 MiB

function entryPath(): string {
  return join(dirname(fileURLToPath(import.meta.url)), 'entry.png');
}

function outputPath(): string {
  const dir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
  return join(dir, 'entry.png');
}

function loadArtwork(path: string): Buffer {
  if (!existsSync(path)) {
    throw new Error(`entry image missing: ${path}`);
  }
  const data = readFileSync(path);
  if (data.length === 0) {
    throw new Error('entry image is empty');
  }
  if (data.length > MAX_IMAGE_BYTES) {
    throw new Error(`entry image exceeds 1 MiB: ${data.length} bytes`);
  }
  return data;
}

function assertPng(data: Buffer): void {
  const header = data.subarray(0, PNG_SIGNATURE.length);
  if (!header.equals(PNG_SIGNATURE)) {
    throw new Error('entry.png is not a PNG file (bad magic bytes)');
  }
}

function publish(data: Buffer, destination: string): void {
  mkdirSync(dirname(destination), { recursive: true });
  writeFileSync(destination, data);
  const roundTrip = readFileSync(destination);
  if (!roundTrip.equals(data)) {
    throw new Error('verification failed: written bytes differ from source');
  }
}

function main(): void {
  const artwork = loadArtwork(entryPath());
  assertPng(artwork);
  const destination = outputPath();
  publish(artwork, destination);
  console.log(`wrote ${destination} (${artwork.length} bytes)`);
}

main();
