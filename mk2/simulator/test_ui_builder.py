import unittest

from mk2.simulator.ui_builder import (
    DEFAULT_DESIGN,
    generate_firmware_project,
    generate_firmware_module,
    render_design,
    render_contact_sheet,
    validate_design,
    validate_project,
)


class RecordingFrameBuffer:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        return lambda *args: self.calls.append((name, *args))


class UIBuilderTests(unittest.TestCase):
    def test_default_design_renders_at_pump_resolution(self):
        image = render_design(DEFAULT_DESIGN)
        self.assertEqual(image.size, (240, 240))
        self.assertEqual(image.getpixel((0, 0)), (244, 247, 249))

    def test_generated_module_draws_all_supported_element_types(self):
        design = {
            "version": 1,
            "name": "All elements",
            "background": "#FFFFFF",
            "elements": [
                {"type": "Text", "x": 1, "y": 2, "w": 30, "h": 8, "text": "OK", "color": "#000000"},
                {"type": "Filled rectangle", "x": 2, "y": 3, "w": 12, "h": 8, "text": "", "color": "#FF0000"},
                {"type": "Rectangle", "x": 3, "y": 4, "w": 12, "h": 8, "text": "", "color": "#00FF00"},
                {"type": "Line", "x": 4, "y": 5, "w": 10, "h": 2, "text": "", "color": "#0000FF"},
                {"type": "Circle", "x": 5, "y": 6, "w": 10, "h": 10, "text": "", "color": "#123456"},
                {"type": "Filled circle", "x": 20, "y": 6, "w": 10, "h": 10, "text": "", "color": "#654321"},
            ],
        }
        source = generate_firmware_module(design)
        compile(source, "<generated-ui>", "exec")
        namespace = {}
        exec(source, namespace)
        framebuffer = RecordingFrameBuffer()
        namespace["draw_custom_ui"](framebuffer)
        called_methods = {call[0] for call in framebuffer.calls}
        self.assertTrue({"fill", "text", "fill_rect", "rect", "line", "pixel", "hline"} <= called_methods)
        self.assertEqual(framebuffer.calls[0], ("fill", 0xFFFF))

    def test_validation_rejects_unsupported_type(self):
        design = dict(DEFAULT_DESIGN, elements=[{"type": "Image"}])
        with self.assertRaisesRegex(ValueError, "unsupported type"):
            validate_design(design)

    def test_firmware_export_requires_ascii_text(self):
        design = {
            "version": 1,
            "name": "Unicode",
            "background": "#FFFFFF",
            "elements": [
                {"type": "Text", "x": 0, "y": 0, "w": 40, "h": 10, "text": "Pomp ✓", "color": "#000000"}
            ],
        }
        with self.assertRaisesRegex(ValueError, "ASCII"):
            generate_firmware_module(design)

    def test_project_module_exports_each_screen_and_first_screen_alias(self):
        project = {
            "version": 1,
            "name": "Pump",
            "screens": [
                dict(DEFAULT_DESIGN, name="Home"),
                dict(
                    DEFAULT_DESIGN,
                    name="Settings",
                    elements=DEFAULT_DESIGN["elements"]
                    + [
                        {
                            "type": "Filled rectangle",
                            "x": 2,
                            "y": 3,
                            "w": 12,
                            "h": 8,
                            "text": "",
                            "color": "#FF0000",
                        }
                    ],
                ),
            ],
        }
        source = generate_firmware_project(project)
        compile(source, "<generated-project-ui>", "exec")
        namespace = {}
        exec(source, namespace)
        framebuffer = RecordingFrameBuffer()
        namespace["draw_settings"](framebuffer)
        self.assertTrue(framebuffer.calls)
        self.assertIn(("fill_rect", 2, 3, 12, 8, 0x00F8), framebuffer.calls)
        home_framebuffer = RecordingFrameBuffer()
        alias_framebuffer = RecordingFrameBuffer()
        namespace["draw_home"](home_framebuffer)
        namespace["draw_custom_ui"](alias_framebuffer)
        self.assertEqual(alias_framebuffer.calls, home_framebuffer.calls)

    def test_project_rejects_duplicate_screen_names(self):
        project = {
            "version": 1,
            "name": "Pump",
            "screens": [DEFAULT_DESIGN, dict(DEFAULT_DESIGN)],
        }
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_project(project)

    def test_contact_sheet_contains_all_screens(self):
        screens = [dict(DEFAULT_DESIGN, name="Home"), dict(DEFAULT_DESIGN, name="Settings")]
        image = render_contact_sheet(screens)
        self.assertEqual(image.size, (480, 264))


if __name__ == "__main__":
    unittest.main()
