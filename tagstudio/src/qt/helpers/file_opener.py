# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import os
import subprocess
import shutil
import sys
import traceback

from PySide6.QtWidgets import QLabel

ERROR = f'[ERROR]'
WARNING = f'[WARNING]'
INFO = f'[INFO]'

logging.basicConfig(format="%(message)s", level=logging.INFO)


def open_file(path: str, file_manager: bool = False):
	logging.info(f'Opening file: {path}')
	if not os.path.exists(path):
		logging.error(f'File not found: {path}')
		return
	try:
		if sys.platform == "win32":
			normpath = os.path.normpath(path)
			if file_manager:
				command_name = "explorer"
				command_args = [f"/select,{normpath}"]
			else:
				command_name = "start"
				# first parameter is for title, NOT filepath
				command_args = ["", normpath]
			subprocess.Popen([command_name] + command_args, shell=True, close_fds=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_BREAKAWAY_FROM_JOB)
		else:
			if sys.platform == "darwin":
				command_name = "open"
				command_args = [path]
				if file_manager:
					# will reveal in Finder
					command_args.append("-R")
			else:
				if file_manager:
					command_name = "dbus-send"
					# might not be guaranteed to launch default?
					command_args = ["--session", "--dest=org.freedesktop.FileManager1", "--type=method_call",
									"/org/freedesktop/FileManager1", "org.freedesktop.FileManager1.ShowItems",
									f"array:string:file://{path}", "string:"]
				else:
					command_name = "xdg-open"
					command_args = [path]
			command = shutil.which(command_name)
			if command is not None:
				subprocess.Popen([command] + command_args, close_fds=True)
			else:
				logging.info(f"Could not find {command_name} on system PATH")
	except:
		traceback.print_exc()


class FileOpenerHelper:
	def __init__(self, filepath:str):
		self.filepath = filepath

	def set_filepath(self, filepath:str):
		self.filepath = filepath

	def open_file(self):
		open_file(self.filepath)

	def open_explorer(self):
		open_file(self.filepath, True)


class FileOpenerLabel(QLabel):
	def __init__(self, text, parent=None):
		super().__init__(text, parent)

	def setFilePath(self, filepath):
		self.filepath = filepath

	def mousePressEvent(self, event):
		super().mousePressEvent(event)
		opener = FileOpenerHelper(self.filepath)
		opener.open_explorer()
