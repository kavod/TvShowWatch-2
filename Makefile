leftparen:=(
rightparen:=)

all: 
	@echo "Usage:"
	@echo "'sudo make install' for installation"
	@echo "'sudo make uninstall' for remove installation"
	
install: JSAG
install: tvdb-api

JSAG:
	@python utils/execute_color.py "Installing JsonSchemaAppGenerator" python utils/pkg_manager.py "install" "JSAG"
	
tvdb-api:
	@if [ $(shell pip list|sed -n '/tvdb-api \${leftparen}.*\${rightparen}$$/p' |wc -l) -eq 0 ]; \
	then python utils/execute_color.py "Installing tvdb_api" python utils/pkg_manager.py "install" "tvdb-api"; \
	fi
	
uninstall:
	@python utils/execute_color.py "Removing JsonSchemaAppGenerator" python utils/pkg_manager.py "uninstall" "JSAG"
	
test:JSAG
	@python utils/execute_color.py "Process unittests" python -m unittest discover
