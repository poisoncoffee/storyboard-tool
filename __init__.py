from .storyboard_tool import *
from krita import Krita

registerDocker()
Krita.instance().addExtension(StoryboardToolExtension(Krita.instance()))