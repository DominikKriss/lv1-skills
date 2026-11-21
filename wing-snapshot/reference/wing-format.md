# WING snapshot: what the builder relies on

The format reference is show-file-skills `behringer/wing/references/FORMAT.md`; this page lists only what the
builder uses and how sure each item is.

## Seen in a WING-Edit 3.2.1 INIT save

- `type` `snapshot.10`, one-line JSON, no `busmode` / send `ind` keys: a bus's mode is the `mode` of the sends
  into it (`PRE`, `POST`, `GRP`).
- Strips: `ch` 1-40 (with `flt`, `proc`, `gate`, `gatesc`), `aux` 1-8 (no input filter, no gate), `bus` 1-16,
  `main` 1-4 (`send.MX1`-`MX8`), `mtx` 1-8, `dca` 1-16, `fx` 1-16 (`{"mdl": "NONE", "fxmix": 100}` when empty).
- Sockets `io.in.<grp>.<n>` with `mode` `M` / `ST`; outputs `io.out.<grp>.<n>` `{grp, in}`.
- Every `clink` on: a linked strip shows its socket's name, so the builder turns `clink` off and names both.

## Unconfirmed (check in WING-Edit)

- A stereo source written as `ST` on both sockets of the odd/even pair.
- A mono bus as output source `BUS 2n-1`.
- FX slot or bus dynamics holding only the model: whether WING-Edit loads the model's defaults.
- Gate `ratio` `GATE` (stock gate rather than expander); key filter types `HP12` / `LP12`; EQ low band `CUT` as a
  low cut on aux inputs.
- DCA assignment through strip `tags` `#Dn`.
