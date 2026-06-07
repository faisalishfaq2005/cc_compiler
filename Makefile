PYTHON = python
SRC    = src
TEST   = test
OUT    = output
DOCS   = docs

.PHONY: all clean test lexer rd ll lr symtab first-follow \
        ll-table lr-table help docs-pdf

# Default target
all: test

help:
	@echo "============================================="
	@echo "  Decaf Mini-Compiler"
	@echo "  CS-471L Compiler Construction Lab, UET Lahore"
	@echo "============================================="
	@echo ""
	@echo "Usage: make [target] [FILE=path/to/file.decaf]"
	@echo ""
	@echo "Targets:"
	@echo "  all          - Run all modules on all test files (default)"
	@echo "  test         - Run all parsers on test1 through test5"
	@echo "  lexer        - Run lexer only"
	@echo "  rd           - Run recursive descent parser + symbol table"
	@echo "  ll           - Run LL(1) predictive parser"
	@echo "  lr           - Run SLR(1) parser"
	@echo "  symtab       - Run RD parser with symbol table dump"
	@echo "  first-follow - Print FIRST and FOLLOW sets"
	@echo "  ll-table     - Print LL(1) parse table"
	@echo "  lr-table     - Print SLR(1) action/goto table"
	@echo "  clean        - Remove output files and Python caches"
	@echo ""
	@echo "FILE variable (default: test/test1_valid.decaf):"
	@echo "  make rd FILE=test/test2_class.decaf"

# ----------------------------------------------------------------
# Run all test files through all modules
# ----------------------------------------------------------------
test:
	@for f in $(TEST)/test*.decaf; do \
		echo ""; \
		echo "=== Testing $$f ==="; \
		$(PYTHON) $(SRC)/main.py $$f --all || true; \
	done

# ----------------------------------------------------------------
# Per-module targets (FILE can be overridden on command line)
# ----------------------------------------------------------------
FILE ?= test/test1_valid.decaf

lexer:
	$(PYTHON) $(SRC)/main.py $(FILE) --lexer

rd:
	$(PYTHON) $(SRC)/main.py $(FILE) --rd --symtab

ll:
	$(PYTHON) $(SRC)/main.py $(FILE) --ll

lr:
	$(PYTHON) $(SRC)/main.py $(FILE) --lr

symtab:
	$(PYTHON) $(SRC)/main.py $(FILE) --rd --symtab

first-follow:
	$(PYTHON) $(SRC)/main.py $(FILE) --first --follow

ll-table:
	$(PYTHON) $(SRC)/main.py $(FILE) --ll-table

lr-table:
	$(PYTHON) $(SRC)/main.py $(FILE) --lr-table

# ----------------------------------------------------------------
# Build LaTeX documentation (requires pdflatex)
# ----------------------------------------------------------------
docs-pdf:
	@echo "Compiling LaTeX documentation..."
	@cd $(DOCS) && pdflatex grammar.tex     || echo "pdflatex not found"
	@cd $(DOCS) && pdflatex first_follow.tex || true
	@cd $(DOCS) && pdflatex ll1_table.tex   || true
	@cd $(DOCS) && pdflatex lr_table.tex    || true
	@cd $(DOCS) && pdflatex report.tex      || true

# ----------------------------------------------------------------
# Clean
# ----------------------------------------------------------------
clean:
	@echo "Cleaning output files..."
	@-rm -f $(OUT)/*.txt
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find $(DOCS) -name "*.aux" -delete 2>/dev/null || true
	@find $(DOCS) -name "*.log" -delete 2>/dev/null || true
	@find $(DOCS) -name "*.toc" -delete 2>/dev/null || true
	@echo "Done."
