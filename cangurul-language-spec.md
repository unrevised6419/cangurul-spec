# Cangurul (the Kangaroo executor): language and runtime specification

Version 1.0 · 2026-10-13 · reverse-engineered from the original Windows program

This document describes the programming language of **Cangurul** (file name `Cangourou.exe`, version string `Cangourou 2.20.00`). It was written so that the language can be reimplemented, for example as a web app, and so that every claim can be checked again against the original binary.

School textbooks describe this language together with other teaching executors and simplify it; where the textbook and this program disagree, this document follows the program.

---

## 0. How to read this document

### 0.1 Source of truth

| Artifact | Identity |
|---|---|
| `Cangourou.exe` | 1,554,432 bytes, SHA-256 `abaffe68f083140e3dc691029d12884f7a396504655d8ef5e0deaaae6b8147e9`, file date 2000-02-17 |
| Format | PE32, Intel 80386, Windows GUI, Borland Delphi (VCL), image base `0x400000`, `CODE` 0x401000–0x4649d0 |

Everything here comes from that binary: Ghidra 12.1.4 decompilation, raw disassembly, the Delphi form resources (DFM, binary `TPF0`) and the RTTI method tables. The whole interpreter is in the main unit (0x45d000–0x4649d0). It consists of a line-based syntax checker (0x45e8b8) and a recursive executor (0x45f150). The program was never executed, so all runtime behaviour is derived from static analysis.

A secondary source, used only to form hypotheses, is the Moldovan Grade 8 Informatics textbook (2020, Romanian edition), chapter 2. Section 13 lists where it differs.

### 0.2 Evidence tags

- **[O] Observed**: read directly from code or data at the cited address.
- **[I] Inferred**: a strong deduction from code; the exact value is not in the binary.
- **[U] Unknown**: cannot be determined from the binary.
- **[P] Proposal**: a design choice for a reimplementation, not a property of the original.

Addresses are code VAs unless marked "str" (string literal) or "res" (resource).

### 0.3 The five facts that matter most

1. **Keywords are not compiled in.** Every word of the language except `[`, `]`, `//` and `*` is read at runtime from a localisation INI file, and no such file ships with the program. The language is defined by **keyword roles**, which a localisation fills with words. [O] loader 0x460c94.
2. **The main program is wrapped in the hard-coded lines `[` and `]`**, not in words such as ÎNCEPUT/SFÂRŞIT. [O]
3. **The language is line-based.** One statement per line. Only the first word of a line selects the statement, and a line has at most 4 words. [O]
4. **Keywords are matched case-insensitively for ASCII letters only.** Diacritics are compared byte for byte. [O]
5. Cangurul's executor is mostly **clean and recursive**: nesting works, and procedures and loops behave as expected. The main oddities are the IF layout, the comment toggles, and the fact that Run does not reset the field (§11).

---

## 1. Overview

The kangaroo walks along the **lines of a squared field**, from one grid intersection ("node") to the next. `PAS` (step) draws the segment it walks along, `SALT` (jump) moves without drawing, and `ROTIRE` turns it 90° clockwise. Sensors report whether it faces the field border (`E_MARGINE`) or a node already reached by a drawn line (`E_LINIE`).

A program looks like this (Romanian localisation; the keyword spellings are explained in §2.3):

```
PROCEDURA PATRAT
REPETA 4 ORI
PAS
ROTIRE
SFIRSITUL REPETARII
SFIRSITUL PROCEDURII
[
REPETA 2 ORI
EXECUTA PATRAT
SALT
SALT
SFIRSITUL REPETARII
]
```

---

## 2. Localisation model and keyword roles

### 2.1 Localisation file format [O]

The index file is `<exeDir>\Language\Language.INI`:

```ini
[Files]
Files=<N>            ; number of languages            (0x462270; ident str 0x462480)
File0=<filename>     ; "File" + index                 (0x462270, 0x460c94; str 0x461fb4 / 0x462490)
File1=...
[Current]
Lang=<index>         ; read at startup, default "0"   (entry 0x464570; str 0x4649b8, 0x4649ac)
                     ; written back on exit           (FormCloseQuery 0x463448)
```

Each language file `<exeDir>\Language\<filename>` (path built at 0x460d3f–0x460d69, `'Language\'` str 0x461fc4) is an INI file:

```ini
[General]
Name=<menu caption of this language>        ; 0x462270; "General" str 0x4624ac, "Name" str 0x4624b4
[Data]
; language words (section 2.2)
FStep=  FJump=  FRotate=  FRepeat=  FEnd=  FProcedure=  FExecute=  FWhile=  FIf=  FElse=  FTimes=  FThen=
SFProcedure=  SFRepeat=  SFCycle=  Cond1=  Cond2=  NO_Cond=
; messages (section 8)
Msg1= .. Msg5=
; UI captions
File Edit Commands Options Help New New0 New1 Open Save Exit Copy Paste Cut BasicC AdvC
Step Jump Rotate PRepeat PProcedure PExecute PWhile PIf SpeedConfigure SetLanguage About
Run Stop Check ManualExec AutoExec MainTitle Version OK Ok Cancel Choose_Cond Possible_Cond Choose_Speed
StepHelp JumpHelp RotateHelp
```

All identifiers are Pascal short strings at 0x461fa0–0x462234. Values are read with `TIniFile.ReadString` with default `''` (0x45dce4; the disassembly at 0x45dd13 pushes 0 as the default). **There are no built-in fallback values**: a missing key gives an empty keyword. [O]

**[P]** A reimplementation should keep the role model and supply its own keyword sets. It does not need to copy the INI layout.

### 2.2 Keyword roles

The statement keyword table is at 0x46793c: 17 entries of `string[20]`, so values are truncated to 20 characters. It is filled by 0x460c94. The **first word** of each line is looked up in this table. [O]

| Idx | Role ID | Language-file key (str VA) | Fixed value | Role |
|---|---|---|---|---|
| 0 | `BLANK` | — | `''` | empty line |
| 1 | `MAIN_BEGIN` | — | **`[`** (hard-coded) [O] | start of the main program |
| 2 | `MAIN_END` | — | **`]`** (hard-coded) [O] | end of the main program |
| 3 | `LINE_COMMENT` | — | **`//`** (str 0x462144) [O] | line comment |
| 4 | `STEP` | FStep 0x462148 | | move one node forward, drawing |
| 5 | `JUMP` | FJump 0x462150 | | move one node forward, not drawing |
| 6 | `ROTATE` | FRotate 0x462158 | | turn 90° clockwise |
| 7 | `REPEAT` | FRepeat 0x462160 | | counted-loop head |
| 8 | `END` | FEnd 0x462168 | | first word of every block-end line |
| 9 | `PROC` | FProcedure 0x462170 | | procedure header |
| 10 | `CALL` | FExecute 0x46217c | | procedure call |
| 11 | `WHILE` | FWhile 0x462188 | | while-loop head |
| 12 | `IF` | FIf (inline near 0x462190) | | if head |
| 13 | `ELSE` | FElse 0x462190 | | else-marker line |
| 14 | `TIMES` | FTimes 0x462198 | | decorative word after the count (never checked) |
| 15 | `THEN` | FThen 0x4621a0 | | decorative word after the condition (never checked) |
| 16 | `BLOCK_COMMENT` | — | any first word starting with **`*`** [O] | block-comment toggle |

If several entries hold the same value, the **last** one wins. [O] 0x45e7fc

The second words of block ends and the condition words are stored separately, all read by 0x460c94 [O]:

| Role ID | Key (str VA) | Stored at | Role |
|---|---|---|---|
| `END_PROC_2` | SFProcedure 0x4621a8 | 0x467aa4, `string[255]` | second word of the procedure-end line |
| `END_REPEAT_2` | SFRepeat 0x4621b4 | 0x467ba4 | second word of the repeat-end line |
| `END_WHILE_2` | SFCycle 0x4621c0 | 0x467ca4 | second word of the while-end line |
| `NOT` | NO_Cond 0x4621d8 | 0x467e80 | negation word |
| `COND_EDGE` | Cond1 0x4621c8 | 0x467db4+0x00, `string[50]` | condition 1: facing the border |
| `COND_NOT_EDGE` | `NOT + ' ' + COND_EDGE` | 0x467db4+0x33 | condition 2 (built at 0x461b2b–0x461b83) |
| `COND_LINE` | Cond2 0x4621d0 | 0x467db4+0x66 | condition 3: facing a drawn node |
| `COND_NOT_LINE` | `NOT + ' ' + COND_LINE` | 0x467db4+0x99 | condition 4 |

So a block ends with a **two-word line**: `END` + `END_xxx_2`, for example `SFIRSITUL REPETARII`. Conditions are written either as one word, or as `NOT` + space + one word.

Keyword values are compared **exactly as stored** (§3.1), so they must be **upper-case ASCII** to match normalised lines. [I]

### 2.3 Romanian spellings

The binary has no keyword text, so the Romanian values come from the DFM default captions (res `TMAINFORM`, `TCONDITIONFORM`), the help-form labels and the textbook:

| Role | Evidence in the binary | Romanian keyword |
|---|---|---|
| STEP | menu and speed button "Pas" | `PAS` [I] |
| JUMP | "Salt" | `SALT` [I] |
| ROTATE | "Rotire"; help label: rotation is 90° clockwise | `ROTIRE` [I] |
| REPEAT / TIMES | menu "Repeta <N> Ori" | `REPETA` / `ORI` [I] |
| PROC | menu "Procedura <Nume>" | `PROCEDURA` [I] |
| CALL | menu "Executa <NumeProcedura>" | `EXECUTA` [I] |
| WHILE | menu "Cit <Conditie>" | `CIT` [I] |
| IF / ELSE | menu "Daca <Conditie> … Altfel …"; ConditionForm label "Daca" | `DACA` / `ALTFEL` [I] |
| THEN | inserted by the IF template; no caption | `ATUNCI` [I] (textbook) |
| Conditions | ConditionForm combo items `E_Margine`, `Nu E_Margine`, `E_Linie`, `Nu E_Linie` | `E_MARGINE`, `E_LINIE`, `NOT` = `NU` [I] |
| END | no caption | **[U]**; `SFIRSITUL` recommended, see below |
| END_*_2 | no caption | `PROCEDURII`, `REPETARII`, `CICLULUI` [I] (textbook) |

Supporting evidence for the conditions: the condition text taken from a line is truncated to `string[12]` (0x45f150, WHILE case), and `NU E_MARGINE` is exactly 12 characters long. [O]/[I]

Spelling of `END`: the textbook writes `SFÂRŞITUL`. The original files had to be upper-case ASCII without diacritics, and the program dates from Moldova in 2000, where `â` was still commonly written `î` (so ASCII `I`), as in `SFIRSIT`. So **`SFIRSITUL`** is the most probable value, and `SFARSITUL` is the main alternative. [I]

### 2.4 Keyword sets for a reimplementation

| Role | Romanian (original) [I] | English [P] | Russian [P] |
|---|---|---|---|
| MAIN_BEGIN / MAIN_END | `[` / `]` (fixed in every language) | `[` / `]` | `[` / `]` |
| STEP / JUMP / ROTATE | `PAS` / `SALT` / `ROTIRE` | `STEP` / `JUMP` / `TURN` | `ШАГ` / `ПРЫЖОК` / `ПОВОРОТ` |
| REPEAT … TIMES | `REPETA` … `ORI` | `REPEAT` … `TIMES` | `ПОВТОРИ` … `РАЗ` |
| WHILE | `CIT` | `WHILE` | `ПОКА` |
| IF … THEN / ELSE | `DACA` … `ATUNCI` / `ALTFEL` | `IF` … `THEN` / `ELSE` | `ЕСЛИ` … `ТО` / `ИНАЧЕ` |
| PROC / CALL | `PROCEDURA` / `EXECUTA` | `PROCEDURE` / `CALL` | `ПРОЦЕДУРА` / `ВЫПОЛНИ` |
| END + END_*_2 | `SFIRSITUL PROCEDURII` / `SFIRSITUL REPETARII` / `SFIRSITUL CICLULUI` | `END PROCEDURE` / `END REPEAT` / `END WHILE` | `КОНЕЦ ПРОЦЕДУРЫ` / `КОНЕЦ ПОВТОРА` / `КОНЕЦ ЦИКЛА` |
| NOT, COND_EDGE, COND_LINE | `NU`, `E_MARGINE`, `E_LINIE` | `NOT`, `AT_EDGE`, `AT_LINE` | `НЕ`, `У_КРАЯ`, `У_ЛИНИИ` |

The English and Russian sets are proposals; the original Russian and English files are unknown [U].

**[P]**
- Use Unicode-aware upper-casing.
- Optionally accept diacritic aliases, such as `REPETĂ`, `CÂT`, `DACĂ`, `EXECUTĂ` and `SFÂRŞITUL REPETĂRII`, and also `ÎNCEPUT`/`SFÂRŞIT` as aliases of `[`/`]`, for students who follow the textbook. The original accepts none of these.

---

## 3. Lexical rules

### 3.1 Line normalisation [O] 0x45e570

The program text is the list of editor lines (TMemo, CRLF). Each line is processed in four steps:
1. Upper-case ASCII `a`–`z` only (`System.UpCase` 0x4029b8). The loop counter is a byte, so only the first (length mod 256) characters are upper-cased.
2. Strip leading spaces.
3. Strip trailing spaces.
4. Collapse runs of spaces to one.

Comparisons use exact string compares (`LStrCmp` 0x403e14, `PStrCmp` 0x402b28) against the stored keyword values.

Consequences:
- Source text is case-insensitive for ASCII letters. [O]
- Diacritics (`ă â î ş ţ` in cp1250) are not upper-cased, so `repetă` ≠ `REPETĂ`. [O]
- **Only the space character 0x20 separates words.** A TAB stays inside a word and makes it unknown, which is a syntax error. [O] 0x45e570, 0x45e6b0
- Indentation with spaces is free.

### 3.2 Words [O] 0x45e6b0

After normalisation a line is split on spaces into **at most 4 words** (W0..W3). Each word is a `string[30]`, so words are truncated to 30 characters. A fifth and any further words are silently discarded.

### 3.3 Statement lookup [O] 0x45e7fc

Only **W0** selects the statement, through the 17-entry table in §2.2 (the last matching entry wins). An empty W0 matches entry 0, a blank line. A W0 that starts with `*` matches entry 16. Any other unmatched W0 gives code −1, which is a syntax error.

### 3.4 Tokens and other lexical facts

| Item | Rule | Evidence |
|---|---|---|
| Statement separator | The line break; one statement per line. | [O] |
| Blank line | Allowed when truly empty. **A line of only spaces crashes the original** (it dereferences nil after trimming: Access Violation). | [O] 0x45e601 |
| Line comment | `//` as a **separate first word**: `// text`. `//text` with no space is an unknown word, so a syntax error. | [O] |
| Block comment | A line whose first word starts with `*` toggles comment mode (§3.5). | [O] |
| Integer (REPEAT count) | W1, converted with `StrToInt` (optional sign, decimal or `$hex`). Invalid input raises `'%s' is not a valid integer value` (res string 65520). The value is used as an **unsigned 16-bit** count: 0 means no iterations and −1 means 65535. | [O] 0x45f2af–0x45f3b7 (`jbe` at 0x45f3a0, `dec si`) |
| Procedure name | W1 of the line: one space-free word, ≤ 30 characters, compared after ASCII upper-casing. **No character validation**, and the "starts with a letter" rule is not enforced. | [O] 0x45f3bc, 0x463a38 |
| Condition | W1, or `NOT` + `' '` + W2 when W1 equals `NOT` (str 0x45fa68 = `' '`). The result is truncated to 12 characters before matching. | [O] 0x45f56e |

### 3.5 Block comments with `*` (quirky) [O]

- **Checker** (0x45e7fc, 0x45e8b8): each `*…` line toggles flag 0x467da4. While the flag is on, every non-`*` line is accepted without validation.
- **Executor** (0x45f150, cases 0..2 and 0xc): each `*…` line toggles flag 0x467f80 (0x45f99f–0x45f9b1), which is reset to 0 at Run (0x46330c). While the flag is on, **only the simple commands STEP, JUMP and ROTATE are suppressed**: each of them tests the flag before its call (`cmp byte ptr [0x467f80],0` at 0x45f26a, 0x45f281, 0x45f298). REPEAT, WHILE, IF and CALL still run. The flag is global, so simple commands inside their bodies are suppressed too. A loop such as `CIT NU E_MARGINE` inside a comment region therefore never moves the kangaroo and never ends (Stop still works). [I]
- If there is an odd number of `*` lines, the checker leaves its flag on. The executor's lookups then return the comment code for every line, so the program does nothing and reports success. [I]

**[P]** Treat `*` lines as block-comment delimiters that skip everything between them, in both checking and execution. Reproduce the original behaviour only in compatibility mode.

---

## 4. Syntax

### 4.1 Program structure

```
{ procedure definitions }      ← anywhere; the editor template puts them at the top
[
{ statements }
]
```

The `[` line and the `]` line must each appear **exactly once** in the text. [O] 0x45e8b8 (str 0x45ea80, 0x45ea84)

### 4.2 EBNF (on normalised lines)

`NL` = line break, `SP` = one space (after normalisation), `K(role)` = the keyword of the current localisation, `any` = any word.

```ebnf
program        = { line_any } ;     (* exactly one "[" line and exactly one "]" line overall *)
                                    (* execution: from the first "[" line to the first "]" line after it *)
                                    (* procedures are found by searching the whole text from line 0 *)

procedure_def  = K(PROC) SP name NL { body_line NL } K(END) SP K(END_PROC_2) ;
main           = "[" NL { body_line NL } "]" ;

body_line      = simple | call | repeat | while | if | comment | blank ;
simple         = K(STEP) | K(JUMP) | K(ROTATE) ;               (* nothing else on the line *)
call           = K(CALL) SP name [ SP any [ SP any ] ] ;
repeat         = K(REPEAT) SP int [ SP any [ SP any ] ] NL     (* conventionally "REPETA n ORI" *)
                 { body_line NL }
                 K(END) SP K(END_REPEAT_2) ;
while          = K(WHILE) SP cond [ SP any ] NL
                 { body_line NL }
                 K(END) SP K(END_WHILE_2) ;
if             = K(IF) SP cond [ SP any ] NL                   (* conventionally "DACA cond ATUNCI" *)
                 single_line
                 [ NL K(ELSE) { SP any } NL single_line ] ;
single_line    = simple | call | comment | blank ;             (* exactly ONE line; see 5.6 *)

cond           = K(COND_EDGE) | K(COND_LINE)
               | K(NOT) SP K(COND_EDGE) | K(NOT) SP K(COND_LINE) ;
comment        = "//" { SP any } | "*" { char } ;
blank          = "" ;
name           = word ;            (* 1..30 non-space characters *)
int            = word ;            (* Delphi StrToInt *)
```

Notes:
- `TIMES` and `THEN` are **never checked**. They are decoration that the editor templates insert. You can omit them or replace them with any word. [O] (no references outside the template handlers 0x463720, 0x46400c)
- Block-end lines are two words: W0 = `END` and W1 = `END_xxx_2`. Anything after W1 is ignored. [O]
- Nesting: REPEAT inside REPEAT and WHILE inside WHILE are matched by counting heads (§5). **Procedure definitions do not nest.** [O]

### 4.3 How the original checks syntax [O] 0x45e8b8

It runs over every editor line, in order:
1. Normalise, split and look up W0.
2. Count lines whose W0 is `[` and lines whose W0 is `]`. Each count must be **exactly 1**.
3. For codes 1, 2, 4, 5 and 6 (`[`, `]`, STEP, JUMP, ROTATE), W1, W2 and W3 must be empty.
4. Code −1 (unknown first word) is an error.
5. Code 16 (`*`) toggles comment mode (§3.5).
6. **Every other code is accepted without further checks.** Block matching, numbers, procedure names and conditions are not checked.

The check stops at the first error. Its result is a single yes/no, with **no line number**. [O]

**[P]** A reimplementation should check everything the grammar in §4.2 requires and report line numbers. The checks are: blocks balanced, counts valid, conditions valid, called procedures defined, and IF layout correct.

---

## 5. Runtime model

### 5.1 Field and state [O]

| Item | Global (VA) | Values |
|---|---|---|
| Position x | byte 0x4680b0 | node column 0..17, left → right |
| Position y | byte 0x4680b1 | node row 0..21, top → bottom |
| Heading | byte 0x4680b4 | 0 = East (+x), 1 = North (−y), 2 = West (−x), 3 = South (+y) |
| Visited-node map | 0x4680b8 | 18 × 22 bytes, index `x*22 + y` |
| Speed | byte 0x4682c0 | 0..20; default 8 |
| Recursion depth | word 0x4682c2 | |
| Error flag / abort flag | 0x4682c4 / 0x4682c5 | |

- **Field:** 17 × 21 cells of 18 px, i.e. 18 × 22 nodes. The image is 325 × 379 px. Background `$C0C0C0`, cell outlines drawn with a yellow (`$00FFFF`) dotted pen. Built at 0x462eec. [O]
- **Sprites:** `IMG0`..`IMG3` (RT_BITMAP) match the heading: right, back, left, front. `TRUP0`/`TRUP1` are the "fall" sprites. [O]
- **Start and reset** (0x462eec, used by New Program 0x4630dc and New Window 0x463700): x = 0, y = 0 (**top-left node**), heading **East**, map cleared, drawing erased. [O]
- **Run does not reset the field.** It only clears the flags (0x46330c), so a program continues from the current position, heading and drawing. [O]

### 5.2 Simple commands [O]

- **STEP** (0x45e230):
  1. Black solid pen, 1 px.
  2. MoveTo(18x, 18y) and mark node (x,y) visited.
  3. Move one node forward.
  4. LineTo(18x′, 18y′) and mark the new node visited.
  5. Redraw the sprite.
- **JUMP** (0x45e37c): move one node forward without drawing and without marking any node.
- **ROTATE** (0x45e3f4): `heading := (heading + 3) mod 4`, so East → South → West → North → East: **90° clockwise**. The sprite is updated.
- **Edge refusal** (0x45e1b4 → 0x45dfcc): if STEP or JUMP would leave the node range 0..17 × 0..21, the kangaroo **does not move**. Instead the program does the following:
  1. Plays one of 7 random sounds.
  2. Shows a fall sprite.
  3. Shows a message box **`Whoooooooooops!!!`** (str 0x45e194).
  4. Sets both the abort and the error flag.
  5. Restores the normal sprite.

  The run stops and no further message is shown. [O]

### 5.3 Executor loop [O] 0x45f150 (called recursively with a list of lines)

1. Depth := depth + 1 on entry, depth − 1 on normal exit.
2. Find the first line equal to `[`. Execution starts at that line, which is a no-op.
3. At the start of every iteration:
   - If depth = 10000, set the error flag.
   - If the abort flag is set, set the error flag.
   - If the error flag is set, stop.
4. Normalise and split line i, look up W0, and dispatch (jump table 0x45f231):

| Code | Statement | Action |
|---|---|---|
| 4 | STEP | step, unless block-comment mode is on (§3.5) |
| 5 | JUMP | jump, unless block-comment mode is on |
| 6 | ROTATE | rotate, unless block-comment mode is on |
| 7 | REPEAT | §5.4 |
| 10 | CALL | §5.5 |
| 11 | WHILE | §5.6 |
| 12 | IF | §5.7 |
| 16 | `*` | toggle block-comment mode |
| 0, 1, 2, 3, 8, 9, 13, 14, 15, −1 and the comment code | no-op | a stray END, ELSE, THEN or PROC line does nothing |

5. i := i + 1. After an executed statement (codes 4, 5, 6, 7, 10, 11, 12):
   - Process UI events, so **Stop works everywhere**.
   - Wait **300 − 15·speed ms** (0x45f9cb–0x45f9e2). The default speed of 8 gives 180 ms; the speed range is 0..20.
6. Repeat until line i is `]` (0x45fa06).

Consequence of the "stray PROC is a no-op" rule: a procedure definition written **inside** `[ … ]` is not skipped. Its header and end lines do nothing, but its body lines run inline. [O]

### 5.4 REPEAT [O] 0x45f2af

1. `count := StrToInt(W1)`, used as unsigned 16-bit.
2. Collect the body from the following lines up to the matching end line. That is the first line with W0 = `END` and W1 = `END_REPEAT_2` at nesting level 0; the nesting level counts lines whose W0 is `REPEAT`.
3. The **raw** body lines (not normalised) are copied into a new list wrapped in `[` … `]`, and the executor recurses on it `count` times.
4. Execution continues after the end line.

### 5.5 Procedure call [O] 0x45f3bc

1. `name := W1`.
2. Search **the whole editor text** (not the current list) from line 0 for the first line with W0 = `PROC` and W1 = name.
3. Collect every following line up to the first line with W0 = `END` and W1 = `END_PROC_2`. There is no nesting count, so a procedure body cannot contain a line that looks like a procedure end.
4. Wrap the body in `[` … `]` and run it once.

- **Recursion is allowed.** Depth is limited to 10000 (Msg2), although a stack overflow probably happens first. [O]/[I]
- **Undefined procedure: the original hangs.** The search runs past the last line, and the collect loop then reads past the end of the text forever. [I] (the loops at 0x45f4xx never test the line count)

### 5.6 WHILE [O] 0x45f56e

1. Build the condition text from W1 (and W2), truncated to 12 characters. Match it against the 4 condition strings, giving an index from 1 to 4. **An unknown condition gives index 0, which is always false.** This is not an error.
2. Collect the body up to the matching end line: W0 = `END` and W1 = `END_WHILE_2`, with nesting counted on `WHILE` lines.
3. **Pre-test loop:** evaluate the condition. While it is true, run the body (recursively) and evaluate the condition again. Leave the loop if the abort flag is set.
4. Infinite loops are possible, but Stop works (§5.3).

### 5.7 IF [O] 0x45f793 (disassembly 0x45f88f–0x45f995)

1. Evaluate the condition as for WHILE. W2/W3 (`THEN`) are ignored.
2. The THEN branch is **line i+1 alone**, wrapped in `[ ]`, and runs if the condition is true.
3. If W0 of line i+2 is `ELSE`, the ELSE branch is **line i+3 alone** and runs if the condition is false. Execution then continues at line i+4. Otherwise it continues at line i+2.
4. `ELSE` is optional. Words after `ELSE` on its line are ignored, so in `ALTFEL PAS` the `PAS` is **not** executed.
5. Each branch is exactly one line. For several statements, use `EXECUTA <procedure>`. A REPEAT or WHILE header used as a branch would look for its body beyond the one-line list and raise `List index out of bounds (%d)` (res string 65455). [I]
6. **The textbook layout does not work.** In `DACA cond` / `ATUNCI ROTIRE` / `ALTFEL PAS`, the THEN line's first word is `THEN`, a no-op. The ELSE branch then becomes the line *after* `ALTFEL PAS`. [I] (follows from 2–4)

Correct layout:
```
DACA E_MARGINE ATUNCI
ROTIRE
ALTFEL
PAS
```

### 5.8 Conditions [O]

| Condition | True when | Evidence |
|---|---|---|
| `COND_EDGE` (`E_MARGINE`) | the kangaroo faces the border: heading East and x = 17, North and y = 0, West and x = 0, South and y = 21 | 0x45de80 |
| `COND_LINE` (`E_LINIE`) | the node directly ahead is marked visited (it was an endpoint of an earlier STEP), **or** `COND_EDGE` is true | 0x45dee0 |
| `NOT …` | logical negation | |

The map marks **nodes, not edges**. So `E_LINIE` is also true when a perpendicular line passes through the node ahead, and JUMP never marks anything. The "or at the edge" rule is what makes the textbook spiral program end.

---

## 6. Limits [O]

| Item | Limit |
|---|---|
| Words per line | 4, each ≤ 30 characters |
| Keyword values | 20 characters; END_*_2 values up to 255 |
| Condition text | compared on its first 12 characters |
| REPEAT count | unsigned 16-bit (0..65535) |
| Nesting / recursion depth | 10000 |
| Field | 18 × 22 nodes (17 × 21 cells) |
| Delay | 300 − 15·speed ms per executed statement, speed 0..20 |
| Upper-casing | only the first (length mod 256) characters of a line |

---

## 7. File format (`.cng`) [O]

- Plain text. It is the editor's `Lines.SaveToFile` / `LoadFromFile` (0x4635b0, 0x4638f8): single-byte ANSI (cp1250 on Romanian Windows) with CRLF.
- **No header and no field state.** Drawings are not saved.
- Save: everything from the first `.cng` in the file name (case-sensitive) is cut off, and `.cng` is appended.
- Filter: `Cangourou Files|*.cng|All Files|*.*`.
- Load resets the field first (New Program).
- The default new file name is `Cang0001.cng` (str 0x4632f4).

---

## 8. Messages

Message **texts** come from the language file and are unknown [U]. Their roles are [O]:

| Key | Stored at | Shown when | Where |
|---|---|---|---|
| Msg1 | 0x4682d8 | the run finished with no error and no stop | 0x46330c |
| Msg2 | 0x4683d8 | the run was aborted at recursion depth 10000 | 0x46330c, 0x45f1b4 |
| Msg3 | 0x4684d8 | the syntax check failed (on Run and on Check) | 0x46330c, 0x463548 |
| Msg4 | 0x4685d8 | confirmation when closing the app (Yes closes) | 0x463448 |
| Msg5 | 0x4686d8 | the syntax check passed (Check button) | 0x463548 |

Hard-coded strings [O]:
- `Whoooooooooops!!!`: the edge refusal (str 0x45e194).
- `Introduceti valoarea lui <N>: `: the prompt of the REPEAT template (str 0x4638c8).
- `Introduceti Numele Procedurii`: the prompt of the PROC and CALL templates, repeated until the answer is non-empty (str 0x463b7c / 0x463fe8).
- VCL `'%s' is not a valid integer value`: a bad REPEAT count (res string 65520). [I]

After Stop or an edge refusal, no Msg is shown. [O] 0x46330c

Suggested Romanian texts [P], none of them original:
- Msg1: `Programul a fost executat`
- Msg2: `Prea multe apeluri imbricate`
- Msg3: `Eroare de sintaxa`
- Msg4: `Doriti sa iesiti?`
- Msg5: `Sintaxa este corecta`

---

## 9. Editor templates (menu "Comenzi", shortcuts Ctrl+F1..F8) [O]

Each template inserts lines at the caret line (0x462d80, `Lines.Insert`). `K(x)` is the current localisation's value.

| Menu (handler) | Inserted lines |
|---|---|
| Pas / Salt / Rotire (0x462db4 / 0x462e1c / 0x462e84) | `K(STEP)` / `K(JUMP)` / `K(ROTATE)` |
| Repeta <N> Ori (0x463720) | `K(REPEAT) N K(TIMES)` · (empty) · `K(END) K(END_REPEAT_2)` |
| Procedura <Nume> (0x463a38) | inserted **at line 0**: `K(PROC) name` · (empty) · `K(END) K(END_PROC_2)` |
| Executa <NumeProcedura> (0x463f1c) | `K(CALL) name` |
| Cit <Conditie> (0x463ba0, condition chosen in a dialog) | `K(WHILE) cond` · (empty) · `K(END) K(END_WHILE_2)` |
| Daca <Conditie> … Altfel … (0x46400c) | `K(IF) cond K(THEN)` · (empty) · `K(ELSE)` · (empty) |
| New program (0x4630dc) | the editor becomes `[`, (empty), (empty), `]` |

---

## 10. UI model relevant to the language [O]

- **Executare** (Run, 0x46330c): copy the editor into a list, run the syntax check (Msg3 on failure), clear the flags, run the executor (§5.3), then show Msg1 or Msg2.
- **Controlul textului** (Check, 0x463548): check only (Msg3 or Msg5).
- **Stoparea Executiei** (Stop, 0x463cf4): sets the abort flag; it works during loops and calls.
- **Executarea manuala** (manual mode, 0x463d18): the Pas, Salt and Rotire buttons act on the kangaroo at once, and editing is disabled. **Executarea automata** (0x463ecc) returns to program mode.
- **Speed:** a slider from 0 to 20 (0x45f0ec).
- **Iesire:** close.

---

## 11. Quirk catalogue

Each item says whether a reimplementation should be faithful (**F**) or correct (**C**). The recommendation is [P].

| # | Quirk | Evidence | Recommendation |
|---|---|---|---|
| 1 | The main program is wrapped in `[` / `]`, not keywords. | 4.1, [O] | F (it is the language), optionally with `ÎNCEPUT`/`SFÂRŞIT` aliases |
| 2 | IF: THEN on the IF line or left out; the branch is the next line; ELSE alone on its line; the else branch is the line after that. | 5.7, [O] | F (it is the language). Consider also accepting the textbook layout as an extension. |
| 3 | Words after `ALTFEL` on its line are ignored. | 5.7, [O] | C: report an error |
| 4 | A REPEAT or WHILE used as an IF branch crashes. | 5.7, [I] | C: reject it in the checker |
| 5 | `TIMES` / `THEN` are never checked. | 4.2, [O] | F, or warn |
| 6 | A line of only spaces crashes the original. | 3.4, [O] | C: treat it as blank |
| 7 | A TAB is not whitespace. | 3.1, [O] | C |
| 8 | `//` needs a following space. | 3.4, [O] | C: accept `//text` |
| 9 | `*` comment mode suppresses only STEP, JUMP and ROTATE during execution, while loops, IF and calls inside it still run; an unbalanced `*` silently disables the program. | 3.5, [O]/[I] | C |
| 10 | An unknown condition is silently false. | 5.6, [O] | C: report an error |
| 11 | Calling an undefined procedure hangs. | 5.5, [I] | C: report an error |
| 12 | A procedure defined inside `[ … ]` runs inline. | 5.3, [O] | C: reject it |
| 13 | Run does not reset the field. | 5.1, [O] | F (teachers rely on it), with a visible Reset button |
| 14 | E_LINIE is true at the edge, and also for a perpendicular line through the node ahead. | 5.8, [O] | F (the textbook spiral depends on it) |
| 15 | The checker gives no line numbers and checks almost nothing. | 4.3, [O] | C |
| 16 | REPEAT count −1 means 65535. | 3.4, [O] | C: reject negative counts |
| 17 | Words beyond the 4th are dropped, and words are truncated to 30 characters. | 3.2, [O] | C: report an error |

---

## 12. Test cases

Each case uses the Romanian keywords and the start state from §5.1 (node (0,0), heading East, empty field). **Faithful** is the original's behaviour; **Corrected** is the behaviour recommended in §11.

| # | Program | Faithful | Corrected |
|---|---|---|---|
| T1 | `[` / `PAS` / `]` | segment (0,0)–(1,0); kangaroo at (1,0) | same |
| T2 | `[` / `SALT` / `ROTIRE` / `PAS` / `]` | no line for the jump; segment (1,0)–(1,1); heading South | same |
| T3 | `[` / `ROTIRE` / `ROTIRE` / `PAS` / `]` | heading West at x = 0: `Whoooooooooops!!!`, no move, run aborted | same |
| T4 | `[` / `pas` / `]` | same as T1 (case-insensitive) | same |
| T5 | `INCEPUT` / `PAS` / `SFIRSIT` | syntax error (no `[`/`]`; INCEPUT is unknown) | syntax error, or accepted with aliases |
| T6 | `[` / `REPETA 3 ORI` / `PAS` / `SFIRSITUL REPETARII` / `]` | kangaroo at (3,0) | same |
| T7 | `[` / `REPETA 2 ORI` / `REPETA 2 ORI` / `PAS` / `SFIRSITUL REPETARII` / `SFIRSITUL REPETARII` / `]` | kangaroo at (4,0) (nesting works) | same |
| T8 | `[` / `REPETA 3` / `PAS` / `SFIRSITUL REPETARII` / `]` (no ORI) | accepted; (3,0) | accepted, possibly with a warning |
| T9 | `PROCEDURA P` / `PAS` / `ROTIRE` / `SFIRSITUL PROCEDURII` / `[` / `REPETA 4 ORI` / `EXECUTA P` / `SFIRSITUL REPETARII` / `]` | a 1 × 1 square, ending at (0,0) heading East | same |
| T10 | `[` / `CIT NU E_MARGINE` / `SALT` / `SFIRSITUL CICLULUI` / `]` | kangaroo at (17,0), no drawing | same |
| T11 | `[` / `CIT NU E_LINIE` / `CIT NU E_LINIE` / `PAS` / `SFIRSITUL CICLULUI` / `ROTIRE` / `SFIRSITUL CICLULUI` / `]` | an inward spiral, which ends when every direction is blocked | same |
| T12 | `[` / `DACA E_MARGINE ATUNCI` / `ROTIRE` / `ALTFEL` / `PAS` / `]` | not at the edge, so PAS: (1,0) | same |
| T13 | `[` / `DACA E_MARGINE` / `ATUNCI ROTIRE` / `ALTFEL PAS` / `]` | `ATUNCI ROTIRE` is a no-op; `ALTFEL PAS` is not an ELSE marker; nothing visible happens | an error, or the textbook layout as an extension |
| T14 | `[` / `EXECUTA NIMIC` / `]` (undefined) | the original hangs | error "procedure not defined" |
| T15 | `[` / `// comentariu` / `PAS` / `]` | (1,0) | same |
| T16 | `[` / `*` / `PAS` / `*` / `SALT` / `]` | the PAS is suppressed, SALT runs: (1,0), no line | the PAS is skipped: same result |
| T17 | `PROCEDURA P` / `ROTIRE` / `SFIRSITUL PROCEDURII` / `[` / `*` / `EXECUTA P` / `*` / `PAS` / `]` | the call **runs**, but its ROTIRE is suppressed; PAS draws (0,0)–(1,0) | the call is skipped: same result |
| T18 | run T1 twice without New Program | the second run continues from (1,0) to (2,0) | same (Run does not reset) |
| T19 | `[` / `REPETA 100 ORI` / `DACA E_MARGINE ATUNCI` / `ROTIRE` / `ALTFEL` / `PAS` / `SFIRSITUL REPETARII` / `]` | traces the field border clockwise | same |

---

## 13. Textbook (Grade 8, 2020, chapter 2) compared with the binary

| Textbook says | Binary does |
|---|---|
| Program = procedures, then `ÎNCEPUT … SFÂRŞIT` | Main is wrapped in the hard-coded lines `[` and `]`; procedures may be anywhere (the template puts them at the top) [O] |
| `PROCEDURA Nume … SFÂRŞITUL PROCEDURII` | Same structure (PROC + name; END + END_PROC_2, two words); spellings from the language file. The "starts with a letter" rule is not enforced [O] |
| `EXECUTĂ Nume` | Confirmed: CALL + name [O] |
| `PAS`, `SALT`, `ROTIRE` (90° clockwise) | Confirmed. Moves go node to node along the grid lines [O] |
| `REPETĂ n ORI … SFÂRŞITUL REPETĂRII`, nesting | Confirmed. `ORI` is ignored; n is unsigned 16-bit [O] |
| `CÂT cond … SFÂRŞITUL CICLULUI` | Confirmed (the binary's menu spells it `Cit`); a pre-test loop [O] |
| `DACĂ cond` / `ATUNCI i1` / `ALTFEL i2` | **Different layout**: `DACA cond ATUNCI` / i1 / `ALTFEL` / i2 [O] |
| Conditions `E_LINIE`, `E_MARGINE`, `NU E_LINIE`, `NU E_MARGINE` | Confirmed; `NU` is a separate word [O] |
| A refusal shows a message and stops | Confirmed: `Whoooooooooops!!!`, for both PAS and SALT [O] |

---

## 14. Open questions

1. The exact keyword, condition and message spellings in every original language file, especially `FEnd` (`SFIRSITUL` or `SFARSITUL`?) and `FThen`. Copies of `Language\Language.INI` and its language files may survive on old school computers. [U]
2. Whether the original files used diacritics. The DFM captions suggest not (`Cit`, `Daca`, `Iesire`). The editor font uses RUSSIAN_CHARSET. [I]
3. The help tab "Comenzi Compuse" (compound commands) is empty in the DFM, and no code fills it. [O]/[U]
4. The exact error dialogs for the access-violation and stack-overflow cases. [U]

---

## 15. How to revalidate this specification

Tools that were used (macOS; no Windows needed):
- Ghidra 12.1.4 (Homebrew `ghidra`) with JDK 21. Ghidra's auto-analysis does not create functions for Delphi published event handlers. Create them at the RTTI method-table addresses below with `tools/DumpApp.java`: `analyzeHeadless <proj> <name> -import Cangourou.exe -scriptPath tools -postScript DumpApp.java <out.c> 0x45d000 0x470000 <handler addresses…> -deleteProject`.
- The REA reverse-engineering CLI/MCP (`npx rea-agents`) with the Ghidra provider, for evidence-tracked string searches and decompilation.
- `tools/helpers/` holds the Python helpers: `pe.py` (VA → file offset, Delphi strings), `ann.py` (annotates decompiled code with resolved literals), `dfm.py` (TPF0 form parser), `rsrc.py` (resource extraction). Set `EXE=/path/to/Cangourou.exe` before running them, and run them from their own folder.
- `evidence/` holds the parsed forms `dfm_*.txt`; `evidence/images/` and `evidence/sounds/` hold every image and sound.

Published event-handler addresses (RTTI method table) [O]:

```
FormCreate 0x4630dc  ToolButton1Click 0x46330c (Run)  ToolButton2Click 0x463548 (Check)
ToolButton3Click 0x463cf4 (Stop)  ToolButton4Click 0x463d0c (Exit)
ToolButton5Click 0x463d18 (manual)  ToolButton6Click 0x463ecc (automatic)
Pas1Click 0x462db4  Salt1Click 0x462e1c  Rotire1Click 0x462e84
RepetaNori1Click 0x463720  ProceduraNume1Click 0x463a38  CitConditie1Click 0x463ba0
ExecutaNumeProcedura1Click 0x463f1c  DacaConditieAltfel1Click 0x46400c
SalvareFisier1Click 0x4635b0  CitireFisier1Click 0x4638f8  ProgramNou1Click 0x463708
FereastraNoua1Click 0x463700  ConfigurareaVitezei1Click 0x463710  SelectLanguage1Click 0x4641a4
SpeedButton1/2/3Click 0x463d58/0x463dd4/0x463e50  FormCloseQuery 0x463448
TrackBar1Change 0x45ed3c  ComboBox1Change 0x45fe94
```

Internal routines [O]:

```
language loader 0x460c94  INI read 0x45dce4  normalise 0x45e570  split 0x45e6b0
lookup 0x45e7fc  syntax check 0x45e8b8  executor 0x45f150 (REPEAT 0x45f2af, CALL 0x45f3bc,
WHILE 0x45f56e, IF 0x45f793)  step 0x45e230  jump 0x45e37c  rotate 0x45e3f4
move/limits 0x45e1b4  refusal 0x45dfcc  E_MARGINE 0x45de80  E_LINIE 0x45dee0  field reset 0x462eec
```

Suggested revalidation order:
1. Confirm the keyword slots in §2.2 from 0x460c94 and the lookup at 0x45e7fc.
2. Confirm normalisation (§3.1).
3. Confirm the IF layout (§5.7) in the disassembly.
4. Check each quirk in §11.
5. Run the test cases in §12 against a reimplementation.
