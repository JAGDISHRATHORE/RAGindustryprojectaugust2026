.PHONY: install install-dev index assess serve demo test lint eval eval-full docker

OFFLINE = COMPLYRAG_EMBEDDING_BACKEND=lsa COMPLYRAG_RERANKER_BACKEND=none COMPLYRAG_JUDGE_BACKEND=rules

install:
	pip install -e ".[models]"

install-dev:
	pip install -e ".[models,dev]"

index:
	complyrag index

assess:
	complyrag assess

serve:
	complyrag serve

# Offline demo: no model downloads and no LLM needed
demo:
	$(OFFLINE) COMPLYRAG_INDEX_DIR=.index-offline complyrag index
	$(OFFLINE) COMPLYRAG_INDEX_DIR=.index-offline complyrag assess

test:
	pytest -q

lint:
	ruff check . && ruff format --check .

eval:
	python eval/run_eval.py --embedding lsa --reranker none --judge rules

# Needs internet access for the ONNX models and a running LLM endpoint
eval-full:
	python eval/run_eval.py --embedding fastembed --reranker cross-encoder --judge llm

docker:
	docker compose up --build -d
