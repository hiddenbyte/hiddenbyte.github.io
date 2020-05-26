.PHONY: build
build: html css

.PHONY: watch
watch: build html-watch

.PHONY: css
css:
	sass ./sass:./css

.PHONY: html
html: vyasa
	./vyasa/dist/vyasa -d . --compile

.PHONY: html-watch
html-watch: vyasa
	./vyasa/dist/vyasa -d . --server --watch

.PHONY: vyasa
vyasa:
	cd ./vyasa/ && make build