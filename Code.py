import os
import shutil
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import matplotlib.pyplot as plt

class FileOrganizerThread(QThread):
    progress_updated = pyqtSignal(int, int)  # Signal to update progress (current, total)
    category_counts_updated = pyqtSignal(dict)  # Signal to update category counts

    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.category_counts = {
            'Documents': 0,
            'Images': 0,
            'Audio': 0,
            'Video': 0,
            'Archives': 0,
            'Executables': 0,
            'Misc': 0,
            'Folders': 0
        }

    def run(self):
        try:
            self.group_files_by_type(self.directory)
            self.progress_updated.emit(100, 100)  # Finished
        except Exception as e:
            print(f"Error: {str(e)}")
            self.progress_updated.emit(0, 100)  # Error

    def group_files_by_type(self, directory):
        # Change to the specified directory
        os.chdir(directory)

        # Define categories and their corresponding extensions
        categories = {
            'Documents': ['pdf', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx'],
            'Images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg'],
            'Audio': ['mp3', 'wav', 'aac', 'flac', 'ogg', 'wma'],
            'Video': ['mp4', 'mkv', 'flv', 'avi', 'mov', 'wmv'],
            'Archives': ['rar', 'zip', 'tar', 'gz', '7z'],
            'Executables': ['exe', 'bat', 'sh', 'bin', 'msi'],
            'Misc': []  # Misc will catch all files without a specified category
        }

        # Get a list of all files in the directory
        files = [f for f in os.listdir() if os.path.isfile(f)]
        total_files = len(files)

        # Iterate over the files and group them by type
        current_file = 0
        for file in files:
            # Extract the file extension
            file_extension = os.path.splitext(file)[1][1:]  # Remove the dot from the extension

            # Determine the category
            moved = False
            for category, extensions in categories.items():
                if file_extension in extensions:
                    # Create a directory for the category if it doesn't exist
                    if not os.path.exists(category):
                        os.makedirs(category)
                    # Move the file to the corresponding directory
                    shutil.move(file, os.path.join(category, file))
                    moved = True
                    self.category_counts[category] += 1
                    break

            # If file does not match any category, move it to Misc
            if not moved:
                if not os.path.exists('Misc'):
                    os.makedirs('Misc')
                shutil.move(file, os.path.join('Misc', file))
                self.category_counts['Misc'] += 1

            current_file += 1
            self.progress_updated.emit(current_file, total_files)
            self.category_counts_updated.emit(self.category_counts)

        # Group folders separately
        folders = [d for d in os.listdir() if os.path.isdir(d) and d not in categories.keys() and d != 'Misc']
        if folders:
            if not os.path.exists('Folders'):
                os.makedirs('Folders')
            for folder in folders:
                # Avoid moving already grouped directories
                if folder not in categories and folder != 'Folders' and folder != 'Misc':
                    shutil.move(folder, os.path.join('Folders', folder))
                    self.category_counts['Folders'] += 1
                    self.category_counts_updated.emit(self.category_counts)


class FileOrganizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('File Organizer')
        self.setGeometry(100, 100, 600, 400)

        self.folder_path_label = QLabel('Select a directory to organize:')
        self.browse_button = QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.browse_button_clicked)

        self.organize_button = QPushButton('Organize Files', self)
        self.organize_button.clicked.connect(self.organize_button_clicked)

        self.progress_label = QLabel('Progress:')
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)

        self.categories_label = QLabel('Category Counts:')
        self.categories_info = QLabel('')
        
        layout = QVBoxLayout()
        layout.addWidget(self.folder_path_label)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.organize_button)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.categories_label)
        layout.addWidget(self.categories_info)

        self.setLayout(layout)

        self.organizer_thread = None

    def browse_button_clicked(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if directory:
            self.directory_path = directory
            self.folder_path_label.setText(f'Selected Directory: {self.directory_path}')

    def organize_button_clicked(self):
        if hasattr(self, 'directory_path'):
            self.organize_button.setEnabled(False)
            self.progress_bar.setValue(0)
            self.organizer_thread = FileOrganizerThread(self.directory_path)
            self.organizer_thread.progress_updated.connect(self.update_progress)
            self.organizer_thread.category_counts_updated.connect(self.update_category_info)
            self.organizer_thread.start()
        else:
            QMessageBox.warning(self, 'Warning', 'Please select a directory first.')

    def update_progress(self, current, total):
        progress = int(current / total * 100)
        self.progress_bar.setValue(progress)
        if progress == 100:
            QMessageBox.information(self, 'Success', 'Files and folders have been grouped by their type.')
            self.organize_button.setEnabled(True)

    def update_category_info(self, category_counts):
        info_text = ''
        for category, count in category_counts.items():
            info_text += f'{category}: {count}\n'
        
        self.categories_info.setText(info_text.strip())

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Optional: Set the style to Fusion for a modern look
    window = FileOrganizerApp()
    window.show()
    sys.exit(app.exec_())
