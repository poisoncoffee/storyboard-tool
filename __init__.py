from .storyboard_tool import StoryboardToolExtension
from krita import Krita

Krita.instance().addExtension(StoryboardToolExtension(Krita.instance()))