from krita import *
from PyQt5.QtCore import pyqtSignal, QObject, QUuid

from dataclasses import dataclass, field
import json
from pathlib import Path

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

    def __init__(self, node: Node):
        self.node = node

    def __copy__(self):
        scene_copy = Scene(self.node.duplicate())
        scene_copy.is_ignored = self.is_ignored
        scene_copy.text = self.text
        scene_copy.character_name = self.character_name
        return scene_copy

    def to_dict(self):
        return {
            "node": self.node.uniqueId().toString(),
            "is_ignored": self.is_ignored,
            "text": self.text,
            "character_name": self.character_name,
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
        return self


class SceneManager(QObject):
    character_name_updated = pyqtSignal(str)
    text_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
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

        
    def save(self, save_document=False):
        print(f"Saving json at path: {self.filename}")
        with open(self.filename, "w") as file:
            json.dump([scene.to_dict() for scene in self.scenes], file, indent=4)
        if save_document:
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
        self.character_name_updated.emit(scene_to_set_active.character_name)
        self.text_updated.emit(scene_to_set_active.text) 


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
        node.addChildNode(self._create_background_layer(), None)
        node.addChildNode(self._create_empty_layer(), None)
        root.addChildNode(node, self.get_active_node())
        scene = Scene(node)
        self.set_active_scene(scene)
        
        self.scenes.append(scene)


    def remove_scene(self, scene_to_remove=None) -> None:
        if scene_to_remove is None:
            scene_to_remove = self.get_scene(self.get_active_node())
        self.set_active_scene(self.get_next_active_scene(scene_to_remove))        
        if scene_to_remove is not None:
            self.scenes = [scene for scene in self.scenes if scene.node.uniqueId() is not scene_to_remove.node.uniqueId()]
            scene_to_remove.node.remove()

    
    def duplicate_scene(self, scene_to_duplicate=None) -> None:
        if scene_to_duplicate is None:
            scene_to_duplicate = self.get_scene(self.get_active_node())
        new_scene = Scene(scene_to_duplicate.node.duplicate())
        KI.activeDocument().rootNode().addChildNode(new_scene.node, self.get_scene(self.get_active_node()).node)
        self.scenes.append(new_scene)
        self.set_active_scene(new_scene)


    def cut_scene(self, scene_to_cut=None) -> None:
        if scene_to_cut is None:
            scene_to_cut = self.get_scene(self.get_active_node())
        self.set_active_scene(self.get_next_active_scene(scene_to_cut))
        self.clipboard = Scene(scene_to_cut.node.duplicate())
        self.remove_scene(scene_to_remove=scene_to_cut)


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


    def change_character_name(self, text) -> None:
        current_scene = self.get_scene(self.get_active_node())
        if current_scene is not None:
            current_scene.character_name = text


    def change_text(self, text) -> None:
        current_scene = self.get_scene(self.get_active_node())
        if current_scene is not None:
            current_scene.text = text


    def reemit_signals(self) -> None:
        current_scene = self.get_scene(self.get_active_node())
        if current_scene is not None:
            self.character_name_updated.emit(current_scene.character_name)
            self.text_updated.emit(current_scene.text)

    def _create_background_layer():
        info = InfoObject()
        info.setProperty("color", "White")
        return KI.activeDocument().createFillLayer("Background", "color", info, Selection())


    def _create_empty_layer():
         return KI.activeDocument().createNode("Paint Layer", "paintlayer")
    

class SceneManagerProvider():
    def __init__(self):
        # key: Document path, value: SceneManager
        self.scene_managers: dict[str, SceneManager] = {}
        self.widgets_to_connect: dict[QWidget, SceneManager] = {}

        self.set_character_name: Callable = None
        self.set_text: Callable = None


    def create_scene_manager(self) -> SceneManager | None:
        if self.set_character_name is None or self.set_text is None:
            raise_error("Cannot initialize Scene Manager, widget does not exist")
            return None
        scene_manager = SceneManager()
        scene_manager.character_name_updated.connect(self.set_character_name)
        scene_manager.text_updated.connect(self.set_text)
        return scene_manager


    def try_get_scene_manager(self) -> SceneManager | None:
        document_path = get_active_document_path()
        if document_path is None:
            return None
        elif Path(document_path).suffix != ".kra":
            raise_error("Active document is not a .kra file. Storyboard Tool will not work.")
            return None
        elif document_path not in self.scene_managers:
            self.scene_managers[document_path] = self.create_scene_manager()
        return self.scene_managers[document_path]
