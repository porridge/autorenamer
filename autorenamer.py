#!/usr/bin/python
# AutoRenamer - renames files so they sort in a given order
# Copyright 2011-2016 Marcin Owsiany <marcin@owsiany.pl>

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

import logging
import math
import random
from gi.repository import Gtk
from gi.repository import GdkPixbuf
import os

from autorenamer import thumbnails

COL_PATH = 0
COL_PIXBUF = 1
COL_IS_DIRECTORY = 2
APP_NAME = "AutoRenamer"

class AutoRenamer(Gtk.Window):

    def close(self, unused_event, unused_data):
        if self.modified_store:
            return not self.pop_dialog("Discard changes?", "Do you want to exit and lose your changes?", ok_only=False, accept_save=False)
        else:
            return False

    def __init__(self):
        super(AutoRenamer, self).__init__()

        self.thumbnailer = thumbnails.Thumbnailer()
        self.set_size_request(650, 400)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.connect("delete-event", self.close)
        self.connect("destroy", Gtk.main_quit)

        self.set_title(APP_NAME)

        self.home_directory = os.path.realpath(os.path.expanduser('~'))
        self.current_directory = os.path.realpath('.')
        self.store_modified_handle = None

        self.upButton = Gtk.ToolButton(Gtk.STOCK_GO_UP)
        self.upButton.set_is_important(True)
        self.upButton.connect("clicked", self.on_up_clicked)

        self.homeButton = Gtk.ToolButton(Gtk.STOCK_HOME)
        self.homeButton.set_is_important(True)
        self.homeButton.connect("clicked", self.on_home_clicked)

        self.saveButton = Gtk.ToolButton(Gtk.STOCK_SAVE)
        self.saveButton.set_is_important(True)
        self.saveButton.connect("clicked", self.on_save_clicked)

        self.discardButton = Gtk.ToolButton(Gtk.STOCK_CANCEL)
        self.discardButton.set_is_important(True)
        self.discardButton.connect("clicked", self.on_discard_clicked)

        shuffle_image = Gtk.Image.new_from_icon_name("media-playlist-shuffle", Gtk.IconSize.BUTTON)
        self.randomizeButton = Gtk.ToolButton()
        self.randomizeButton.set_icon_widget(shuffle_image)
        self.randomizeButton.set_is_important(True)
        self.randomizeButton.set_label("Shuffle")
        self.randomizeButton.connect("clicked", self.on_randomize_clicked)

        self.dirsButton = Gtk.ToolButton(Gtk.STOCK_DIRECTORY)
        self.dirsButton.set_is_important(True)
        self.dirsButton.set_label("Toggle directories")
        self.dirsButton.connect("clicked", self.on_dirs_clicked)

        toolbar = Gtk.Toolbar()
        toolbar.insert(self.upButton, -1)
        toolbar.insert(self.homeButton, -1)
        toolbar.insert(self.saveButton, -1)
        toolbar.insert(self.discardButton, -1)
        toolbar.insert(self.randomizeButton, -1)
        toolbar.insert(self.dirsButton, -1)

        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        vbox = Gtk.VBox(False, 0)
        vbox.pack_start(toolbar, False, False, 0)
        vbox.pack_start(sw, True, True, 0)

        self.store = Gtk.ListStore(str, GdkPixbuf.Pixbuf, bool)
        self.fill_store()

        self.iconView = Gtk.IconView(self.store)
        self.iconView.set_reorderable(True)
        self.iconView.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.iconView.set_text_column(COL_PATH)
        self.iconView.set_pixbuf_column(COL_PIXBUF)
        self.iconView.connect("item-activated", self.on_item_activated)

        sw.add(self.iconView)
        self.iconView.grab_focus()

        self.add(vbox)
        self.show_all()

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
        self.randomizeButton.set_sensitive(bool(self.initial_order))
        self.set_title(APP_NAME + ": " + self.current_directory)
        directories_present = False
        for fl in self.initial_order:
            full_path = os.path.join(self.current_directory, fl)
            is_dir = os.path.isdir(full_path)
            if is_dir:
                directories_present = True
            self.store.append([fl, self.thumbnailer.pixbuf_for(full_path, is_dir), is_dir])
        self.store_modified_handle = self.store.connect("row-deleted", self.on_row_deleted)
        self.dirsButton.set_sensitive(directories_present)

    def on_row_deleted(self, treemodel, path):
        self.on_order_changed()

    def on_order_changed(self):
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

    def on_dirs_clicked(self, widget):
        all_store_indices = xrange(len(self.store))
        directory_indices = [index for index, item in zip(all_store_indices, self.store) if item[COL_IS_DIRECTORY]]
        for index in directory_indices:
            path = Gtk.TreePath(index)
            if self.iconView.path_is_selected(path):
                self.iconView.unselect_path(path)
            else:
                self.iconView.select_path(path)

    def selected_elements_in_order(self):
       selected_indices = [path[0] for path in self.iconView.get_selected_items()]
       selected_indices.sort()
       return [self.store[index] for index in selected_indices]

    def on_save_clicked(self, widget):
        new_order_elements = self.selected_elements_in_order() or self.store
        rename_selected_only = new_order_elements is not self.store
        ordered_names_to_rename = [e[COL_PATH] for e in new_order_elements]

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
        if self.pop_dialog("Renames", "The following renames will be performed." +
                           (rename_selected_only and "\nNote: only the selected entries are renamed." or ""),
                           ok_only=False,
                           column_names=("From", "To"),
                           column_values=renames):
            for source, dest in renames:
                source = os.path.join(self.current_directory, source)
                dest = os.path.join(self.current_directory, dest)
                os.rename(source, dest)
            self.fill_store()

    def pop_dialog(self, title, label_text, ok_only=True, accept_save=True, column_names=None, column_values=None):
        label = Gtk.Label(label=label_text)
        if ok_only:
            buttons = (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT)
        elif accept_save:
            buttons = (Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT, Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT)
        else:
            buttons = (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT, Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT)
        dialog = Gtk.Dialog(title, self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, buttons)
        dialog.vbox.props.homogeneous = False
        dialog.vbox.pack_start(label, False, False, 0)
        if column_names is not None and column_values is not None:
            types = [str for c in column_names]
            store = Gtk.ListStore(*types)
            for value in column_values:
                store.append(value)
            list_view = Gtk.TreeView(store)
            list_view.set_reorderable(False)
            sw = Gtk.ScrolledWindow()
            sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
            sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            for name, offset in zip(column_names, range(len(column_names))):
                list_view.append_column(Gtk.TreeViewColumn(name, Gtk.CellRendererText(), text=offset))
            sw.add(list_view)
            dialog.vbox.pack_start(sw, True, True, 0)
        dialog.show_all()
        try:
            return dialog.run() == Gtk.ResponseType.ACCEPT
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

    def on_randomize_clicked(self, widget):
        order = range(len(self.initial_order))
        random.shuffle(order)
        self.store.reorder(order)
        self.on_order_changed()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    AutoRenamer()
    Gtk.main()
