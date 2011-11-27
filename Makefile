all:
install:
	install -d $(DESTDIR)/usr/bin
	install -d $(DESTDIR)/usr/share/applications
	install autorenamer.py $(DESTDIR)/usr/bin/autorenamer
	install autorenamer.desktop $(DESTDIR)/usr/share/applications/
