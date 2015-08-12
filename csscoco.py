import os, codecs
import subprocess
import sublime, sublime_plugin


PLUGIN_FOLDER = os.path.dirname(os.path.realpath(__file__))
STYLE_GUIDES_FOLDER = PLUGIN_FOLDER + '/StyleGuides'
SETTINGS_FILE = 'csscoco.sublime-settings'


class CsscocoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        filepath = self.view.file_name()
        if not self.is_file_correct(filepath):
            return
        
        self.view.erase_regions('csscoco_errors')
        script_name = self.get_script_name()
        coco_file = self.get_conventions_file()

        temp_file_path = self.save_to_temp_file()
        cmd = [script_name, temp_file_path, coco_file]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False, env=os.environ)
        os.remove(temp_file_path)

        Violations.store(out, filepath)
        hints = self.get_hints()

        self.view.add_regions('csscoco_errors', hints, 
            scope='keyword',
            icon='circle',
            flags=sublime.DRAW_EMPTY | sublime.DRAW_NO_FILL )

    def is_file_correct(self, filepath):
        return filepath and self.is_css_file(filepath)

    def get_script_name(self):
        s = sublime.load_settings(SETTINGS_FILE)
        return s.get('csscoco_path')

    def get_conventions_file(self):
        s = sublime.load_settings(SETTINGS_FILE)
        return ''.join([STYLE_GUIDES_FOLDER, '/', s.get('conventions_file')])

    def save_to_temp_file(self):
        buffer_text = self.view.substr(sublime.Region(0, self.view.size()))
        temp_file_path = ''.join([PLUGIN_FOLDER, '/', '.__temp__'])
        f = codecs.open(temp_file_path, mode='w', encoding='utf-8')
        f.write(buffer_text)
        f.close()
        return temp_file_path

    def get_hints(self):
        hints = []
        for line_number in Violations.line_to_violations:
            for message in Violations.line_to_violations[line_number]:
                hint = self.view.text_point(int(line_number) - 1, 0)
                hint_line = self.view.line(hint)
                hints.append(hint_line)
        return hints

    def is_css_file(self, filepath):
        return filepath.endswith('.css')


class CsscocoClearCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    self.view.erase_regions('csscoco_errors')
    self.view.erase_status('csscoco_status')


class CsscocoSettingsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        w = self.view.window()
        w.open_file(PLUGIN_FOLDER + '/' + SETTINGS_FILE)


class Violations(object):

    line_to_violations = {}
    filepath = ''

    @classmethod
    def store(cls, violations_string, filepath):
        result = {}
        for line in violations_string.splitlines():
            line_number, message = Violations.get_line_and_violation(str(line))
            if line_number in result:
                result[line_number].add(message)
            else:
                result[line_number] = set([message])
        cls.line_to_violations = result
        cls.filepath = filepath

    @classmethod
    def get_line_and_violation(cls, string_line):
        pos = string_line.find(':')
        line_number = int(string_line[20:pos])
        message = string_line[pos+2:-1]
        return line_number, message


class SelectionListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        if not self.should_update_status(view.file_name()):
            return
        
        (row,col) = view.rowcol(view.sel()[0].begin())
        line_number = row + 1
        
        if line_number not in Violations.line_to_violations:
            view.erase_status('csscoco_status')
            return
        
        view.set_status('csscoco_status', ''.join(Violations.line_to_violations[line_number]))

    def should_update_status(self, file_path):
        return file_path and Violations.filepath == file_path

    def on_post_save(self, view):
        if self.should_run_on_save() and self.is_file_correct(view.file_name()):
            sublime.active_window().run_command("csscoco")

    def should_run_on_save(self):
        s = sublime.load_settings(SETTINGS_FILE)
        return s.get('run_on_save', False)

    def is_file_correct(self, filepath):
        return filepath.endswith('.css')



