.PHONY: demo test lint bench media

demo:
	pocketshelf demo --open

test:
	pytest --cov=pocketshelf

lint:
	ruff check . && ruff format --check .

bench:
	pocketshelf bench -n 20000 -o /tmp/bench20k.html && node bench/load_time.mjs /tmp/bench20k.html 4 5
