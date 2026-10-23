# CAD: feeder bracket (stand-in for the IDRP part; confirm with the coach)
Built in Fusion from the prompts in `../docs/CAD_PROMPTS.md`. Files: `feeder_bracket_model1_good.*` (Model 1, good) and `feeder_bracket_model2_defective.*` (Model 2, defective variant): STEP (exported from Fusion), STL (generated from the STEP with cadquery, for printing), top and isometric PNG renders (generated from the STEP mesh; the shading triangles are a rendering artefact, not geometry).
The Fusion F3D files are not in this folder yet: add your own exports here.

## Checked from the STEP files (cadquery, mm)
| Check | Model 1 (good) | Model 2 (defective) | Design value |
|---|---|---|---|
| Solids / valid | 1 / yes | 1 / yes | 1 solid |
| Bounding box | 60 x 40 x 40 | 60 x 40 x 40 | 60 x 40 x 40 |
| Volume | 23,035 mm3 | 23,858 mm3 | about 23,000 / 23,900 (hand calculation) |
| Faces | 27 | 22 | Model 2 has 5 fewer: 4 for the slot, 1 for the hole |
| 6 mm base holes (r=3) | 4 | 3 | 4 / 3 |
| Slot (two r=3 end faces) | yes | no | yes / no |
| 5 mm wall holes (r=2.5) | 2 | 2 | 2 / 2 |
| R4 inner fillet | yes (3 segments split by the gussets) | same | yes |

Model 2 differs from Model 1 in exactly two ways: the central slot is filled and the mounting hole at (X,Y) = (52,8) is filled. Volume difference 823 mm3 matches the two filled features. Both are clearly different in a top-down view (`*_top.png`).

Not checked: print quality (slice it first), real-world dimensions after printing.
