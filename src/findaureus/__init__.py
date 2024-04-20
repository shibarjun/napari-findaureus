__version__ = "0.0.2"

from ._reader import napari_get_reader
from ._widget import Find_Bacteria
from napari_plugin_engine import napari_hook_implementation

def napari_experimental_provide_dock_widget():
    return Find_Bacteria

__all__ = (
    "napari_get_reader",
    "Find_Bacteria"
)
