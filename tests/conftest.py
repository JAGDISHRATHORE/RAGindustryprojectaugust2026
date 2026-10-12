from pathlib import Path

import pytest
import yaml

from complyrag.config import Settings
from complyrag.index import build_index
from complyrag.obligations import load_obligations, load_profile

ROOT = Path(__file__).resolve().parents[1]


def offline_settings(tmp: Path, **overrides) -> Settings:
    """Settings that need no network: LSA embeddings, no reranker, rule judge."""
    base = dict(
        data_dir=ROOT / "data",
        index_dir=tmp / "index",
        runs_dir=tmp / "runs",
        audit_log=tmp / "runs" / "audit.jsonl",
        cache_dir=tmp / "cache",
        embedding_backend="lsa",
        reranker_backend="none",
        judge_backend="rules",
    )
    base.update(overrides)
    return Settings(**base)


@pytest.fixture(scope="session")
def tmp_root(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("complyrag")


@pytest.fixture(scope="session")
def settings(tmp_root) -> Settings:
    return offline_settings(tmp_root)


@pytest.fixture(scope="session")
def index(settings):
    idx = build_index(settings, persist=False)
    yield idx
    idx.close()


@pytest.fixture(scope="session")
def obligations(settings):
    return {
        o.id: o
        for o in load_obligations(
            settings.path(settings.obligations_file),
            settings.path("regulation/ai_act_articles.csv"),
        )
    }


@pytest.fixture(scope="session")
def profile(settings):
    return load_profile(settings.path(settings.profile_file))


@pytest.fixture(scope="session")
def gold():
    return yaml.safe_load((ROOT / "eval/gold/labels.yaml").read_text())["labels"]
