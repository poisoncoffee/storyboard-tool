from .storyboard_tool_scene import SceneManagerProvider
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

# UI Helpers

def delete_confirmation_dialog():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText("Are you sure you want to delete the scene?")
    msg.setWindowTitle("Delete scene")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    
    if response := msg.exec_():
        return response == QMessageBox.Yes


def raise_error(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle("Error")
    msg.setStandardButtons(QMessageBox.Ok)

    msg.exec_()
         

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
    scene_manager = SCENE_MANAGER_PROVIDER.try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.reemit_signals()


class StoryboardToolWidget(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storyboard Tool")
        ui_container = QWidget(self)
        main_layout = QHBoxLayout(ui_container)     
        col_1 = QVBoxLayout()
        col_2 = QVBoxLayout()

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

        next_scene_button = QPushButton("Next Scene")
        next_scene_button.setToolTip("Go to next scene")
        col_2.addWidget(next_scene_button)
        next_scene_button.released.connect(partial(next_scene))

        prev_scene_button = QPushButton("Previous Scene")
        prev_scene_button.setToolTip("Go to previous scene")
        col_2.addWidget(prev_scene_button)
        prev_scene_button.released.connect(partial(prev_scene))

        delete_scene_button = QPushButton("Delete Scene")
        delete_scene_button.setToolTip("Delete selected scene")
        col_2.addWidget(delete_scene_button)
        delete_scene_button.released.connect(partial(delete_scene))

        duplicate_scene_button = QPushButton("Duplicate Scene")
        duplicate_scene_button.setToolTip("Duplicate selected scene")
        col_2.addWidget(duplicate_scene_button)
        duplicate_scene_button.released.connect(partial(duplicate_scene))

        cut_scene_button = QPushButton("Cut Scene")
        cut_scene_button.setToolTip("Cut selected scene")
        col_2.addWidget(cut_scene_button)
        cut_scene_button.released.connect(partial(cut_scene))

        paste_scene_button = QPushButton("Paste Scene")
        paste_scene_button.setToolTip("Paste scene from clipboard")
        col_2.addWidget(paste_scene_button)
        paste_scene_button.released.connect(partial(paste_scene))

        change_scene_ignored_button = QPushButton("Mark/Unmark Ignored")
        change_scene_ignored_button.setToolTip("Marks or unmarks scene as ignored")
        col_2.addWidget(change_scene_ignored_button)
        change_scene_ignored_button.released.connect(partial(change_scene_ignored))

        save_document_button = QPushButton("Save")
        save_document_button.setToolTip("Saves storyboard document and .kra document")
        col_2.addWidget(save_document_button)
        save_document_button.released.connect(partial(save_document))

        refresh_data_button = QPushButton("Refresh")
        refresh_data_button.setToolTip("Manually refreshes widget with scene data")
        col_2.addWidget(refresh_data_button)
        refresh_data_button.released.connect(partial(refresh_scene_data))

        print("Storyboard Tool initialized")

        main_layout.addLayout(col_1)
        main_layout.addLayout(col_2)

        ui_container.setLayout(main_layout)
        self.setWidget(ui_container)

    def canvasChanged(self, canvas):
        pass


class StoryboardToolExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)


    def setup(self):
        docker = DockWidgetFactory(
        "pykrita_storyboard_tool", DockWidgetFactoryBase.DockRight, StoryboardToolWidget)
        Krita.instance().addDockWidgetFactory(docker)


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

