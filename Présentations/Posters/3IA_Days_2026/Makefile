SHELL := /bin/bash
PDF := Poster_3IA_2026_Hauseux_A0.pdf
PNG := Poster_3IA_2026_Hauseux_A0.png
TEX := poster.tex beamerthemegemini.sty beamercolorthemeinria.sty references.tex $(wildcard figures/*.tex figures/defense/*.tex)
ASSETS := $(wildcard assets/*.png assets/*.pdf)

.PHONY: all pdf png check preview figures assets clean
all: pdf
pdf: $(PDF)
png: $(PNG)
$(PDF): $(TEX) $(ASSETS)
	mkdir -p build
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=build poster.tex > build/pass1.log 2>&1 || { tail -80 build/pass1.log; exit 1; }
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=build poster.tex > build/pass2.log 2>&1 || { tail -80 build/pass2.log; exit 1; }
	! grep -E 'Overfull|Missing character|LaTeX Font Warning' build/poster.log
	cp build/poster.pdf $(PDF)
$(PNG): $(PDF) render_png.py
	python3 render_png.py $(PDF) $(PNG)
check: pdf
	python3 test_six_point_geometry.py
	python3 check_poster.py $(PDF)
preview: pdf
	python3 check_poster.py $(PDF) --preview apercu.png
assets:
	python3 prepare_assets.py
	python3 prepare_defense_figures.py
figures:
	python3 make_figures.py
	python3 prepare_defense_figures.py
clean:
	rm -rf build
