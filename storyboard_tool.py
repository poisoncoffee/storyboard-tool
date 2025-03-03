from .storyboard_tool_scene import SceneManagerProvider, ExportConfig
from krita import *

from PyQt5.QtWidgets import QTextEdit, QMessageBox
from PyQt5.QtWidgets import (
    QPushButton,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from functools import partial


SCENE_MANAGER_PROVIDER = SceneManagerProvider()
EXPORT_CONFIG = ExportConfig()

# UI Helpers

def delete_confirmation_dialog():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText("Are you sure you want to delete the scene?")
    msg.setWindowTitle("Delete scene")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    
    if response := msg.exec_():
        return response == QMessageBox.Yes
         

# UI Actions

def create_scene():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.create_scene()


def next_scene():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None and (next_scene := scene_manager.get_next_active_scene()):
        scene_manager.set_active_scene(next_scene)


def prev_scene():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None and (next_scene := scene_manager.get_next_active_scene(reverse=True)):
        scene_manager.set_active_scene(next_scene)


def delete_scene():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None and delete_confirmation_dialog():
        scene_manager.remove_scene()


def duplicate_scene():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.duplicate_scene()


def cut_scene():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.cut_scene()


def paste_scene():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.paste_scene()


def change_scene_ignored():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.change_scene_ignored()


def save_document():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.save(save_document=True)


def update_character_name(text):
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.change_character_name(text)


def update_text(text):
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.change_text(text)


def set_text_on_widget(widget, text):
    widget.blockSignals(True)
    widget.setText(text)
    widget.blockSignals(False)


def print_scenes():
    global SCENE_MANAGER_PROVIDER
    for key, scene_manager in SCENE_MANAGER_PROVIDER.scene_managers.items():
        print(scene_manager.scenes)


def refresh_scene_data():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.reemit_signals()


def toggle_export_options():
    next((dock.show() for dock in Krita.instance().dockers() if dock.windowTitle() == "Storyboard Export Options"), None)


def update_scale(value):
    if value:
        global EXPORT_CONFIG
        EXPORT_CONFIG.scale = float(int(value) / 100)


def update_chapter_name(value):
    global EXPORT_CONFIG
    EXPORT_CONFIG.chapter_name = value


def update_delimiter(value):
    global EXPORT_CONFIG
    EXPORT_CONFIG.delimiter = value


def update_extension(value):
    global EXPORT_CONFIG
    EXPORT_CONFIG.extension = value


def export():
    global SCENE_MANAGER_PROVIDER
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        global EXPORT_CONFIG
        scene_manager.export(EXPORT_CONFIG)


class StoryboardExportOptionsWidget(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storyboard Export Options")
        ui_container = QWidget(self)
        main_layout = QVBoxLayout(ui_container)

        form_layout = QFormLayout()
        global EXPORT_CONFIG

        chapter_label = QLabel("Chapter name")
        chapter_name_input = QLineEdit()
        chapter_name_input.setText(EXPORT_CONFIG.chapter_name)
        chapter_name_input.textChanged.connect(update_chapter_name)

        scale_label = QLabel("Image scale [%]")
        scale_input = QLineEdit()
        scale_input.setValidator(QIntValidator())
        scale_input.setText(str(int(EXPORT_CONFIG.scale * 100)))
        scale_input.textChanged.connect(update_scale)

        delimiter_label = QLabel("Default separator")
        delimiter_input = QLineEdit()
        delimiter_input.setText(EXPORT_CONFIG.delimiter)
        delimiter_input.textChanged.connect(update_delimiter)

        extension_label = QLabel("File format")
        extension_dropdown = QComboBox()
        extension_dropdown.addItems(["jpg", "png"])
        extension_dropdown.setCurrentText(EXPORT_CONFIG.extension)
        extension_dropdown.currentTextChanged.connect(update_extension)

        form_layout.addRow(scale_label, scale_input)
        form_layout.addRow(chapter_label, chapter_name_input)
        form_layout.addRow(delimiter_label, delimiter_input)
        form_layout.addRow(extension_label, extension_dropdown)

        main_layout.addLayout(form_layout)

        export_all_button = QPushButton("Export All")
        export_all_button.setToolTip("Export All Layers")
        main_layout.addWidget(export_all_button)
        export_all_button.released.connect(partial(export))

        export_selected_button = QPushButton("Export Selected Layers")
        export_selected_button.setToolTip("Export Selected Layers")
        main_layout.addWidget(export_selected_button)
        export_selected_button.released.connect(partial(export))

        export_selected_and_newer = QPushButton("Export Selected and newer")
        export_selected_and_newer.setToolTip("Export Selected Layer and newer")
        main_layout.addWidget(export_selected_and_newer)
        export_selected_and_newer.released.connect(partial(export))

        ui_container.setLayout(main_layout)
        
        self.setWidget(ui_container)


    def canvasChanged(self, canvas):
        pass


class StoryboardToolWidget(DockWidget):
    def getNewSeparator(self) -> QFrame:
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator
        

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storyboard Tool")
        ui_container = QWidget(self)
        main_layout = QHBoxLayout(ui_container)        

        col_1 = QVBoxLayout()
        col_2 = QVBoxLayout()
        col_3 = QVBoxLayout()

        col_1_widget = QWidget()
        col_1_widget.setLayout(col_1)

        col_2_widget = QWidget()
        col_2_widget.setLayout(col_2)

        col_3_widget = QWidget()
        col_3_widget.setLayout(col_3)

        # Column 1
        character_name_edit = QLineEdit()
        text_edit = QTextEdit()
        col_1.addWidget(character_name_edit)
        col_1.addWidget(text_edit)

        character_name_edit.textChanged.connect(lambda text: update_character_name(text))
        text_edit.textChanged.connect(lambda: update_text(text_edit.toPlainText()))

        global SCENE_MANAGER_PROVIDER
        SCENE_MANAGER_PROVIDER.set_character_name = lambda text: set_text_on_widget(character_name_edit, text)
        SCENE_MANAGER_PROVIDER.set_text = lambda text: set_text_on_widget(text_edit, text)

        # Column 2
        new_scene_button = QPushButton("New Scene")
        new_scene_button.setToolTip("Create new scene")
        col_2.addWidget(new_scene_button)
        new_scene_button.released.connect(partial(create_scene))

        delete_scene_button = QPushButton("Delete Scene")
        delete_scene_button.setToolTip("Delete selected scene")
        col_2.addWidget(delete_scene_button)
        delete_scene_button.released.connect(partial(delete_scene))

        col_2.addWidget(self.getNewSeparator())

        next_scene_button = QPushButton("Next Scene")
        next_scene_button.setToolTip("Go to next scene")
        col_2.addWidget(next_scene_button)
        next_scene_button.released.connect(partial(next_scene))

        prev_scene_button = QPushButton("Previous Scene")
        prev_scene_button.setToolTip("Go to previous scene")
        col_2.addWidget(prev_scene_button)
        prev_scene_button.released.connect(partial(prev_scene))

        # Column 3        
        duplicate_scene_button = QPushButton("Duplicate Scene")
        duplicate_scene_button.setToolTip("Duplicate selected scene")
        col_3.addWidget(duplicate_scene_button)
        duplicate_scene_button.released.connect(partial(duplicate_scene))

        cut_scene_button = QPushButton("Cut Scene")
        cut_scene_button.setToolTip("Cut selected scene")
        col_3.addWidget(cut_scene_button)
        cut_scene_button.released.connect(partial(cut_scene))

        paste_scene_button = QPushButton("Paste Scene")
        paste_scene_button.setToolTip("Paste scene from clipboard")
        col_3.addWidget(paste_scene_button)
        paste_scene_button.released.connect(partial(paste_scene))

        col_3.addWidget(self.getNewSeparator())

        change_scene_ignored_button = QPushButton("Un/mark Ignored")
        change_scene_ignored_button.setToolTip("Marks or unmarks scene as ignored")
        col_3.addWidget(change_scene_ignored_button)
        change_scene_ignored_button.released.connect(partial(change_scene_ignored))

        refresh_data_button = QPushButton("Refresh")
        refresh_data_button.setToolTip("Manually refreshes widget with scene data")
        col_3.addWidget(refresh_data_button)
        refresh_data_button.released.connect(partial(refresh_scene_data))

        col_3.addWidget(self.getNewSeparator())

        save_document_button = QPushButton("Save")
        save_document_button.setToolTip("Saves storyboard document and .kra document")
        col_3.addWidget(save_document_button)
        save_document_button.released.connect(partial(save_document))
   
        export_options_button = QPushButton("Export Options")
        export_options_button.setToolTip("Toggle export menu")
        col_3.addWidget(export_options_button)
        export_options_button.released.connect(partial(toggle_export_options))

        print("Storyboard Tool initialized")

        main_layout.addWidget(col_1_widget)
        main_layout.addWidget(col_2_widget)
        main_layout.addWidget(col_3_widget)

        ui_container.setLayout(main_layout)
        
        self.setWidget(ui_container)

    def canvasChanged(self, canvas):
        pass


class StoryboardToolExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)


    def setup(self):
        main_dock = DockWidgetFactory(
        "pykrita_storyboard_tool", DockWidgetFactoryBase.DockRight, StoryboardToolWidget)
        Krita.instance().addDockWidgetFactory(main_dock)

        export_dock = DockWidgetFactory(
        "pykrita_storyboard_export", DockWidgetFactoryBase.DockRight, StoryboardExportOptionsWidget)
        Krita.instance().addDockWidgetFactory(export_dock)


    def createActions(self, window):
        new_scene_action = window.createAction(
                "new_scene",
                str(i18n("New Scene")))
        new_scene_action.triggered.connect(create_scene)

        next_scene_action = window.createAction(
                "next_scene",
                str(i18n("Next Scene")))
        next_scene_action.triggered.connect(next_scene)

        prev_scene_action = window.createAction(
                "prev_scene",
                str(i18n("Previous Scene")))
        prev_scene_action.triggered.connect(prev_scene)

        delete_scene_action = window.createAction(
                "delete_scene",
                str(i18n("Delete Scene")))
        delete_scene_action.triggered.connect(delete_scene)

        duplicate_scene_action = window.createAction(
                "duplicate_scene",
                str(i18n("Duplicate Scene")))
        duplicate_scene_action.triggered.connect(duplicate_scene)

        cut_scene_action = window.createAction(
                "cut_scene",
                str(i18n("Cut Scene")))
        cut_scene_action.triggered.connect(cut_scene)

        paste_scene_action = window.createAction(
                "paste_scene",
                str(i18n("Paste Scene")))
        paste_scene_action.triggered.connect(paste_scene)

        change_scene_ignored_action = window.createAction(
                "ignore_scene",
                str(i18n("Ignore/Unignore Scene")))
        change_scene_ignored_action.triggered.connect(change_scene_ignored)

        save_document_action = window.createAction(
                "save_document",
                str(i18n("Save Document and Storyboard data")))
        save_document_action.triggered.connect(save_document)

        refresh_scene_action = window.createAction(
                "refresh_data",
                str(i18n("Refresh widget with Scene data")))
        refresh_scene_action.triggered.connect(refresh_scene_data)

