## Composer

Backend service for generating query letters from a manuscript and a list of publishers. It uses a few-shot prompt (`composer/letters/*/modified`) and a single API endpoint to return one letter per publisher.

### Endpoint
- `POST /api/composer/query-letters`

### Request (example)
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
      "imprints": ["Imprint A", "Imprint B"],
      "fit_notes": "Why this publisher is a fit",
      "special_criteria": "Biggest publisher"
    }
  ],
  "options": {
    "tone": "professional",
    "format": "classic_query_letter",
    "paraphrase_summary": true
  }
}
```

### Response (example)
```json
{
  "letters": [
    {
      "publisher": "Publisher Name",
      "letter": "Dear ...",
      "status": "ok",
      "warnings": []
    }
  ],
  "errors": []
}
```

### Notes
- Required manuscript fields: `title`, `word_count`, `genre`, `summary`, `author_name`.
- Optional manuscript fields: `comps`, `author_bio`, `personalization_notes`.
- Optional publisher fields: `imprints`, `fit_notes`, `special_criteria`.
- Optional options fields: `paraphrase_summary` (default true).
- Few-shot examples load from `composer/letters/*/modified`.
- Output is generated via **schema → template render** for format control.

### House Style (derived from the guides)
Use this exact order and keep the tone professional and concise:
1. **Personalized opening + book intro**  
   "I am seeking representation for my [genre] novel, [TITLE], complete at [WORD COUNT] words. I am querying you because [personalization/fit]."
2. **Story summary**  
   1–2 paragraphs focused on protagonist, goal, stakes, and specific plot details.
3. **Comps line**  
   "[TITLE] will appeal to readers of [COMP 1] and [COMP 2/3]."
4. **Bio**  
   1–2 factual sentences (credentials, relevant experience).
5. **Closing**  
   "Thank you for your time and consideration. The full manuscript is available upon request."
6. **Signature**  
   "Sincerely," or "Warmly," + author name.

### Reference Articles
- https://www.tiffanyhawk.com/blog/how-to-write-an-awesome-personalized-query-letter
- https://janefriedman.com/query-letters/
