# Cangurul (the Kangaroo): reverse-engineered language specification

Cangurul is a Moldovan/Romanian school program from around 2000. Students write programs that move a kangaroo along the lines of a squared field, drawing figures with its steps.

| File | Content |
|---|---|
| [`cangurul-language-spec.md`](cangurul-language-spec.md) | the full language and runtime specification |
| `binary/Cangourou.exe` | the original program (SHA-256 `abaffe68f083140e3dc691029d12884f7a396504655d8ef5e0deaaae6b8147e9`) |
| `tools/DumpApp.java` | Ghidra headless script: creates functions at given addresses (needed for Delphi event handlers) and decompiles an address range |
| `tools/helpers/` | Python helpers: PE offsets, Delphi strings, DFM form parsing. Set `EXE=../../binary/Cangourou.exe` before running them |
| `tools/extract_images.py` | extracts every image and sound from the binary: `python3 tools/extract_images.py binary/Cangourou.exe <outdir>` |
| `evidence/` | parsed form resources (`dfm_*.txt`) |
| `evidence/images/`, `evidence/sounds/` | all assets, as originals plus PNG copies, indexed in [`evidence/ASSETS.md`](evidence/ASSETS.md) |

The specification was derived from the binary only. A school textbook (Grade 8 Informatics, 2020) was used only for hypotheses, and the spec lists where the textbook is wrong. Every claim is tagged **Observed**, **Inferred**, **Unknown** or **Proposal**, and cites the code address it comes from.

The program does not contain its keywords: it loaded them from localisation files that were not distributed. So the spec defines the language through **keyword roles**, gives the reconstructed Romanian keywords, and proposes English and Russian sets.

## Using this spec

1. Revalidate the spec against `binary/Cangourou.exe`; the spec ends with a "How to revalidate" section listing every relevant code address.
2. Implement a grammar and an interpreter. The spec separates the original (faithful) behaviour from recommended corrections, and ends with test cases for both.
