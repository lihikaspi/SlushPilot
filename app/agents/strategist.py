import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from openai import OpenAI
from pinecone import Pinecone
from pinecone_text.hybrid import hybrid_convex_scale
from pinecone_text.sparse import BM25Encoder

import config
from app.schemas.strategist import (
    HybridSearchQueries,
    PublisherScore,
    RerankedList,
    StrategistManuscript,
)


@dataclass
class StrategistService:
    client: OpenAI
    index: object
    bm25: BM25Encoder
    chat_model: str
    embed_model: str


def create_strategist_service() -> StrategistService:
    if not config.OPENAI_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY")
    if not config.PINECONE_API_KEY:
        raise ValueError("Missing PINECONE_API_KEY")

    client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.BASE_URL)
    pinecone_client = Pinecone(api_key=config.PINECONE_API_KEY)
    index = pinecone_client.Index(config.PINECONE_INDEX)

    bm25_path = Path(config.STRATEGIST_BM25_PATH)
    if not bm25_path.exists():
        raise FileNotFoundError(f"Missing BM25 weights: {bm25_path}")
    bm25 = BM25Encoder().load(str(bm25_path))

    return StrategistService(
        client=client,
        index=index,
        bm25=bm25,
        chat_model=config.CHAT_MODEL,
        embed_model=config.EMBED_MODEL,
    )


def formulate_queries(
    service: StrategistService, manuscript: StrategistManuscript
) -> HybridSearchQueries:
    prompt = (
        "Analyze this manuscript profile and generate search queries for our "
        "publisher database.\n"
        f"Genre: {manuscript.genre} | Word Count: {manuscript.word_count}\n"
        f"Comps: {', '.join(manuscript.comparative_titles)}\n"
        f"Blurb: {manuscript.blurb}\n"
    )

    response = service.client.beta.chat.completions.parse(
        model=service.chat_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert literary agent AI configuring a database search."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format=HybridSearchQueries,
    )
    return response.choices[0].message.parsed


def retrieve_candidates(
    service: StrategistService, queries: HybridSearchQueries, top_k: int = 50
) -> list:
    dense_res = service.client.embeddings.create(
        input=queries.semantic_query, model=service.embed_model
    )
    dense_vec = dense_res.data[0].embedding

    sparse_string = " ".join(queries.lexical_keywords)
    sparse_vec = service.bm25.encode_queries(sparse_string)

    if not sparse_vec or len(sparse_vec.get("indices", [])) == 0:
        return service.index.query(
            vector=dense_vec, top_k=top_k, include_metadata=True
        ).matches

    dense_scaled, sparse_scaled = hybrid_convex_scale(
        dense_vec, sparse_vec, alpha=0.5
    )
    results = service.index.query(
        vector=dense_scaled,
        sparse_vector=sparse_scaled,
        top_k=top_k,
        include_metadata=True,
    )
    return results.matches


def rerank_publishers(
    service: StrategistService, manuscript: StrategistManuscript, candidates: list
) -> List[PublisherScore]:
    clean_candidates = []
    for match in candidates:
        meta = match.metadata
        clean_candidates.append(
            {
                "publisher_id": match.id,
                "name": meta.get("publisher_name"),
                "active_genres": meta.get("active_genres"),
                "recent_comp_titles": meta.get("recent_comp_titles"),
                "avg_goodreads_rating": meta.get("avg_goodreads_rating"),
            }
        )

    prompt = (
        "Evaluate the following list of publishers against the author's manuscript.\n\n"
        "MANUSCRIPT:\n"
        f"Genre: {manuscript.genre}\n"
        f"Comps: {', '.join(manuscript.comparative_titles)}\n"
        f"Blurb: {manuscript.blurb}\n\n"
        "RETRIEVED PUBLISHERS:\n"
        f"{json.dumps(clean_candidates, indent=2)}\n\n"
        "Score each publisher from 1 to 10 based strictly on how well their genres "
        "and recent comp titles align with the manuscript."
    )

    response = service.client.beta.chat.completions.parse(
        model=service.chat_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a master publishing strategist. Identify the absolute best "
                    "fit for this specific manuscript."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format=RerankedList,
    )

    return response.choices[0].message.parsed.scored_publishers


def execute_strategist_pipeline(
    service: StrategistService, manuscript: StrategistManuscript, top_k: int = 40
) -> List[PublisherScore]:
    queries = formulate_queries(service, manuscript)
    candidates = retrieve_candidates(service, queries, top_k=top_k)
    if not candidates:
        return []

    scored_results = rerank_publishers(service, manuscript, candidates)
    scored_results.sort(key=lambda x: x.score, reverse=True)
    top_results = scored_results[:5]

    candidate_names = {
        match.id: (match.metadata or {}).get("publisher_name") for match in candidates
    }
    for result in top_results:
        if not result.publisher_name:
            result.publisher_name = candidate_names.get(result.publisher_id)

    return top_results
