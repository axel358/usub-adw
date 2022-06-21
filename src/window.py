# window.py
#
# Copyright 2022 Axel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gi
import urllib.parse as urlparse
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, Adw
from youtube_transcript_api import YouTubeTranscriptApi as yt_api
from youtube_transcript_api.formatters import WebVTTFormatter


@Gtk.Template(resource_path='/cu/axel/usub/window.ui')
class UsubWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'UsubWindow'

    subs_scroll = Gtk.Template.Child()
    url_entry = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        provider = Gtk.CssProvider()
        provider.load_from_resource('/cu/axel/usub/style.css')
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    @Gtk.Template.Callback()
    def parse_url(self, widget):
        video_id = self.get_video_id(self.url_entry.get_text())
        if video_id:
            try:
                sub_list = yt_api.list_transcripts(video_id)
                self.update_sub_list(sub_list)
            except Exception as e:
                dialog = Gtk.MessageDialog(transient_for=self, title='Something went wrong')
                dialog.props.text = str(e)
                dialog.props.message_type = Gtk.MessageType.ERROR
                dialog.add_buttons("OK", Gtk.ResponseType.ACCEPT)
                dialog.connect('response', self.on_error_dialog)
                dialog.show()
        else:
            pass
        
    def on_error_dialog(self, dialog, response):
        dialog.destroy()
    
    def update_sub_list(self, sub_list):
        subs_list_box = Gtk.ListBox()
        subs_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        subs_list_box.set_margin_top(10)
        subs_list_box.set_margin_bottom(10)
        subs_list_box.set_margin_start(10)
        subs_list_box.set_margin_end(10)
        self.subs_scroll.set_child(subs_list_box)
        
        for sub in sub_list:
            row = Gtk.ListBoxRow()
            row_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            row_content.append(Gtk.Image().new_from_icon_name('subtitle-symbolic'))
            sub_lang_label = Gtk.Label(label=sub.language)
            sub_lang_label.props.hexpand = True
            sub_lang_label.props.halign = Gtk.Align.START
            sub_lang_label.set_margin_start(5)
            row_content.append(sub_lang_label)
            sub_download_btn = Gtk.Button().new_from_icon_name('download-symbolic')
            sub_download_btn.add_css_class('flat')
            sub_download_btn.add_css_class('suggested-button')
            sub_download_btn.connect('clicked', self.download_sub, sub)
            sub_download_btn.set_margin_start(5)
            sub_translate_btn = Gtk.Button().new_from_icon_name('translate-symbolic')
            sub_translate_btn.set_margin_start(5)
            sub_translate_btn.add_css_class('flat')
            sub_translate_btn.connect('clicked', self.translate_sub, sub)
            row_content.append(sub_translate_btn)
            row_content.append(sub_download_btn)
            row.set_child(row_content)
            row.set_margin_bottom(5)
            subs_list_box.append(row)
            
    def download_sub(self, button, sub):
        sub_content = sub.fetch()
        self.save_sub('subtitle_' + sub.language_code+'.srt', sub_content)
        
    def save_sub(self, name, sub_content):
        dialog = Gtk.FileChooserDialog(transient_for=self, title='Save subtitle', action = Gtk.FileChooserAction.SAVE)
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Save", Gtk.ResponseType.ACCEPT)
        dialog.set_current_name(name)
        dialog.connect('response', self.on_save_sub, sub_content)
        dialog.show()
        
    def translate_sub(self, button, sub):
        dialog = Gtk.Dialog(transient_for=self, title='Enter language code', use_header_bar=True)
        lang_code_entry = Gtk.Entry()
        lang_code_entry.set_margin_top(5)
        lang_code_entry.set_margin_start(5)
        lang_code_entry.set_margin_end(5)
        lang_code_entry.set_margin_bottom(5)
        dialog.get_content_area().append(lang_code_entry)
        dialog.get_content_area().set_vexpand(False)
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_OK", Gtk.ResponseType.ACCEPT)
        dialog.connect('response', self.on_translate_sub, lang_code_entry, sub)
        dialog.show()
        
    def on_translate_sub(self, dialog, response, entry, sub):
        if response == Gtk.ResponseType.ACCEPT:
            if len((lang_code:=entry.get_text())) > 1:
                sub_content = sub.translate(lang_code).fetch()
                self.save_sub('subtitle_' + lang_code + '.srt', sub_content)
                
        dialog.destroy()
        
    def on_save_sub(self, dialog, response, sub_content):
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            
            formatter = WebVTTFormatter()
            sub = formatter.format_transcript(sub_content)
            
            with open(file_path, 'w') as file:
                file.write(sub)
                
        dialog.destroy()
        self.toast_overlay.add_toast(Adw.Toast().new(title = 'Subtitle saved'))
    
    def get_video_id(self, url):
        url_data = urlparse.urlparse(url)
        if url_data.hostname == 'youtu.be':
            return url_data.path[1:]
        if url_data.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if url_data.path == '/watch':
                query = urlparse.parse_qs(url_data.query)
                return query['v'][0]
            if url_data.path[:7] == '/embed/':
                return url_data.path.split('/')[2]
            if url_data.path[:3] == '/v/':
                return url_data.path.split('/')[2]
        return None
    
    @Gtk.Template.Callback()
    def on_about_action(self, widget):
        about = AboutDialog(self)
        about.present()


class AboutDialog(Gtk.AboutDialog):

    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self)
        self.props.program_name = 'USub'
        self.props.version = "0.1.0"
        self.props.authors = ['Axel']
        self.props.copyright = '(C) 2021 Axel'
        self.props.logo_icon_name = 'cu.axel.usub'
        self.set_transient_for(parent)

