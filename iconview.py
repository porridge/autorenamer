#!/usr/bin/python

# ZetCode PyGTK tutorial 
#
# This example demonstrates the IconView widget.
# It shows the contents of the currently selected
# directory on the disk.
#
# author: jan bodnar
# website: zetcode.com 
# last edited: February 2009

import gnome.ui
import gnomevfs

import math
import gtk
import os

COL_PATH = 0
COL_PIXBUF = 1
COL_IS_DIRECTORY = 2


class PyApp(gtk.Window): 
    def __init__(self):
        super(PyApp, self).__init__()
        
        self.thumb_factory = gnome.ui.ThumbnailFactory(gnome.ui.THUMBNAIL_SIZE_NORMAL)
        self.set_size_request(650, 400)
        self.set_position(gtk.WIN_POS_CENTER)
        
        self.connect("destroy", gtk.main_quit)
        self.set_title("IconView")
        
        self.home_directory = os.path.realpath(os.path.expanduser('~'))
        self.current_directory = self.home_directory
        self.store_modified_handle = None

        vbox = gtk.VBox(False, 0)
       
        toolbar = gtk.Toolbar()
        vbox.pack_start(toolbar, False, False, 0)

        self.upButton = gtk.ToolButton(gtk.STOCK_GO_UP)
        self.upButton.set_is_important(True)
        toolbar.insert(self.upButton, -1)

        self.homeButton = gtk.ToolButton(gtk.STOCK_HOME)
        self.homeButton.set_is_important(True)
        toolbar.insert(self.homeButton, -1)

        self.saveButton = gtk.ToolButton(gtk.STOCK_SAVE)
        self.saveButton.set_is_important(True)
        toolbar.insert(self.saveButton, -1)

        self.discardButton = gtk.ToolButton(gtk.STOCK_CANCEL)
        self.discardButton.set_is_important(True)
        toolbar.insert(self.discardButton, -1)

        self.fileIcon = self.get_icon(gtk.STOCK_FILE)
        self.dirIcon = self.get_icon(gtk.STOCK_DIRECTORY)

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(sw, True, True, 0)

        self.store = gtk.ListStore(str, gtk.gdk.Pixbuf, bool)
        self.fill_store()

        self.iconView = gtk.IconView(self.store)
        self.iconView.set_reorderable(True)
        self.iconView.set_selection_mode(gtk.SELECTION_MULTIPLE)

        self.upButton.connect("clicked", self.on_up_clicked)
        self.homeButton.connect("clicked", self.on_home_clicked)
        self.discardButton.connect("clicked", self.on_discard_clicked)
        self.saveButton.connect("clicked", self.on_save_clicked)

        self.iconView.set_text_column(COL_PATH)
        self.iconView.set_pixbuf_column(COL_PIXBUF)

        self.iconView.connect("item-activated", self.on_item_activated)
        sw.add(self.iconView)
        self.iconView.grab_focus()

        self.add(vbox)
        self.show_all()

    def get_icon(self, name):
        theme = gtk.icon_theme_get_default()
        return theme.load_icon(name, 48, 0)
    
    def fill_store(self):
        if self.store_modified_handle:
            self.store.disconnect(self.store_modified_handle)
        self.store.clear()
        self.modified_store = False

        if self.current_directory == None:
            return

        if self.current_directory == "/":
            self.upButton.set_sensitive(False)
        else:
            self.upButton.set_sensitive(True)

        if self.current_directory == self.home_directory:
            self.homeButton.set_sensitive(False)
        else:
            self.homeButton.set_sensitive(True)
        self.saveButton.set_sensitive(False)
        self.discardButton.set_sensitive(False)

        self.initial_order = [f for f in sorted(os.listdir(self.current_directory)) if f[0] != "."]
        for fl in self.initial_order:
            full_path = os.path.join(self.current_directory, fl)
            if os.path.isdir(full_path):
                self.store.append([fl, self.dirIcon, True])
            else:
                icon = self.fileIcon
                uri = gnomevfs.get_uri_from_local_path(full_path)
                mime = gnomevfs.get_mime_type(uri)
                if self.thumb_factory.can_thumbnail(uri ,mime, 0):
                    icon = self.thumb_factory.generate_thumbnail(uri, mime)
                self.store.append([fl, icon, False])
        self.store_modified_handle = self.store.connect("row-changed", self.on_row_changed)

    def on_row_changed(self, treemodel, path, treeiter):
        self.modified_store = True
        self.upButton.set_sensitive(False)
        self.homeButton.set_sensitive(False)
        self.saveButton.set_sensitive(True)
        self.discardButton.set_sensitive(True)

    def on_home_clicked(self, widget):
        self.current_directory = os.path.realpath(os.path.expanduser('~'))
        self.fill_store()

    def on_discard_clicked(self, widget):
        self.fill_store()

    def on_save_clicked(self, widget):
        self.new_order = [e[0] for e in self.store]
        num_items = len(self.new_order)
        width = math.ceil(math.log10(num_items))
        fmt = "%%0%dd-%%s" % width
        prefixed = [(fmt % (i, f)) for i, f in zip(xrange(num_items), self.new_order)]
        conflicts = set.intersection(set(self.new_order), set(prefixed))
        if conflicts:
            self.pop_dialog("Cannot rename", "The following filenames conflict: %s" % conflicts)
            return

        renames = zip(self.new_order, prefixed)
        self.pop_dialog("rename", "%s" % "\n".join([str(t) for t in renames]))
        for source, dest in renames:
            source = os.path.join(self.current_directory, source)
            dest = os.path.join(self.current_directory, dest)
            os.rename(source, dest)
        self.fill_store()

    def pop_dialog(self, title, label_text):
        label = gtk.Label(label_text)
        dialog = gtk.Dialog(title, self, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dialog.vbox.pack_start(label)
        label.show()
        dialog.run()
        dialog.destroy()

    def on_item_activated(self, widget, item):
        model = widget.get_model()
        path = model[item][COL_PATH]
        isDir = model[item][COL_IS_DIRECTORY]

        if not isDir:
            return

        if self.modified_store:
            self.pop_dialog("Save or discard", "Save or discard first!")
            return

        self.current_directory = self.current_directory + os.path.sep + path
        self.fill_store()

    def on_up_clicked(self, widget):
        self.current_directory = os.path.dirname(self.current_directory)
        self.fill_store()
    

if __name__ == '__main__':
    PyApp()
    gtk.main()
