# Sources and design changes

| Source | Baseline / use | Attribution and license |
| --- | --- | --- |
| [Charybdis](https://github.com/Bastardkb/Charybdis/tree/47af70b9cd9b8d1d3a055ea88ab95c724bd3c02a) | Commit `47af70b9cd9b8d1d3a055ea88ab95c724bd3c02a`; Nano `charybdisnano_v2_v187.stl`; specified top adapter, BTU bottom and sensor cover; MK2 appearance reference | BastardKB and original contributors, CC BY-NC-SA 4.0 |
| [Skeletyl V4](https://github.com/Bastardkb/Skeletyl/tree/main/V4) | `case_v4_103.stl`, mirrored for the left half; `case_v4_v99.step` retained as a modeling reference | BastardKB and original contributors, CC BY-NC-SA 4.0 |
| [Elite-C-holder](https://github.com/Bastardkb/Elite-C-holder/tree/8b7cdf78d13d242d84367ef6aa4020f80e6c0c11) | PCB reference commit `8b7cdf78d13d242d84367ef6aa4020f80e6c0c11`; enclosure mounting datums follow the original case, as used in the existing build | BastardKB and original contributors, CC BY-NC-SA 4.0 |
| [Amoeba Royale](https://github.com/mtl/keyboard-pcbs/tree/master/amoeba-royale) | Selected single-switch PCB; dimensional reference | mtl and contributors, CC0 1.0; [retained license](../development/references/amoeba-LICENSE.txt) |
| [ZMK](https://github.com/zmkfirmware/zmk) | Intended firmware; configuration not included in this snapshot | ZMK contributors; refer to upstream license |

Reference-file SHA-256 values are in [provenance.json](../development/references/provenance.json).
That record also includes upstream source files kept only in the local workspace.

The Skeletyl STEP and STL have different version numbers. The geometry preservation
claim is specifically against the retained **103 STL**, not an assertion that
every Skeletyl revision is identical.

Gyre Nano changes the open frame into a closed enclosure, blends the thumb and
trackball transitions, adds holder support and USB access, and uses matching
bottom trays with screw mounts close to the walls. Functional key lands and the
original trackball seat remain at the original datums. These are modifications,
not official BastardKB releases or endorsements.
