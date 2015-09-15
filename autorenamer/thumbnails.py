# AutoRenamer - renames files so they sort in a given order
# Copyright 2015 Marcin Owsiany <marcin@owsiany.pl>

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

from gi.repository import Gio
from gi.repository import GLib
try:
  from gi.repository import GnomeDesktop
except:
  logging.exception('Importing GNOME desktop library failed. Thumbnail support will be limited.')
  GnomeDesktop = None
from gi.repository import Gtk

  
_ICON_SIZE = 48

class Thumbnailer(object):
  """Handles thumbnails for autorenamer."""

  def __init__(self):
    if GnomeDesktop:
      self._thumbnail_factory = GnomeDesktop.DesktopThumbnailFactory()
    else:
      self._thumbnail_factory = None
    self._theme = Gtk.IconTheme.get_default()
    self.file_icon = self._theme.load_icon(Gtk.STOCK_FILE, _ICON_SIZE, 0)
    self.dir_icon = self._theme.load_icon(Gtk.STOCK_DIRECTORY, _ICON_SIZE, 0)

  def pixbuf_for(self, full_path, is_dir):
    if is_dir:
      logging.debug('%s is a dir', full_path)
      return self.dir_icon

    uri = GLib.filename_to_uri(full_path)
    gio_file = Gio.File.new_for_path(full_path)
    file_info = gio_file.query_info('*', Gio.FileQueryInfoFlags.NONE, None)
    mtime = file_info.get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_MODIFIED)

    # Use existing thumbnail if any.
    if self._thumbnail_factory:
      existing_thumbnail = self._thumbnail_factory.lookup(uri, mtime)
    else:
      existing_thumbnail = file_info.get_attribute_byte_string(Gio.FILE_ATTRIBUTE_THUMBNAIL_PATH)
    if existing_thumbnail:
      logging.debug('%s has existing thumbnail', full_path)
      image = Gtk.Image.new_from_file(existing_thumbnail)
      if image:
        return image.get_pixbuf()
      else:
        logging.debug('%s failed to load existing thumbnail', full_path)

    # Attempt to generate a new thumbnail, saving the result as appropriate.
    if self._thumbnail_factory:
      mime_type = file_info.get_attribute_as_string(Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE)
      if self._thumbnail_factory.can_thumbnail(uri, mime_type, mtime):
        logging.debug('%s can be thumbnailed by GNOME thumbnailer', full_path)
        pixbuf = self._thumbnail_factory.generate_thumbnail(uri, mime_type)
        if pixbuf:
          self._thumbnail_factory.save_thumbnail(pixbuf, uri, mtime)
          return pixbuf
        else:
          logging.debug('%s could NOT be thumbnailed by GNOME thumbnailer after all', full_path)
          self._thumbnail_factory.create_failed_thumbnail(uri, mtime)

    # Use an appropriate icon.
    icon = file_info.get_icon()
    if icon:
      icon_info = self._theme.lookup_by_gicon(icon, _ICON_SIZE, Gtk.IconLookupFlags(0))
      if icon_info:
        loaded_icon = icon_info.load_icon()
        if loaded_icon:
          logging.debug('%s has a suggested icon', full_path)
          return loaded_icon
        else:
          logging.debug('%s icon suggestion could not be loaded', full_path)
      else:
        logging.debug('%s icon suggestion could not be looked up in current theme', full_path)
    else:
      logging.debug('%s has NO particular icon suggestion', full_path)

    # As last resort, use a generic file icon.
    return self.file_icon
