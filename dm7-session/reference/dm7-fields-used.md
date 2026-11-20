# DM7 fields the builder writes

Paths under `Current/CurrentBackupFile.bup` (and its `.old` copy) section `Mixing` unless noted. Meanings from
show-file-skills `yamaha/references/dm7-fields.md`.

| What | Path |
|---|---|
| Name, colour | `InputChannel[ch]/Label.Name`, `.Color` (8 characters shown) |
| Patch | `InputChannel/InPatch/Bank[0].Source`: Dante IN n = 0x01A00000 + n-1; FX return = 0x06C00000 + slot x 16 + side |
| Pair | `GainGang`, `DelayGang` 1; `Signal.Relation` 128 / 1; `StereoInputType` `STEREO`; `ToStereo.PanType` `BALANCE` |
| HPF / LPF | `HPF[0]` / `LPF[0]` `On`, `Frequency` (0.1 Hz), `Slope` |
| EQ | `PEQ/Bank[0]/Band[k]` `Frequency` 0.1 Hz, `Gain` 0.01 dB, `Q` x1000; `LowShelving` / `HighShelving` `On`, `Q` |
| Dynamics | `Dynamics[0]` DYN1, `[1]` DYN2 `Bank[0]` `Type`, `On`, `MixBalance`, `Parameter[j].Value`; `KeyIn[0]` |
| Sends | `InputChannel/ToMix[m]` `Pre` 1 + `PrePoint` 100 (Pre Fader) for monitor mixes; `On` 0 from FX returns |
| Mixes | `Mix[k]/Label.Name`, `BusType` `VARI`, `ToStereo.ToStereoA` 0 |
| Matrices | `Matrix[t]/Label.Name`; pairs `Signal.Relation` 128 / 1, `DelayGang` 1; feed `Stereo[0..1]/ToMatrix[t]` `On`, `Level` |
| FX rack input | `EffectRack/Slot[f]/InputPort[0..1]/Patch.Source` = mix code 0x03E00000 + m-1 |
| Dante OUT | `Process` section `Dante/OutputPort[k]/Patch.Source`: mix 0x03E00000 + n-1, matrix 0x04000000 + n-1 |
| Dante IN subscription | `Setup/SetupBackupFile.bup` `Setup` section `DanteNetwork/InputPort[n]/Patch.Source` = 0x44000000, unit << 12, port - 1; unit = mounted `DanteRemoteControl/IOUnit` index + 1 (seen in a DM Editor session with two Rio3224-D3: unit 1 = 0x44001000) |

Gate words: threshold 0.01 dB, attack ms, range 0.01 dB (negative), hold us, decay us. Legacy Comp words:
threshold 0.01 dB, attack ms, release us, ratio x10 (255 = inf), knee 0-5, out gain 0.01 dB.
