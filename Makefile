leftparen:=(
rightparen:=)

all: 
	@echo "Usage:"
	@echo "'sudo make install' for installation"
	@echo "'sudo make uninstall' for remove installation"
	
install: JSAG3
install: python_packages
install: 
	@cp utils/directory_linux.conf utils/directory.conf

JSAG3:
	@python utils/execute_color.py "Installing JSAG3" python utils/pkg_manager.py "install" "JSAG3"
	
uninstall:
	@python utils/execute_color.py "Removing JsonSchemaAppGenerator" python utils/pkg_manager.py "uninstall" "JSAG3"
	
test:JSAG3
	@python -m unittest discover
	
python_packages:
	@python utils/execute_color.py "Checking & install python packages" python utils/pkg_manager.py "install" "python_packages"

clean:
	@if [ -f syno/package.tgz ]; then rm syno/package.tgz; fi;
	@if [ -f syno/tvshowwatch2.spk ]; then rm syno/tvshowwatch2.spk; fi;
	@if [ -f utils/directory.conf ]; then rm utils/directory.conf; fi;

syno:syno/tvshowwatch2.spk
	

syno/tvshowwatch2.spk:
	@cp utils/directory_syno.conf utils/directory.conf
	@tar czf package.tgz * --exclude-vcs --exclude-vcs-ignores --exclude='package.tgz' --exclude='syno' --exclude='tests'
	@mv package.tgz syno/
	@cd syno/ &&	tar -cf tvshowwatch2.spk * --exclude-vcs --exclude='tvshowwatch2.spk'
