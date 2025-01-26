from functools import partial
from krita import (
    DockWidget, 
    DockWidgetFactory, 
    DockWidgetFactoryBase, 
    GroupLayer,
    Krita,
    InfoObject,
    Selection )
from PyQt5.QtWidgets import QDockWidget, QTextEdit
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

KI = Krita.instance()

def getAllScenes():
    nodes = KI.activeDocument().rootNode().childNodes()
    scenes = []
    for node in nodes:
        if isinstance(node, GroupLayer):
            scenes.append(node)
    return scenes

def isRoot(node):
    return node.uniqueId() == KI.activeDocument().rootNode().uniqueId()

def isScene(node):
    scenes = getAllScenes()
    for scene in scenes:
        if node.uniqueId() == scene.uniqueId():
            return True
    return False   


def getScene(node):
    if isRoot(node):
        return None
    if isScene(node):
        return node
    else:
        return getScene(node.parentNode())


def createBackgroundLayer():
    info = InfoObject()
    info.setProperty("color", "White")
    return KI.activeDocument().createFillLayer("Background", "color", info, Selection())

def createEmptyLayer():
    return KI.activeDocument().createNode("Paint Layer", "paintlayer")

def createScene():
    root = KI.activeDocument().rootNode()
    scene = KI.activeDocument().createNode("SNG ", "grouplayer")
    scene.addChildNode(createBackgroundLayer(), None)
    scene.addChildNode(createEmptyLayer(), None)
    root.addChildNode(scene, getScene(KI.activeDocument().activeNode()))

def nextScene():
    pass

def prevScene():
    pass

class StoryboardToolWidget(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storyboard Tool")
        uiContainer = QWidget(self)
        hboxlayout = QHBoxLayout()

        newSceneButton = QPushButton("New Scene")
        newSceneButton.setToolTip("Create new scene")
        hboxlayout.addWidget(newSceneButton)
        newSceneButton.released.connect(partial(createScene))

        nextSceneButton = QPushButton("Next Scene")
        nextSceneButton.setToolTip("Go to next scene")
        hboxlayout.addWidget(nextSceneButton)
        nextSceneButton.released.connect(partial(nextScene))

        prevSceneButton = QPushButton("New Scene")
        prevSceneButton.setToolTip("Go to previous scene")
        hboxlayout.addWidget(prevSceneButton)
        prevSceneButton.released.connect(partial(prevScene))

        uiContainer.setLayout(hboxlayout)
        self.setWidget(uiContainer)

    def canvasChanged(self, canvas):
        pass



def registerDocker():
    docker = DockWidgetFactory(
        "pykrita_storyboard_tool", DockWidgetFactoryBase.DockRight, StoryboardToolWidget
    )
    KI.addDockWidgetFactory(docker)