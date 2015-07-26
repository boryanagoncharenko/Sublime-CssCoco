import os
import subprocess
import sublime, sublime_plugin


class CsscocoCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		filepath = self.view.file_name()
		if not filepath:
			return

		if not self.is_css_file(filepath):
			return

		self.view.erase_regions('csscoco_errors')

		script_name = '/Library/Frameworks/Python.framework/Versions/3.4/bin/csscoco'
		coco_file = '/Users/bore/Projects/ThesisCode/Source/samples/idiomatic.coco'
		# css_file = '/Users/bore/Projects/ThesisCode/Source/samples/buffer.coco'

		cmd = [script_name, filepath, coco_file]
		out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False, env=os.environ)

		hints = []
		quick_pane_items = []
		Violations.store(out, filepath)
		for line_number in Violations.line_to_violations:
			for message in Violations.line_to_violations[line_number]:
				hint = self.view.text_point(int(line_number) - 1, 0)
				hint_line = self.view.line(hint)
				hints.append(hint_line)
				# quick_pane_items.append(''.join(['Violation on line ', str(line_number), ': ', message]))
			
		# print('bla di bla di bla')
		# sublime.status_message('bla bla bla')

		# self.view.window().show_quick_panel(quick_pane_items, self.on_quick_pane_selection)

		self.view.add_regions('csscoco_errors', hints, 
			scope='keyword',
            icon='circle',
            flags=sublime.DRAW_EMPTY | 
            sublime.DRAW_NO_FILL )

	def on_quick_pane_selection(self, index):
		pass
		

	def is_css_file(self, filepath):
		if len(filepath) < 4:
			return False
		return filepath[-4:] == '.css'




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


