.PHONY: build
build: html css

.PHONY: css
css:
	sass ./sass:./css

.PHONY: html
html:
	cd ./vyasa/ && make build && cd .. && ./vyasa/dist/vyasa compile .