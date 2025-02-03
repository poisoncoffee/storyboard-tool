from functools import partial
from krita import *
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
CLIPBOARD_SCENE = None

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


def duplicateScene():
    currentScene = getScene(KI.activeDocument().activeNode())
    if newScene := currentScene.duplicate():
        KI.activeDocument().rootNode().addChildNode(newScene, getScene(currentScene))
        setActiveScene(newScene)


def cutScene():
    currentScene = getScene(KI.activeDocument().activeNode())
    nextScene() # Will select next scene
    if currentScene is not None:
        global CLIPBOARD_SCENE
        CLIPBOARD_SCENE = currentScene.duplicate()
        currentScene.remove()


def pasteScene():
    global CLIPBOARD_SCENE
    if CLIPBOARD_SCENE is not None:
        if newScene := CLIPBOARD_SCENE.duplicate():
            KI.activeDocument().rootNode().addChildNode(newScene, getScene(KI.activeDocument().activeNode()))
            setActiveScene(newScene)
        


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
        deleteSceneButton.setToolTip("Delete selected scene")
        hboxlayout.addWidget(deleteSceneButton)
        deleteSceneButton.released.connect(partial(deleteScene))

        duplicateSceneButton = QPushButton("Duplicate Scene")
        duplicateSceneButton.setToolTip("Duplicate selected scene")
        hboxlayout.addWidget(duplicateSceneButton)
        duplicateSceneButton.released.connect(partial(duplicateScene))

        cutSceneButton = QPushButton("Cut Scene")
        cutSceneButton.setToolTip("Cut selected scene")
        hboxlayout.addWidget(cutSceneButton)
        cutSceneButton.released.connect(partial(cutScene))

        pasteSceneButton = QPushButton("Paste Scene")
        pasteSceneButton.setToolTip("Paste scene from clipboard")
        hboxlayout.addWidget(pasteSceneButton)
        pasteSceneButton.released.connect(partial(pasteScene))

        uiContainer.setLayout(hboxlayout)
        self.setWidget(uiContainer)

    def canvasChanged(self, canvas):
        pass


class StoryboardToolExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

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


def registerDocker():
    docker = DockWidgetFactory(
        "pykrita_storyboard_tool", DockWidgetFactoryBase.DockRight, StoryboardToolWidget
    )
    KI.addDockWidgetFactory(docker)