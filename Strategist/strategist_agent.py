import os
import json
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder
from pinecone_text.hybrid import hybrid_convex_scale

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
# Initialize Clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.llmod.ai")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("slushpilot-publishers")

# Load your custom BM25 weights
bm25 = BM25Encoder().load("bm25_publisher_weights.json")


# ==========================================
# 2. PYDANTIC SCHEMAS
# ==========================================
class ManuscriptProfile(BaseModel):
    title: str
    genre: str
    word_count: int
    blurb: str
    comparative_titles: List[str]
    target_audience: str


class HybridSearchQueries(BaseModel):
    semantic_query: str = Field(
        description="A descriptive paragraph capturing the thematic vibe and narrative style. Optimize for a dense vector search.")
    lexical_keywords: List[str] = Field(
        description="List of 5-10 specific tropes, sub-genres, and comp authors. Optimize for exact keyword matching.")


class PublisherScore(BaseModel):
    publisher_id: str
    score: int = Field(description="Relevance score from 1 to 10 based on how well they fit the manuscript.")
    reasoning: str = Field(description="A brief 1-sentence explanation for the score based on their metadata.")
    comps: List[str] = Field(description="A list of 1 to 3 specific book titles from the publisher's 'recent_comp_titles' metadata that most closely match the author's manuscript. DO NOT hallucinate titles outside of their provided metadata.")


class RerankedList(BaseModel):
    scored_publishers: List[PublisherScore]


# ==========================================
# 3. THE STRATEGIST AGENT FUNCTIONS
# ==========================================
def formulate_queries(manuscript: ManuscriptProfile) -> HybridSearchQueries:
    """Translates the manuscript into semantic and lexical queries using GPT-4o."""
    print("Strategist: Translating manuscript into search queries...")

    prompt = f"""
    Analyze this manuscript profile and generate search queries for our publisher database.
    Genre: {manuscript.genre} | Word Count: {manuscript.word_count}
    Comps: {', '.join(manuscript.comparative_titles)}
    Blurb: {manuscript.blurb}
    """

    response = client.beta.chat.completions.parse(
        model="RPRTHPB-gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are an expert literary agent AI configuring a database search."},
            {"role": "user", "content": prompt}
        ],
        response_format=HybridSearchQueries,
    )
    return response.choices[0].message.parsed


def retrieve_candidates(queries: HybridSearchQueries, top_k: int = 50) -> list:
    """Hits Pinecone with the hybrid query to get the top candidates."""
    print(f"Strategist: Querying Pinecone for top {top_k} matches...")

    # 1. Create Dense Vector
    dense_res = client.embeddings.create(input=queries.semantic_query, model="RPRTHPB-text-embedding-3-small")
    dense_vec = dense_res.data[0].embedding

    # 2. Create Sparse Vector
    sparse_string = " ".join(queries.lexical_keywords)
    sparse_vec = bm25.encode_queries(sparse_string)

    # Safety Check: If the LLM generated keywords that aren't in our BM25 vocabulary at all
    if not sparse_vec or len(sparse_vec.get("indices", [])) == 0:
        print("Warning: Lexical keywords not in vocabulary. Falling back to dense-only search.")
        results = index.query(vector=dense_vec, top_k=top_k, include_metadata=True)
    else:
        # 3. Scale vectors for Hybrid Search (alpha=0.5 balances vibe and exact keywords)
        dense_scaled, sparse_scaled = hybrid_convex_scale(dense_vec, sparse_vec, alpha=0.5)

        # 4. Search Pinecone
        results = index.query(
            vector=dense_scaled,
            sparse_vector=sparse_scaled,
            top_k=top_k,
            include_metadata=True
        )

    return results.matches


def rerank_publishers(manuscript: ManuscriptProfile, candidates: list) -> List[PublisherScore]:
    """Uses GPT-4o to evaluate the retrieved Pinecone candidates and score them."""
    print("Strategist: Reranking candidates using LLM reasoning...")

    # Prepare the metadata for the prompt (stripping out the massive vector arrays)
    clean_candidates = []
    for match in candidates:
        meta = match.metadata
        clean_candidates.append({
            "publisher_id": match.id,
            "name": meta.get("publisher_name"),
            "active_genres": meta.get("active_genres"),
            "recent_comp_titles": meta.get("recent_comp_titles"),
            "avg_goodreads_rating": meta.get("avg_goodreads_rating")
        })

    prompt = f"""
    Evaluate the following list of publishers against the author's manuscript.

    MANUSCRIPT:
    Genre: {manuscript.genre}
    Comps: {', '.join(manuscript.comparative_titles)}
    Blurb: {manuscript.blurb}

    RETRIEVED PUBLISHERS:
    {json.dumps(clean_candidates, indent=2)}

    Task 1: Score each publisher from 1 to 10 based strictly on how well their genres and recent comp titles align with the manuscript.
    Task 2: Extract the 1-3 best 'aligned_comp_titles' from their metadata that prove they publish similar books. If none are a perfect match, return an empty list.
    """

    response = client.beta.chat.completions.parse(
        model="RPRTHPB-gpt-5-mini",
        messages=[
            {"role": "system",
             "content": "You are a master publishing strategist. Identify the absolute best fit for this specific manuscript."},
            {"role": "user", "content": prompt}
        ],
        response_format=RerankedList,
    )

    return response.choices[0].message.parsed.scored_publishers


def execute_strategist_pipeline(manuscript: ManuscriptProfile):
    """The main execution flow."""
    # Step 1: Translate
    queries = formulate_queries(manuscript)
    print(f"   -> Semantic vibe: {queries.semantic_query[:60]}...")
    print(f"   -> Lexical keywords: {queries.lexical_keywords}")

    # Step 2 & 3: Retrieve
    candidates = retrieve_candidates(queries, top_k=40)

    if not candidates:
        print("No matches found in the database.")
        return []

    # Step 4: Rerank
    scored_results = rerank_publishers(manuscript, candidates)

    # Step 5: Sort and Curate Top 5
    scored_results.sort(key=lambda x: x.score, reverse=True)
    top_5 = scored_results[:5]

    print("\nSTRATEGIST FINAL RECOMMENDATIONS:")
    for rank, pub in enumerate(top_5, 1):
        # Match the ID back to the name from the candidate list
        name = next((c.metadata["publisher_name"] for c in candidates if c.id == pub.publisher_id), "Unknown Publisher")
        print(f"{rank}. {name} (Score: {pub.score}/10)\n   Why: {pub.reasoning}\n")

    return top_5


# ==========================================
# 4. TEST RUN
# ==========================================
if __name__ == "__main__":
    # Test the agent with a sample manuscript profile!
    my_book = ManuscriptProfile(
        genre="Sci-Fi Thriller",
        word_count=85000,
        blurb="In a future where memories can be extracted and sold, a black-market memory broker discovers a sequence that proves the ruling corporation engineered the collapse of Earth's atmosphere.",
        comparative_titles=["Dark Matter by Blake Crouch", "Altered Carbon by Richard K. Morgan"],
        target_audience="Adults who enjoy fast-paced, dystopian corporate espionage."
    )

    execute_strategist_pipeline(my_book)
