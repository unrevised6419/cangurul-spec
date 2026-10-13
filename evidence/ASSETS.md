# Image and sound assets

All assets were extracted from the binary with `../tools/extract_images.py <exe> <outdir>`. The originals (`.bmp`, `.ico`, `.wav`) are kept unchanged, and every image also has a `.png` copy made with macOS `sips`.

Naming:
- `<name>`: an `RT_BITMAP` resource with that name.
- `icon_1`: the main icon (32 × 32, 16 colours).
- `<form>_<component>_<property>`: a bitmap stored inside a Delphi form (DFM). `glyph` is a button image; `picture` is a `TImage`.
- `_imagelist0` / `_imagelist1`: an image-list strip and its mask.

Transparency: the original Delphi controls make one colour transparent, normally the colour of the bottom-left pixel. The PNGs are not made transparent.

## Files (`images/`, `sounds/`)

| File | Size | Use |
|---|---|---|
| `img0` … `img3` | sprite | kangaroo facing East / North (back view) / West / South (by heading; see spec §5.1) |
| `trup0`, `trup1` | sprite | "fall" sprites shown on the edge refusal (`Whoooooooooops!!!`) |
| `tmainform_Image2_picture` | 40 × 40 | the kangaroo on the main form |
| `tmainform_{NormalButtons,EnabledButtons,MenuImageList}_imagelist0` / `…1` | 64 × 32 strip / mask | toolbar and menu icons (16 × 16 cells) |
| `tconfigform_Numbers_imagelist0` / `…1` | 56 × 75 | digit images for the speed dialog |
| `tconfigform_Image1..3_picture` | 22 × 12, 240 × 15 | speed-dialog decorations (slider scale) |
| `tinitform_Image1_picture` | 375 × 105 | splash screen |
| `taboutbox_Image1_picture`, `taboutbox_Image6_picture` | 150 × 179, 284 × 80 | About-box pictures |
| `thelpform_Image1,3,4,5,6_picture` | 150 × 179, 172 × 81 ×3, 284 × 80 | help-window pictures; the 172 × 81 ones are probably PAS/SALT/ROTIRE illustrations |
| `twaveform_Bt{Play,Clear,Load}_glyph` | 32 × 16 | buttons of a sound-test form |
| `cdrom`, `floppy`, `hard`, `network`, `ram`, `closedfolder`, `openfolder`, `currentfolder`, `executable`, `knownfile`, `unknownfile`, `tinitool` | small | stock icons of a third-party file-dialog component; not specific to the app |
| `icon_1` | 32 × 32 | application icon |
| `sounds/sound_0` … `sound_6.wav` | mono 22,050 Hz 16-bit, 0.3–4.0 s | the 7 sounds of which one is played at random on the edge refusal (spec §5.2) |
