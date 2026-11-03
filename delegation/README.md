# Delegation input pack

Generated, never hand-copied. Regenerate with:

```
python tools/make_delegation_pack.py
```

Sources: `Hardware/PSDR.asc` (part types, decals, placement),
`dist/netlist/PSDR_2.6.1_netlist.json` (pin/net + part types),
`Hardware/BOMs/PSDR_2.6.1/OctopartBOM.csv` (DigiKey-numbered BOM rows).

Units: PADS ASCII coordinates are integers, **38100 units = 1 mil** (derived from
the board outline, not stated in the file).

Decal names are the layout database's own names and are **shared or inherited**: the
STM32F746 on this board sits on the decal named `STM32F746_LQFP100` in the netlist but
its pad group is called `STM32F429_LQFP100` in `*PARTDECAL*`. Never infer which chip a
footprint is for from the decal file name - use `decal_raw/_index.csv` (refdes -> part
type -> decal) for that mapping.

## Files

| file | what it is | feeds task |
|---|---|---|
| `ic_context/<ref>.md` | one IC: every pin -> net -> other pins on that net, with each part type. Passive part-type names **encode the value** (`CSM-X5R-22U-20P-10V-1210`, `RSM-6K98-1PCT-250MW-1206`) | C |
| `decal_raw/<decal>.txt` | **verbatim** `*PARTDECAL*` source block for that footprint (deliberately not decoded - compare pads against the vendor's recommended land pattern without taking my word for the grammar) | F |
| `decal_raw/_index.csv` | refdes -> placement type -> decal, terminal count, block file | F |
| `parts_census.csv` | every distinct part type with quantity and designators | A, B, E |
| `bom_rows.csv` | BOM rows carrying a DigiKey part number (qty / DK / vendor / MPN / link) | A, B |

## Answer schema (this repo machine-checks against it)

```
<file>:<row> | conclusion (one sentence) | evidence strength (datasheet text / vendor page / distributor) | source (document + revision + page or table) | verbatim English quote | contradiction with the premise | unverified items
```

Hard rules for the answering side:

1. Every conclusion needs a document name + revision + page or table, plus a short
   **verbatim English quote**. No citation = no answer.
2. Anything not read from official material is written as `unverified`. Never fill a
   gap with "typical value" or "usual practice".
3. Distributor or aggregator text is a lead, not evidence.
4. If official material contradicts the premise in the file, say so plainly.
5. Answer only the question at the top of the file. No design proposals.

Verification on our side: rows are re-checked by re-decoding the decals with
`tools/pads_asc_decal.py`, and by spot-recomputing 10 random BOM/census rows.
A batch with any failed spot check is returned whole, not cherry-picked.
