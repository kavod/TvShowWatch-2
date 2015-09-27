all: 
	@echo "Usage:"
	@echo "'sudo make install' for installation"
	@echo "'sudo make uninstall' for remove installation"
	
install:JSAG

JSAG:
	@python utils/execute_color.py "Installing JsonSchemaAppGenerator" python utils/pkg_manager.py "install" "JSAG"
	
uninstall:
	@python utils/execute_color.py "Removing JsonSchemaAppGenerator" python utils/pkg_manager.py "uninstall" "JSAG"
	
test:JSAG
	@python utils/execute_color.py "Process unittests" python -m unittest discover
