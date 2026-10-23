# CAD prompts (Fusion): feeder bracket, Model 1 (good) and Model 2 (defective variant)
Stand-in part designed for this project: confirm with your coach that it meets the "IDRP CAD file" requirement; if the course supplies an official file, adapt these steps to it.
Coordinates: X width, Y depth, Z height, millimetres.

## Prompt 1: Model 1
```
In Fusion, create a new design in millimetres and build a single solid body named "Feeder_Bracket_M1". Use this coordinate system: X = width, Y = depth, Z = height. Create these as user parameters so they are editable: base_w=60, base_d=40, base_t=5, wall_h=40, wall_t=5.

1. BASE PLATE: rectangle 60 x 40 on the XY plane, corner at the origin (X 0..60, Y 0..40), extrude 5 up (Z 0..5).
2. VERTICAL PLATE: on the back edge, a block X 0..60, Y 35..40, Z 0..40 (5 thick, 40 tall), joined to the base.
3. INNER FILLET: 4 mm radius fillet along the inside corner where the base top face meets the front face of the vertical plate (the edge at Y=35, Z=5, running along X).
4. BASE MOUNTING HOLES: four 6 mm diameter through holes in the base at (X,Y) = (8,8), (52,8), (8,27), (52,27).
5. CENTRAL SLOT: one 24 mm x 6 mm slot with fully rounded ends, cut through the base, long axis along X, centred at (X,Y) = (30,12), so it spans X 18..42, Y 9..15.
6. WALL HOLES: two 5 mm diameter through holes in the vertical plate, drilled along Y, at (X,Z) = (15,25) and (45,25).
7. GUSSETS: two right-triangle ribs, each 4 mm thick, at X 22..26 and X 34..38. Each triangle has vertices (Y,Z) = (17,5), (35,5) and (35,30): it sits on the base top face and against the front face of the vertical plate. Join them to the body.

Keep it one solid body. Do not add any other features. After building, report: volume (mm^3), bounding box, number of faces, and number of through holes. Expected volume is about 23,000 mm^3 (within a few hundred).
Then save the design as "feeder_bracket_model1" and export F3D, STEP and STL (binary, high resolution) to <your folder>, all named feeder_bracket_model1.*
```

## Prompt 2: Model 2 (defective variant)
```
Open feeder_bracket_model1 and use "Save As" to create a new document named "feeder_bracket_model2". Do NOT change the Model 1 file. Rename the body to "Feeder_Bracket_M2" and make exactly these two changes, nothing else:
1. Remove the central slot: fill it so the base plate is solid there (the base top and bottom faces should be flat across X 18..42, Y 9..15).
2. Remove the mounting hole at (X,Y) = (52,8): fill it solid, flush with the base faces.
Keep all other dimensions, holes and gussets identical to Model 1.
Report: volume (mm^3), bounding box, number of faces, number of through holes. Expected volume is about 23,900 mm^3 (Model 1 plus about 820 mm^3), with 3 base holes instead of 4 and no slot.
Export F3D, STEP and STL to the same folder as feeder_bracket_model2.*
```

## Prompt 3: images
```
For each of the two designs, hide construction geometry, set a plain white background, and export PNG images (at least 2000 px wide): (a) a top view, orthographic, looking straight down at the base plate, (b) an isometric view. Name them feeder_bracket_model1_top.png, feeder_bracket_model1_iso.png and the same for model2, into the same folder.
```

Printing: PLA, 0.2 mm layers, 20% infill, base plate down, no supports. The expected volumes are hand calculations: a few hundred mm^3 of difference is fine.
