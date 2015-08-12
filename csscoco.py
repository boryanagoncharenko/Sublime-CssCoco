import os, codecs
import subprocess
import sublime, sublime_plugin


PLUGIN_FOLDER = os.path.dirname(os.path.realpath(__file__))


class CsscocoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        filepath = self.view.file_name()
        if not filepath:
            return

        if not self.is_css_file(filepath):
            return

        self.view.erase_regions('csscoco_errors')

        script_name = '/Library/Frameworks/Python.framework/Versions/3.4/bin/csscoco'
        coco_file = '/Users/bore/Projects/ThesisCode/Source/samples/buffer.coco'
        
        temp_file_path = self.save_to_temp_file()
        cmd = [script_name, temp_file_path, coco_file]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False, env=os.environ)
        os.remove(temp_file_path)

        Violations.store(out, filepath)
        hints = self.get_hints()

        self.view.add_regions('csscoco_errors', hints, 
            scope='keyword',
            icon='circle',
            flags=sublime.DRAW_EMPTY | 
            sublime.DRAW_NO_FILL )

        print('coco command executed')

    def save_to_temp_file(self):
        buffer_text = self.view.substr(sublime.Region(0, self.view.size()))
        temp_file_path = PLUGIN_FOLDER + "/.__temp__"
        f = codecs.open(temp_file_path, mode="w", encoding="utf-8")
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

    def on_quick_pane_selection(self, index):
        pass
        

    def is_css_file(self, filepath):
        if len(filepath) < 4:
            return False
        return filepath[-4:] == '.css'


class CsscocoClearCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print('clear command executed')
    self.view.erase_regions("csscoco_errors")


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
        current_filepath = view.file_name()
        if not current_filepath:
            return
        
        if Violations.filepath != current_filepath:
            return
        
        (row,col) = view.rowcol(view.sel()[0].begin())
        line_number = row + 1
        
        if line_number not in Violations.line_to_violations:
            view.erase_status('csscoco_status')
            return
        
        view.set_status('csscoco_status', ''.join(Violations.line_to_violations[line_number]))


