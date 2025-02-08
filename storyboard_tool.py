from functools import partial
from krita import *
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDockWidget, QTextEdit, QMessageBox, QShortcut
from PyQt5.QtWidgets import (
    QPushButton,
    QStatusBar,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QWidget,
)
from PyQt5.QtCore import QUuid

from dataclasses import dataclass, field
import json
from pathlib import Path
import os

KI = Krita.instance()

def get_active_document_path() -> str | None:
    active_document = KI.activeDocument()
    if active_document is not None and (file_path := active_document.fileName()):
        return file_path        
    else:
        raise_error("There is no active document or the document has not been saved yet")
        return None


@dataclass
class Scene:
    node: Node
    is_ignored: bool = field(default=False)
    text: str = field(default="")
    character_name: str = field(default="")
    character_tag: str = field(default="")

    def __init__(self, node: Node):
        self.node = node

    def __copy__(self):
        scene_copy = Scene(self.node.duplicate())
        scene_copy.is_ignored = self.is_ignored
        scene_copy.text = self.text
        scene_copy.character_name = self.character_name
        scene_copy.character_tag = self.character_tag
        return scene_copy

    def to_dict(self):
        return {
            "node": self.node.uniqueId().toString(),
            "is_ignored": self.is_ignored,
            "text": self.text,
            "character_name": self.character_name,
            "character_tag": self.character_tag
        }
        

    @classmethod
    def from_dict(cls, data):
        return cls(
            node = KI.activeDocument().nodeByUniqueID(QUuid(data["node"]))
        ).update_from_dict(data)


    def update_from_dict(self, data):
        if self.node is None:
            return None
        self.is_ignored = data["is_ignored"]
        self.text = data["text"]
        self.character_name = data["character_name"]
        self.character_tag = data["character_tag"]
        return self


class SceneManager:
    def __init__(self):
        self.filename: str = str(Path(get_active_document_path()).with_suffix(".json"))
        self.scenes: [Scene] = [] 
        self.load()
        self.clipboard: Scene = None


    def load(self):
        try:
            with open(self.filename, "r") as file:
                scene_manager_dict = json.load(file)
                self.scenes = [scene for scene in (Scene.from_dict(scene_data) for scene_data in scene_manager_dict) if scene is not None]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        
    def save(self):
        print(f"Saving json at path: {self.filename}")
        with open(self.filename, "w") as file:
            json.dump([scene.to_dict() for scene in self.scenes], file, indent=4)
        KI.activeDocument().save()


    def is_root(self, node) -> bool:
        return node.uniqueId() == KI.activeDocument().rootNode().uniqueId()


    def is_scene(self, node) -> bool:
        return any(node.uniqueId() == scene.node.uniqueId() for scene in self.scenes)


    def get_scene(self, node) -> Scene:
        if node is None or self.is_root(node):
            return None
        elif self.is_scene(node):
            scene = next((scene for scene in self.scenes if scene.node.uniqueId() == node.uniqueId()), None)
            return scene
        else:
            return self.get_scene(node.parentNode())


    def get_all_scenes_in_order(self) -> [Scene]:
        nodes = KI.activeDocument().rootNode().childNodes()
        return [self.get_scene(node) for node in nodes if self.is_scene(node)]
        
 
    def get_active_node(self) -> Node:
        active_node = KI.activeDocument().activeNode()
        return active_node

             
    def set_active_scene(self, scene_to_set_active) -> None:
        for scene in self.scenes:
            scene.node.setCollapsed(scene.node.uniqueId() != scene_to_set_active.node.uniqueId())
        KI.activeDocument().setActiveNode(scene_to_set_active.node)


    def get_next_active_scene(self, current_scene=None, reverse=False) -> Scene:
        if current_scene is None:
            current_scene = self.get_scene(self.get_active_node())
        all_scenes = self.get_all_scenes_in_order()
        if reverse:
            all_scenes = all_scenes[::-1]
        
        current_scene_idx = next((i for i, scene in enumerate(all_scenes) if scene.node.uniqueId() == current_scene.node.uniqueId()), -1)
        if current_scene_idx == -1:
            return None
        for scene in all_scenes[current_scene_idx + 1:]:
            if not scene.is_ignored:
                return scene
        return None
        

    def create_scene(self) -> None:
        root = KI.activeDocument().rootNode()
        node = KI.activeDocument().createNode("SNG ", "grouplayer")
        node.addChildNode(createBackgroundLayer(), None)
        node.addChildNode(createEmptyLayer(), None)
        root.addChildNode(node, self.get_active_node())
        scene = Scene(node)
        self.set_active_scene(scene)
        
        self.scenes.append(scene)
        self.save()


    def remove_scene(self, scene_to_remove=None) -> None:
        if scene_to_remove is None:
            scene_to_remove = self.get_scene(self.get_active_node())
        self.set_active_scene(self.get_next_active_scene(scene_to_remove))        
        if scene_to_remove is not None:
            self.scenes = [scene for scene in self.scenes if scene.node.uniqueId() is not scene_to_remove.node.uniqueId()]
            scene_to_remove.node.remove()
            self.save()

    
    def duplicate_scene(self, scene_to_duplicate=None) -> None:
        if scene_to_duplicate is None:
            scene_to_duplicate = self.get_scene(self.get_active_node())
        new_scene = Scene(scene_to_duplicate.node.duplicate())
        KI.activeDocument().rootNode().addChildNode(new_scene.node, self.get_scene(self.get_active_node()).node)
        self.scenes.append(new_scene)
        self.set_active_scene(new_scene)
        self.save()


    def cut_scene(self, scene_to_cut=None) -> None:
        if scene_to_cut is None:
            scene_to_cut = self.get_scene(self.get_active_node())
        print(f"cut_scene scene_to_cut is None: {scene_to_cut is None}")
        self.set_active_scene(self.get_next_active_scene(scene_to_cut))
        self.clipboard = Scene(scene_to_cut.node.duplicate())
        print(f"cut_scene self.clipboard is None: {self.clipboard is None}")
        self.remove_scene(scene_to_remove=scene_to_cut)
        print(f"cut_scene self.clipboard after removal is None: {self.clipboard is None}")


    def paste_scene(self) -> None:
        if self.clipboard is not None:
            self.duplicate_scene(self.clipboard)
        else:
            print("Will not paste. No scene in the clipboard.")


    def change_scene_ignored(self, scene=None) -> None:
        if scene is None:
            scene = self.get_scene(self.get_active_node())
        if scene.is_ignored:
            scene.node.setName(scene.node.name()[4:]) 
        else:
            scene.node.setName(f"IGN {scene.node.name()}")
        scene.is_ignored = not scene.is_ignored
        self.save()


# key: Document path, value: SceneManager
SCENE_MANAGERS: dict[str, SceneManager] = {}       

def createBackgroundLayer():
    info = InfoObject()
    info.setProperty("color", "White")
    return KI.activeDocument().createFillLayer("Background", "color", info, Selection())


def createEmptyLayer():
    return KI.activeDocument().createNode("Paint Layer", "paintlayer")

# UI Helpers

def deleteConfirmationDialog():
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


def try_get_scene_manager() -> SceneManager | None:
    global SCENE_MANAGERS
    document_path = get_active_document_path()
    if document_path is None:
        return None
    elif Path(document_path).suffix != ".kra":
        raise_error("Active document is not a .kra file. Storyboard Tool will not work.")
        return None
    elif document_path not in SCENE_MANAGERS:
        SCENE_MANAGERS[document_path] = SceneManager()
    return SCENE_MANAGERS[document_path]
         

# UI Actions

def createScene():
    scene_manager = try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.create_scene()


def nextScene():
    scene_manager = try_get_scene_manager()
    if scene_manager is not None and (next_scene := scene_manager.get_next_active_scene()):
        scene_manager.set_active_scene(next_scene)


def prevScene():
    scene_manager = try_get_scene_manager()
    if scene_manager is not None and (next_scene := scene_manager.get_next_active_scene(reverse=True)):
        scene_manager.set_active_scene(next_scene)


def deleteScene():
    scene_manager = try_get_scene_manager()
    if scene_manager is not None and deleteConfirmationDialog():
        scene_manager.remove_scene()


def duplicateScene():
    scene_manager = try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.duplicate_scene()


def cutScene():
    scene_manager = try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.cut_scene()


def pasteScene():
    scene_manager = try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.paste_scene()


def changeSceneIgnored():
    scene_manager = try_get_scene_manager()
    if scene_manager is not None:
        scene_manager.change_scene_ignored()

def printScenes():
    global SCENE_MANAGERS
    print(SCENE_MANAGERS)
    for key, scene_manager in SCENE_MANAGERS.items():
        print(scene_manager.scenes)


class StoryboardToolWidget(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storyboard Tool")
        uiContainer = QWidget(self)
        main_layout = QVBoxLayout(uiContainer)
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()

        newSceneButton = QPushButton("New Scene")
        newSceneButton.setToolTip("Create new scene")
        row1.addWidget(newSceneButton)
        newSceneButton.released.connect(partial(createScene))

        nextSceneButton = QPushButton("Next Scene")
        nextSceneButton.setToolTip("Go to next scene")
        row1.addWidget(nextSceneButton)
        nextSceneButton.released.connect(partial(nextScene))

        prevSceneButton = QPushButton("Previous Scene")
        prevSceneButton.setToolTip("Go to previous scene")
        row1.addWidget(prevSceneButton)
        prevSceneButton.released.connect(partial(prevScene))

        deleteSceneButton = QPushButton("Delete Scene")
        deleteSceneButton.setToolTip("Delete selected scene")
        row1.addWidget(deleteSceneButton)
        deleteSceneButton.released.connect(partial(deleteScene))

        duplicateSceneButton = QPushButton("Duplicate Scene")
        duplicateSceneButton.setToolTip("Duplicate selected scene")
        row1.addWidget(duplicateSceneButton)
        duplicateSceneButton.released.connect(partial(duplicateScene))

        cutSceneButton = QPushButton("Cut Scene")
        cutSceneButton.setToolTip("Cut selected scene")
        row1.addWidget(cutSceneButton)
        cutSceneButton.released.connect(partial(cutScene))

        pasteSceneButton = QPushButton("Paste Scene")
        pasteSceneButton.setToolTip("Paste scene from clipboard")
        row1.addWidget(pasteSceneButton)
        pasteSceneButton.released.connect(partial(pasteScene))

        changeSceneIgnoredButton = QPushButton("Mark/Unmark Ignored")
        changeSceneIgnoredButton.setToolTip("Marks or unmarks scene as ignored")
        row1.addWidget(changeSceneIgnoredButton)
        changeSceneIgnoredButton.released.connect(partial(changeSceneIgnored))

        debugButton = QPushButton("[DEBUG] Print Scenes]")
        debugButton.setToolTip("Debug")
        row1.addWidget(debugButton)
        debugButton.released.connect(partial(printScenes))

        print("Storyboard Tool initialized")

        main_layout.addLayout(row1)
        main_layout.addLayout(row2)

        uiContainer.setLayout(main_layout)
        self.setWidget(uiContainer)

    def canvasChanged(self, canvas):
        pass


class StoryboardToolExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)


    def setup(self):
        docker = DockWidgetFactory(
        "pykrita_storyboard_tool", DockWidgetFactoryBase.DockRight, StoryboardToolWidget)
        KI.addDockWidgetFactory(docker)


    def createActions(self, window):
        newSceneAction = window.createAction(
                "new_scene",
                str(i18n("New Scene")))
        newSceneAction.triggered.connect(createScene)

        nextSceneAction = window.createAction(
                "next_scene",
                str(i18n("Next Scene")))
        nextSceneAction.triggered.connect(nextScene)

        prevSceneAction = window.createAction(
                "prev_scene",
                str(i18n("Previous Scene")))
        prevSceneAction.triggered.connect(prevScene)

        deleteSceneAction = window.createAction(
                "delete_scene",
                str(i18n("Delete Scene")))
        deleteSceneAction.triggered.connect(deleteScene)

        duplicateSceneAction = window.createAction(
                "duplicate_scene",
                str(i18n("Duplicate Scene")))
        duplicateSceneAction.triggered.connect(duplicateScene)

        cutSceneAction = window.createAction(
                "cut_scene",
                str(i18n("Cut Scene")))
        cutSceneAction.triggered.connect(cutScene)

        pasteSceneAction = window.createAction(
                "paste_scene",
                str(i18n("Paste Scene")))
        pasteSceneAction.triggered.connect(pasteScene)

        changeSceneIgnoredAction = window.createAction(
                "ignore_scene",
                str(i18n("Ignore/Unignore Scene")))
        changeSceneIgnoredAction.triggered.connect(changeSceneIgnored)

