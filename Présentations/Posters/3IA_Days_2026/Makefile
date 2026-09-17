SHELL := /bin/bash
PDF := Poster_3IA_2026_Hauseux_A0.pdf
TEX := poster.tex beamerthemegemini.sty beamercolorthemeinria.sty references.tex $(wildcard figures/*.tex)
ASSETS := $(wildcard assets/*.png assets/*.pdf)

.PHONY: all pdf check preview figures assets clean
all: pdf
pdf: $(PDF)
$(PDF): $(TEX) $(ASSETS)
	mkdir -p build
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=build poster.tex > build/pass1.log 2>&1 || { tail -80 build/pass1.log; exit 1; }
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=build poster.tex > build/pass2.log 2>&1 || { tail -80 build/pass2.log; exit 1; }
	! grep -E 'Overfull|Missing character|LaTeX Font Warning' build/poster.log
	cp build/poster.pdf $(PDF)
check: pdf
	python3 check_poster.py $(PDF)
preview: pdf
	python3 check_poster.py $(PDF) --preview apercu.png
assets:
	python3 prepare_assets.py
figures:
	python3 make_figures.py
clean:
	rm -rf build
