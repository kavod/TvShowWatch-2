leftparen:=(
rightparen:=)

all: 
	@echo "Usage:"
	@echo "'sudo make install' for installation"
	@echo "'sudo make uninstall' for remove installation"
	
install: JSAG
install: python_packages

JSAG:
	@python utils/execute_color.py "Installing JsonSchemaAppGenerator" python utils/pkg_manager.py "install" "JSAG"
	
uninstall:
	@python utils/execute_color.py "Removing JsonSchemaAppGenerator" python utils/pkg_manager.py "uninstall" "JSAG"
	
test:JSAG
	@python -m unittest discover
	
python_packages:
	@python utils/execute_color.py "Checking & install python packages" python utils/pkg_manager.py "install" "python_packages"
