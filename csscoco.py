import os, codecs
import subprocess
import sublime, sublime_plugin


PLUGIN_FOLDER = os.path.dirname(os.path.realpath(__file__))
SETTINGS_FILE = 'csscoco.sublime-settings'
NO_VIOLATIONS_STATUS = 'No violations! Hooraay!'
INVALID_CSS_STATUS = 'Please check the validity of your CSS!'
COCO_ERRORS_STATUS = 'There are errors in your coco file. Open Sublime console (View > Show Console) for details'
ERROR_LOG_HEADER = '*** CssCoco *** The following errors were found is your .coco file:'


class CsscocoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        filepath = self.view.file_name()
        if not Utils.is_file_correct(filepath):
            return
        
        Utils.clear_regions(self.view)
        script_name = self.get_script_name()
        coco_file = self.get_conventions_file()
        temp_file_path = self.save_to_temp_file()
        cmd = [script_name, temp_file_path, coco_file]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False, env=os.environ)
        os.remove(temp_file_path)
        out = out.decode('utf-8') 

        if self._is_invalid_css(out):
            result = CocoResult.create_invalid_css_result()
            Utils.set_status(self.view, INVALID_CSS_STATUS)
        elif self._contains_errors(out):
            coco_errors = self._construct_coco_errors(out)
            result = CocoResult.create_coco_errors_result(coco_errors)
            Utils.set_status(self.view, COCO_ERRORS_STATUS)
            Utils.print_in_console(ERROR_LOG_HEADER + '\n' + coco_errors)
        else:
            violations = self._construct_violations(out)
            result = CocoResult.create_violations_result(violations)
            hints = self.get_hints(violations)
            if not hints:
                Utils.set_status(self.view, NO_VIOLATIONS_STATUS)
            else:
                Utils.draw_regions(self.view, hints)
            
        Storage.store(filepath, result)

    def _is_invalid_css(self, output):
        return output.startswith('Please check')

    def _contains_errors(self, output):
        return output.startswith('Error log:')

    def _construct_coco_errors(self, output):
        return output[11:].strip()

    def _construct_violations(self, output):
        result = {}
        for line in output.splitlines():
            if not line:
                continue
            line_number, message = self._get_line_and_violation(line)
            if line_number in result:
                result[line_number].add(message)
            else:
                result[line_number] = set([message])
        return result

    def _get_line_and_violation(self, string_line):
        pos = string_line.find(':')
        line_number = int(string_line[18:pos])
        message = string_line[pos+1:]
        return line_number, message

    def get_script_name(self):
        s = sublime.load_settings(SETTINGS_FILE)
        return s.get('csscoco_path')

    def get_conventions_file(self):
        s = sublime.load_settings(SETTINGS_FILE)
        return s.get('conventions_file')

    def save_to_temp_file(self):
        buffer_text = self.view.substr(sublime.Region(0, self.view.size()))
        temp_file_path = ''.join([PLUGIN_FOLDER, '/', '.__temp__'])
        f = codecs.open(temp_file_path, mode='w', encoding='utf-8')
        f.write(buffer_text)
        f.close()
        return temp_file_path

    def get_hints(self, violations):
        hints = []
        for line_number in violations:
            for message in violations[line_number]:
                hint = self.view.text_point(int(line_number) - 1, 0)
                hint_line = self.view.line(hint)
                hints.append(hint_line)
        return hints


class CsscocoClearCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        Utils.clear_regions(self.view)
        Utils.clear_status(self.view)
        Storage.clear(self.view.file_name())


class CsscocoSettingsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        w = self.view.window()
        w.open_file(PLUGIN_FOLDER + '/' + SETTINGS_FILE)


class Storage(object):
    _files_to_result = {}

    @classmethod
    def store(cls, file_name, result):
        cls._files_to_result[file_name] = result
        
    @classmethod
    def clear(cls, file_name):
        cls._files_to_result.pop(file_name)

    @classmethod
    def contains(cls, file_name):
        return file_name in cls._files_to_result

    @classmethod
    def has_violations(cls, file_name):
        return cls._files_to_result[file_name].has_violations()

    @classmethod
    def get_violations(cls, file_name):
        return cls._files_to_result[file_name].data

    @staticmethod
    def is_invalid_css(cls, file_name):
        if filename in cls._files_to_result:
            return cls._files_to_result[file_name].is_invalid_css()
        return False


class CocoResult(object):
    def __init__(self, status, data):
        self.status = status
        self.data = data

    @classmethod
    def create_invalid_css_result(cls):
        return CocoResult('invalid', [])

    @classmethod
    def create_coco_errors_result(cls, data):
        return CocoResult('errors', data)

    @classmethod
    def create_violations_result(cls, data):
        return CocoResult('violations', data)

    def is_invalid_css(self):
        return self.status == 'invalid'

    def has_violations(self):
        return self.status == 'violations' and self.data


class SelectionListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        file_name = view.file_name()
        if not self.should_update_status(file_name):
            return
        
        (row,col) = view.rowcol(view.sel()[0].begin())
        line_number = row + 1
        line_to_violation = Storage.get_violations(file_name)
        if line_number not in line_to_violation:
            Utils.clear_status(view)
            return
        
        Utils.set_status(view, ''.join(line_to_violation[line_number]))

    def should_update_status(self, file_path):
        return file_path and Storage.contains(file_path) and Storage.has_violations(file_path)


class SaveListener(sublime_plugin.EventListener):
    def on_post_save(self, view):
        if self.should_run_on_save() and Utils.is_file_correct(view.file_name()):
            sublime.active_window().run_command("csscoco")

    def should_run_on_save(self):
        s = sublime.load_settings(SETTINGS_FILE)
        return s.get('run_on_save', False)


class Utils(object):
    @staticmethod
    def set_status(view, message):
        view.set_status('csscoco_status', message)

    @staticmethod
    def clear_status(view):
        view.erase_status('csscoco_status')

    @staticmethod
    def print_in_console(message):
        print(message)

    @staticmethod
    def draw_regions(view, regions):
        view.add_regions('csscoco_errors', regions, 
            scope='keyword',
            icon='circle',
            flags=sublime.DRAW_EMPTY | sublime.DRAW_NO_FILL )

    @staticmethod
    def clear_regions(view):
        view.erase_regions('csscoco_errors')
        
    @staticmethod
    def is_file_correct(filepath):
        return filepath and filepath.endswith('.css')
