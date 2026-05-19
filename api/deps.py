from __future__ import annotations

from arq.connections import ArqRedis
from fastapi import Request

from embeddings.bgem3 import BGEM3Embedder
from financial.cache import PriceCache
from financial.store import PriceStore
from llm.client import CortexLLM
from retrieval.reranker import CrossEncoderReranker
from retrieval.store import QdrantStore


def get_embedder(request: Request) -> BGEM3Embedder:
    return request.app.state.embedder


def get_store(request: Request) -> QdrantStore:
    return request.app.state.store


def get_reranker(request: Request) -> CrossEncoderReranker:
    return request.app.state.reranker


def get_llm(request: Request) -> CortexLLM:
    return request.app.state.llm


def get_arq_pool(request: Request) -> ArqRedis:
    return request.app.state.arq_pool


def get_price_store(request: Request) -> PriceStore:
    return request.app.state.price_store


def get_price_cache(request: Request) -> PriceCache:
    return request.app.state.price_cache
