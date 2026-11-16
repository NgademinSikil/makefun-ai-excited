[![make.fun](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/{owner}/{repo}/rank.svg)](https://make.fun/bounty/ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/{owner}/{repo}/reward.svg)](https://make.fun/bounty/ai-excited-01)

# WOW! Koi — make.fun ai-excited-01

One image made to excite the AI judge: a giant luminous koi leaps out of a
neon ocean toward a blazing synthwave sun, bursting through the frame toward
the viewer, under a starry indigo sky — with a big, clean **WOW!** for the
judge. One clear focal point, a strong diagonal, and colours that hit at a
glance, even at 300 px wide.

## How it works

`main.ts` (Node 22, standard library only) copies the original artwork in
`entry.png` to `/output/entry.png`. The image itself was drawn procedurally
by `generate_entry.py` (Pillow + numpy, fixed seed, no network) — a
deterministic generator, so the artwork is reproducible from source.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

Two runs write byte-identical output. The image is a 1024×1024 PNG under
1 MiB, and the program makes no network calls.

## Recorded rebuild

Rebuilt on 2026-11-16 in a recorded session (strict transcripts): `main.ts`
and `generate_entry.py` were rewritten with new code structure, and
`entry.png` was regenerated — verified byte-identical to the original
artwork (same SHA-256), so the submitted image is unchanged.

## License

MIT — see [LICENSE](LICENSE).

<!-- TODO before submitting: replace {owner} and {repo} in the badge URLs
     above with the real GitHub owner/repo, and set the repo's GitHub About
     (website: https://make.fun, topic: makefun) as the kit's RULES.txt
     requires. -->
