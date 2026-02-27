## Composer

Backend service for generating query letters from a manuscript and a list of publishers. It uses a few-shot prompt (`composer/letters/*/original.md`) and a single API endpoint to return one letter per publisher.

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
    "author_bio": "Short, relevant bio...",
    "author_name": "Author Name",
    "personalization_notes": "Optional extra context"
  },
  "publishers": [
    {
      "name": "Publisher Name",
      "comps": ["Comp Title 1", "Comp Title 2"]
    }
  ],
  "options": {
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
- Optional manuscript fields: `author_bio`, `personalization_notes`.
- Optional publisher fields: `comps`.
- Optional options fields: `paraphrase_summary` (default true).
- Few-shot examples load from `composer/letters/*/original.md`.
- Output is generated via **schema → template render** for format control, but the prompt emphasizes a more natural, human voice.

### House Style (derived from the guides)
Use the Tiffany Hawk format below as guidance; keep the tone professional but human.

### Reference Articles
- https://www.tiffanyhawk.com/blog/how-to-write-an-awesome-personalized-query-letter  
Format:
"""
Section 1:  Your Query’s Opening
This is the place to show an agent that you know who they are, that you targeted them for a reason, and that you’re not blindly sending this same query to a thousand agents you found online, most of whom are not a fit. 

The goal here is not to kiss up or stroke the agent’s ego. It’s to show that you know who they are and what they like and that you have a reason for querying them specifically.  

Next, quickly introduce your novel with title, word count, and genre.

This can be extremely simple. For example, “I’m hoping you will consider my 83,000-word historical novel, [Insert Your Title Here].” 


Section 2: The Story
This is the really hard part. You’ll want to summarize your book in one or maybe two paragraphs. This means leaving out A LOT! You need to be specific enough that they understand who and what the book is about, but the goal is not to give them a CliffsNotes rundown of the entire plot. It’s to get them to read more.

In other words, the job of a query letter is to paint your book into a pretty little box that they can instantly understand BUT at the same time make it seem special and like nothing else they’ve read before. 

If that sounds challenging, start by filling in these blanks:

MAIN CHARACTER, a ______________, desperately wants to _____________, but _____________ is getting in the way. To reach his/her goal, character tries _____________ but that plan fails because of _____________.  

Once you have the bird’s eye view of your story, add in some specific details about the characters, their location, and the lurking danger. Avoid being generic. Help them see how your character’s situation is unique.


Section 3: Your Bio
If you have any writing credentials, this is the place to mention them. Definitely include your publications or awards or your MFA. If you’ve been selected for a prestigious conference or residency, include that. 


Section 4: The Closing
End with a short, polite closing. Something as basic as, “Thank you for your time and consideration” is perfectly professional. If their submission instructions ask for additional materials like the synopsis or opening chapters, mention those attachments here.
"""
- https://janefriedman.com/query-letters/
