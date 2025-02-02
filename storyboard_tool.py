from functools import partial
from krita import (
    DockWidget, 
    DockWidgetFactory, 
    DockWidgetFactoryBase, 
    GroupLayer,
    Krita,
    InfoObject,
    Selection )
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
    if node is None or isRoot(node):
        return None
    elif isScene(node):
        return node
    else:
        return getScene(node.parentNode())


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
    

# Collapses all scenes except active one
def setActiveScene(activeScene):
    KI.activeDocument().setActiveNode(activeScene)
    allScenes = getAllScenes()
    for scene in allScenes:
        scene.setCollapsed(scene.uniqueId() != activeScene.uniqueId())


# UI Actions

def createScene():
    root = KI.activeDocument().rootNode()
    scene = KI.activeDocument().createNode("SNG ", "grouplayer")
    scene.addChildNode(createBackgroundLayer(), None)
    scene.addChildNode(createEmptyLayer(), None)
    root.addChildNode(scene, getScene(KI.activeDocument().activeNode()))
    setActiveScene(scene)


def nextScene():
    allScenes = getAllScenes()
    currentScene = getScene(KI.activeDocument().activeNode())
    for i in range(len(allScenes) - 1):
        if allScenes[i].uniqueId() == currentScene.uniqueId():
            setActiveScene(allScenes[i + 1])


def prevScene():
    allScenes = getAllScenes()
    currentScene = getScene(KI.activeDocument().activeNode())
    for i in range(1, len(allScenes)):
        if allScenes[i].uniqueId() == currentScene.uniqueId():           
            setActiveScene(allScenes[i - 1])


def deleteScene():
    if deleteConfirmationDialog():
        currentScene = getScene(KI.activeDocument().activeNode())
        nextScene() # Will select next scene
        if currentScene is not None:
            currentScene.remove()


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

        prevSceneButton = QPushButton("Previous Scene")
        prevSceneButton.setToolTip("Go to previous scene")
        hboxlayout.addWidget(prevSceneButton)
        prevSceneButton.released.connect(partial(prevScene))

        deleteSceneButton = QPushButton("Delete Scene")
        deleteSceneButton.setToolTip("Delete currently selected scene(s)")
        hboxlayout.addWidget(deleteSceneButton)
        deleteSceneButton.released.connect(partial(deleteScene))

        uiContainer.setLayout(hboxlayout)
        self.setWidget(uiContainer)

    def canvasChanged(self, canvas):
        pass



def registerDocker():
    docker = DockWidgetFactory(
        "pykrita_storyboard_tool", DockWidgetFactoryBase.DockRight, StoryboardToolWidget
    )
    KI.addDockWidgetFactory(docker)