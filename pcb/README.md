# GyreNano electronics

[简体中文](README.zh-CN.md)

Current engineering samples, grouped by function. Hardware revisions remain in the filenames so received boards can be traced to their exact artwork. Physical assembly, thin-FR4 forming and FPC durability are still awaiting trials.

| Part | Current editable design | Manufacturing / assembly status |
| --- | --- | --- |
| [FR4 keyfield](keyfield-fr4/README.md) | V33 KiCad + native JLCEDA | 99.70 × 99.80 mm, **0.6 mm**, functional cuttable bridges; user reports KiCad upload |
| [Isolated FR4 alternative](keyfield-fr4/alternative-isolated/README.md) | V32 KiCad | Same size; seven electrically independent regions; retained alternative |
| [FPC keyfield](keyfield-fpc/README.md) | V27 KiCad | 97.18 × 96.47 mm, 0.11 mm; user reports sample submission |
| [Left/right holders](holders/README.md) | V22 native JLCEDA | Seven FFC sockets per side; user reports boards already ordered |
| [PMW3610 sensor](sensor/README.md) | V22 native JLCEDA | FFC interface; use with the original optical stack |

[BOM / 采购清单](keyfield-fpc/BOM.zh-CN.md) · [CSV](keyfield-fpc/BOM.csv) · [Print files](../models/README.md)

Holder/sensor `reference-kicad/` directories retain the older artwork for traceability. Their missing PTH mask openings were corrected in the EDA designs; **do not substitute the old KiCad exports for the EDA projects**. See [EDA verification](eda-validation/README.md).

All order ZIPs are engineering samples, not a qualified production release. Coupon eligibility and vendor classification are not established by this repository. Source board thicknesses have not been changed to 0.4 or 0.8 mm.

The old numbered experiment directories are removed from the working tree. Cross-version generation scripts, inputs and historical evidence are preserved in the [engineering snapshot](https://github.com/GavynDracula/GyreNano/releases/tag/v0.2.0-prototype.1); see [development notes](../docs/DEVELOPMENT.md).
