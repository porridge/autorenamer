#!/usr/bin/python
# AutoRenamer - renames files so they sort in a given order
# Copyright 2011 Marcin Owsiany <marcin@owsiany.pl>

# Derived from an example program from the ZetCode.com PyGTK tutorial
# Copyright 2007-2009 Jan Bodnar

#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#  3. Neither the name of the Authors nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
#  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
#  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#  SUCH DAMAGE.

import gnome.ui
import gnomevfs

import math
import gtk
import os

COL_PATH = 0
COL_PIXBUF = 1
COL_IS_DIRECTORY = 2
APP_NAME = "AutoRenamer"

class AutoRenamer(gtk.Window):
    def __init__(self):
        super(AutoRenamer, self).__init__()

        self.thumb_factory = gnome.ui.ThumbnailFactory(gnome.ui.THUMBNAIL_SIZE_NORMAL)
        self.set_size_request(650, 400)
        self.set_position(gtk.WIN_POS_CENTER)

        self.connect("destroy", gtk.main_quit)
        self.set_title(APP_NAME)

        self.home_directory = os.path.realpath(os.path.expanduser('~'))
        self.current_directory = os.path.realpath('.')
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

        self.selectedToggle = gtk.ToggleToolButton()
        self.selectedToggle.set_label("Only selected")
        self.selectedToggle.set_is_important(True)
        toolbar.insert(self.selectedToggle, -1)

        self.dirsToggle = gtk.ToggleToolButton()
        self.dirsToggle.set_label("Exclude directories")
        self.dirsToggle.set_is_important(True)
        toolbar.insert(self.dirsToggle, -1)

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
        self.set_title(APP_NAME + ": " + self.current_directory)
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
        self.store_modified_handle = self.store.connect("row-deleted", self.on_row_deleted)

    def on_row_deleted(self, treemodel, path):
        if self.initial_order == [e[0] for e in self.store]:
            self.modified_store = False
            self.upButton.set_sensitive(True)
            self.homeButton.set_sensitive(True)
            self.saveButton.set_sensitive(False)
            self.discardButton.set_sensitive(False)
        else:
            self.modified_store = True
            self.upButton.set_sensitive(False)
            self.homeButton.set_sensitive(False)
            self.saveButton.set_sensitive(True)
            self.discardButton.set_sensitive(True)

    def on_home_clicked(self, widget):
        self.current_directory = self.home_directory
        self.fill_store()

    def on_discard_clicked(self, widget):
        self.fill_store()

    def on_save_clicked(self, widget):
        if self.selectedToggle.get_active():
            selected_indexes = [path[0] for path in self.iconView.get_selected_items()]
            selected_indexes.sort()
            new_order_elements = [self.store[index] for index in selected_indexes]
        else:
            new_order_elements = self.store

        if self.dirsToggle.get_active():
            ordered_names_to_rename = [e[COL_PATH] for e in new_order_elements if not e[COL_IS_DIRECTORY]]
        else:
            ordered_names_to_rename = [e[COL_PATH] for e in new_order_elements]

        if not ordered_names_to_rename:
            self.pop_dialog("Nothing to rename", "Check the enabled options and selected elements.")
            return

        num_items = len(ordered_names_to_rename)
        width = math.ceil(math.log10(num_items))
        fmt = "%%0%dd-%%s" % width
        prefixed = [(fmt % (i, f)) for i, f in zip(xrange(num_items), ordered_names_to_rename)]
        all_names = [e[COL_PATH] for e in self.store]
        conflicts = set.intersection(set(all_names), set(prefixed))
        if conflicts:
            self.pop_dialog("Cannot rename", "The following filenames conflict.",
                            column_names=("Filename",),
                            column_values=[(c,) for c in conflicts])
            return

        renames = zip(ordered_names_to_rename, prefixed)
        if self.pop_dialog("Renames", "The following renames will be performed.",
                           ok_only=False,
                           column_names=("From", "To"),
                           column_values=renames):
            for source, dest in renames:
                source = os.path.join(self.current_directory, source)
                dest = os.path.join(self.current_directory, dest)
                os.rename(source, dest)
            self.fill_store()

    def pop_dialog(self, title, label_text, ok_only=True, column_names=None, column_values=None):
        label = gtk.Label(label_text)
        if ok_only:
            buttons = (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        else:
            buttons = (gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        dialog = gtk.Dialog(title, self, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, buttons)
        dialog.vbox.props.homogeneous = False
        dialog.vbox.pack_start(label, False)
        if column_names is not None and column_values is not None:
            types = [str for c in column_names]
            store = gtk.ListStore(*types)
            for value in column_values:
                store.append(value)
            list_view = gtk.TreeView(store)
            list_view.set_reorderable(False)
            sw = gtk.ScrolledWindow()
            sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            for name, offset in zip(column_names, range(len(column_names))):
                list_view.append_column(gtk.TreeViewColumn(name, gtk.CellRendererText(), text=offset))
            sw.add(list_view)
            dialog.vbox.pack_start(sw, True, True, 0)
        dialog.show_all()
        try:
            return dialog.run() == gtk.RESPONSE_ACCEPT
        finally:
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
    AutoRenamer()
    gtk.main()
