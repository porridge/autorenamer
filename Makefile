all:
install:
	install -d $(DESTDIR)/usr/bin
	install autorenamer.py $(DESTDIR)/usr/bin/autorenamer
