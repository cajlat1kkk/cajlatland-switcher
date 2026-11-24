"""Read the focused editable selection of one application for a manual conversion."""
import sys
import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi, GLib


def selected_text(pid):
    desktop = Atspi.get_desktop(0)
    apps = (desktop.get_child_at_index(i) for i in range(desktop.get_child_count()))
    app = next((item for item in apps if item and item.get_process_id() == pid), None)
    if not app:
        return ""
    stack = [app]
    while stack:
        node = stack.pop()
        state = node.get_state_set()
        if node.get_role() == Atspi.Role.PASSWORD_TEXT:
            continue
        if state.contains(Atspi.StateType.FOCUSED) and state.contains(Atspi.StateType.EDITABLE) and node.is_text():
            if node.get_n_selections() == 1:
                selection = Atspi.Text.get_selection(node, 0)
                a,b = sorted((selection.start_offset, selection.end_offset))
                if 0 < b-a <= 2000:
                    return Atspi.Text.get_text(node, a, b)
        for index in reversed(range(node.get_child_count())):
            child = node.get_child_at_index(index)
            if child:
                stack.append(child)
    return ""


if __name__ == "__main__":
    try:
        sys.stdout.write(selected_text(int(sys.argv[1])))
    except (GLib.Error, RuntimeError):
        pass
