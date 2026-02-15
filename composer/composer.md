## Composer MVP Plan

### Goal
Build a backend API endpoint that accepts a list of publishers and a manuscript payload, then returns one query letter per publisher using the composer few-shot examples.

### API Contract
**Endpoint**
- `POST /api/composer/query-letters`

**Request (example)**
```json
{
  "manuscript": {
    "title": "Violet Thistlethwaite Is Not a Villain Anymore",
    "word_count": 80000,
    "genre": "Adult Cozy Fantasy Romance",
    "summary": "1-2 paragraph synopsis...",
    "comps": ["Legends & Lattes", "The Undertaking of Hart and Mercy"],
    "author_bio": "Short, relevant bio...",
    "author_name": "Author Name",
    "personalization_notes": "Optional extra context"
  },
  "publishers": [
    {
      "name": "Publisher Name",
      "agent_name": "Agent Name",
      "imprints": ["Imprint A", "Imprint B"],
      "fit_notes": "Why this publisher is a fit"
    }
  ],
  "options": {
    "tone": "professional",
    "format": "classic_query_letter"
  }
}
```

**Response (example)**
```json
{
  "letters": [
    {
      "publisher": "Publisher Name",
      "agent_name": "Agent Name",
      "letter": "Dear ...",
      "status": "ok",
      "warnings": []
    }
  ],
  "errors": []
}
```

### Validation Rules
- `publishers` must be a non-empty array.
- Required manuscript fields: `title`, `word_count`, `genre`, `summary`, `author_name`.
- Optional fields: `comps`, `author_bio`, `personalization_notes`.
- If `agent_name` is missing, default to “Agent” or omit personalization line.
- If `comps` missing, allow but add a warning in response.

### Prompting Strategy
- **System message**: “You are a query letter composer...”
- **Few-shot examples**: load from `composer/letters/*/modified`.
- **User message**: provide manuscript + publisher data and explicit format constraints:
  - Include personalized opening.
  - Include title, word count, genre.
  - Include 1–2 plot paragraphs with stakes.
  - Include comps (if provided).
  - Include short bio.
  - Professional closing.
  - Keep within ~1 page.

### Generation Flow
For each publisher:
1. Build personalization line using `fit_notes` or `agent_name`.
2. Build prompt using manuscript + publisher data + few-shot examples.
3. Call model.
4. Post-process:
   - Ensure required sections present.
   - Trim extra commentary.
   - Add warnings if fields missing.
5. Return structured result.

### Implementation Steps
1. **Add endpoint** in `app/routers/composer.py`.
2. **Create composer module**:
   - `load_fewshot_examples()` reads from `composer/letters/*/modified`.
   - `build_prompt(manuscript, publisher, options)`
   - `generate_letter(prompt)`
3. **Add validation layer** for request schema.
4. **Add response formatter** for per-publisher outputs.
5. **Logging**: request id, publisher count, latency.

### Testing
- Unit tests for validation and prompt builder.
- Integration tests:
  - Single publisher.
  - Multiple publishers.
  - Missing comps.
  - Missing agent_name.
- Snapshot test for output structure (not content).

### MVP Deliverables
- Endpoint + basic request validation.
- Few-shot loader from `composer/letters`.
- Query letter generation per publisher.
- Example request/response in this doc.
