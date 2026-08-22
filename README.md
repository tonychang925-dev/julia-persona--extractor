# Julia Persona Extractor

A framework for extracting evidence-backed persona structures from long-term interaction archives and generating portable Persona Packages.

The extractor does not create or define a persona.

It transforms historical interaction evidence into structured persona continuity representations through:

- archive normalization
- event segmentation
- causal experience extraction
- density scoring
- human review
- persona package generation

## Core vocabulary

- **evidence-backed**: every extracted structure keeps provenance to the source archive.
- **continuity representation**: output models how identity-relevant judgment patterns form over time.
- **causal experience**: a validated experience node connecting trigger, response, transition, consequence, and activation conditions.
- **portable package**: generated artifacts are designed to be installed, reviewed, versioned, and consumed by downstream Persona Host / Julia Core systems.

## Architecture boundary

Julia Persona Extractor is the **Data Plane** in the Julia Persona Ecosystem.

| Plane | Responsibility | This repository |
| --- | --- | --- |
| Evidence Layer | Preserve what happened | Input and normalized archive schemas |
| Extractor Data Plane | Discover structure from history | Normalization, segmentation, extraction, scoring, package generation |
| Julia Core Control Plane | Decide what may influence runtime judgment | Out of scope; consumes reviewed Persona Packages |

The extractor says: **“I found evidence that this may be important.”**

Julia Core says: **“This structure has / has not earned long-term runtime influence.”**

## v0.1 milestone

**M0 — Archive Normalization**

Goal: unify historical interaction formats into a stable Normalized Conversation Archive.

Example input:

- ChatGPT export `conversations.json`
- Claude export
- Markdown dialogue logs

Example normalized output:

```json
{
  "conversation_id": "",
  "created_at": "",
  "participants": [],
  "messages": [
    {
      "message_id": "",
      "role": "",
      "content": "",
      "timestamp": ""
    }
  ]
}
```

## Repository layout

```text
julia-persona-extractor/
├── README.md
├── LICENSE
├── pyproject.toml
├── CONTRIBUTING.md
├── docs/
├── schemas/
├── src/persona_extractor/
├── tests/
├── examples/
└── benchmarks/golden_mira/
```

`benchmarks/golden_mira/` is a benchmark fixture namespace, not a product-specific extractor.

## Development

```bash
python -m pip install -e .[dev]
pytest
```

## CLI preview

```bash
persona-extractor normalize examples/sample_archive.json --output /tmp/normalized_archive.json
```
