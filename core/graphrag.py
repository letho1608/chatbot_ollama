import csv
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


GRAPH_RESULTS = int(os.getenv("GRAPHRAG_RESULTS", "5"))
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.:+#-]*")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "the", "to", "what", "when",
    "where", "which", "who", "why", "with",
}


@dataclass(frozen=True)
class GraphTriple:
    subject: str
    relation: str
    object: str

    @property
    def relation_label(self) -> str:
        return self.relation.replace("_", " ").strip()


@dataclass(frozen=True)
class GraphSearchResult:
    triple: GraphTriple
    score: float
    content: str


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _dataset_dir() -> Path:
    return Path(os.getenv(
        "GRAPHRAG_DATASET_DIR",
        str(_project_root() / "AISecKG-cybersecurity-dataset" / "dataset"),
    ))


def _default_triples_path() -> Path:
    return Path(os.getenv("GRAPHRAG_TRIPLES_PATH", str(_dataset_dir() / "all_triples.csv")))


def _default_entities_path() -> Path:
    return Path(os.getenv("GRAPHRAG_ENTITIES_PATH", str(_dataset_dir() / "all_entity_info.csv")))


def _is_enabled() -> bool:
    return os.getenv("GRAPHRAG_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def _clean(value: Optional[str]) -> str:
    return (value or "").strip()


def _normalize(value: str) -> str:
    value = value.lower().replace("_", " ")
    return re.sub(r"\s+", " ", value).strip()


def _tokens(value: str) -> Set[str]:
    normalized = _normalize(value)
    return {tok for tok in TOKEN_RE.findall(normalized) if tok not in STOPWORDS}


def _phrase_in_query(entity: str, query_norm: str, query_tokens: Set[str]) -> bool:
    entity_norm = _normalize(entity)
    if not entity_norm:
        return False
    entity_tokens = _tokens(entity)
    if len(entity_tokens) == 1:
        return next(iter(entity_tokens)) in query_tokens
    return entity_norm in query_norm


class KnowledgeGraph:
    def __init__(
        self,
        triples: Iterable[GraphTriple],
        entity_meta: Optional[Dict[str, Dict[str, str]]] = None,
        triples_path: Optional[Path] = None,
        entities_path: Optional[Path] = None,
    ):
        self.triples = list(triples)
        self.entity_meta = entity_meta or {}
        self.triples_path = triples_path
        self.entities_path = entities_path
        self._triple_tokens: List[Set[str]] = []
        self._triple_endpoint_tokens: List[Tuple[Set[str], Set[str], Set[str]]] = []
        self._node_index: Dict[str, Set[int]] = {}
        self._node_names: Dict[str, str] = {}
        self._index()

    @classmethod
    def load(
        cls,
        triples_path: Optional[Path] = None,
        entities_path: Optional[Path] = None,
    ) -> "KnowledgeGraph":
        triples_file = triples_path or _default_triples_path()
        entities_file = entities_path or _default_entities_path()
        entity_meta = cls._load_entity_meta(entities_file)
        triples = cls._load_triples(triples_file)
        return cls(triples, entity_meta, triples_file, entities_file)

    @staticmethod
    def _load_entity_meta(path: Path) -> Dict[str, Dict[str, str]]:
        if not path.exists():
            return {}
        meta: Dict[str, Dict[str, str]] = {}
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = _clean(row.get("entityName"))
                if not name:
                    continue
                meta[_normalize(name)] = {
                    "name": name,
                    "type": _clean(row.get("entityType")),
                    "category": _clean(row.get("entityCategory")),
                    "description": _clean(row.get("entityDescription")),
                }
        return meta

    @staticmethod
    def _load_triples(path: Path) -> List[GraphTriple]:
        if not path.exists():
            return []

        triples: List[GraphTriple] = []
        seen: Set[Tuple[str, str, str]] = set()
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                subject = _clean(row.get("e1") or row.get("subject") or row.get("source"))
                relation = _clean(row.get("r") or row.get("relation") or row.get("Relation"))
                obj = _clean(row.get("e2") or row.get("object") or row.get("target"))
                if not subject or not relation or not obj:
                    continue
                key = (_normalize(subject), _normalize(relation), _normalize(obj))
                if key in seen:
                    continue
                seen.add(key)
                triples.append(GraphTriple(subject=subject, relation=relation, object=obj))
        return triples

    def _index(self) -> None:
        for idx, triple in enumerate(self.triples):
            subject_tokens = _tokens(triple.subject)
            relation_tokens = _tokens(triple.relation_label)
            object_tokens = _tokens(triple.object)
            self._triple_endpoint_tokens.append((subject_tokens, relation_tokens, object_tokens))
            self._triple_tokens.append(subject_tokens | relation_tokens | object_tokens)

            for node in (triple.subject, triple.object):
                key = _normalize(node)
                self._node_names.setdefault(key, node)
                self._node_index.setdefault(key, set()).add(idx)

    def stats(self) -> Dict[str, object]:
        return {
            "triples": len(self.triples),
            "entities": len(self._node_index),
            "triples_path": str(self.triples_path) if self.triples_path else "",
            "entities_path": str(self.entities_path) if self.entities_path else "",
        }

    def search(self, query: str, top_k: int = GRAPH_RESULTS, expand_neighbors: bool = True) -> List[GraphSearchResult]:
        query_norm = _normalize(query)
        query_tokens = _tokens(query)
        if not query_tokens or not self.triples:
            return []

        scored: Dict[int, float] = {}
        seed_nodes = self._seed_nodes(query_norm, query_tokens)

        for idx, triple in enumerate(self.triples):
            score = self._score_triple(idx, triple, query_norm, query_tokens)
            if score > 0:
                scored[idx] = score

        if expand_neighbors:
            for node_key, node_score in seed_nodes:
                for idx in self._node_index.get(node_key, set()):
                    scored[idx] = max(scored.get(idx, 0.0), node_score * 0.6)

        ranked = sorted(scored.items(), key=lambda item: (-item[1], self._fact_sort_key(item[0])))
        results: List[GraphSearchResult] = []
        for idx, score in ranked[:top_k]:
            triple = self.triples[idx]
            results.append(GraphSearchResult(
                triple=triple,
                score=score,
                content=self._format_fact(triple),
            ))
        return results

    def _seed_nodes(self, query_norm: str, query_tokens: Set[str]) -> List[Tuple[str, float]]:
        seeds: List[Tuple[str, float]] = []
        for node_key, node_name in self._node_names.items():
            node_tokens = _tokens(node_name)
            overlap = node_tokens & query_tokens
            score = float(len(overlap))
            if _phrase_in_query(node_name, query_norm, query_tokens):
                score += 2.5
            if score > 0:
                seeds.append((node_key, score))
        seeds.sort(key=lambda item: item[1], reverse=True)
        return seeds[:12]

    def _score_triple(
        self,
        idx: int,
        triple: GraphTriple,
        query_norm: str,
        query_tokens: Set[str],
    ) -> float:
        subject_tokens, relation_tokens, object_tokens = self._triple_endpoint_tokens[idx]
        triple_tokens = self._triple_tokens[idx]
        overlap = query_tokens & triple_tokens
        if not overlap:
            return 0.0

        score = float(len(overlap))
        score += len(query_tokens & relation_tokens) * 1.0
        score += len(query_tokens & subject_tokens) * 0.25
        score += len(query_tokens & object_tokens) * 0.25
        score += len(overlap) / max(len(query_tokens), 1)

        if _phrase_in_query(triple.subject, query_norm, query_tokens):
            score += 2.5
        if _phrase_in_query(triple.object, query_norm, query_tokens):
            score += 2.0 if len(object_tokens) > 1 else 0.4
        return score

    def _format_fact(self, triple: GraphTriple) -> str:
        subject = self._format_entity(triple.subject)
        obj = self._format_entity(triple.object)
        fact = f"Graph fact: {subject} {triple.relation_label} {obj}."

        subject_desc = self.entity_meta.get(_normalize(triple.subject), {}).get("description", "")
        if subject_desc:
            fact += f" {triple.subject}: {subject_desc[:220]}"
        return fact

    def _format_entity(self, entity: str) -> str:
        meta = self.entity_meta.get(_normalize(entity), {})
        display_name = meta.get("name") or entity
        entity_type = meta.get("type") or meta.get("category")
        if entity_type:
            return f"{display_name} ({entity_type})"
        return display_name

    def _fact_sort_key(self, idx: int) -> Tuple[str, str, str]:
        triple = self.triples[idx]
        return (_normalize(triple.subject), _normalize(triple.relation), _normalize(triple.object))


_DEFAULT_GRAPH: Optional[KnowledgeGraph] = None


def get_default_graph() -> KnowledgeGraph:
    global _DEFAULT_GRAPH
    if _DEFAULT_GRAPH is None:
        _DEFAULT_GRAPH = KnowledgeGraph.load()
    return _DEFAULT_GRAPH


def reset_graph_cache() -> None:
    global _DEFAULT_GRAPH
    _DEFAULT_GRAPH = None


def retrieve_graph_context(query: str, top_k: int = GRAPH_RESULTS) -> List[Tuple[str, float]]:
    if not _is_enabled():
        return []
    graph = get_default_graph()
    return [(result.content, result.score) for result in graph.search(query, top_k=top_k)]


def get_graph_status() -> Dict[str, object]:
    if not _is_enabled():
        return {"enabled": False, "triples": 0, "entities": 0}
    graph = get_default_graph()
    return {"enabled": True, **graph.stats()}
