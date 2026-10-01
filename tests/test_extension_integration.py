import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace, ModuleType
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    def load_extension(self):
        self.options = {}
        def option(default, label, component=None, component_args=None, **kwargs):
            return SimpleNamespace(default=default, label=label, component=component, component_args=component_args)
        self.opts = SimpleNamespace(add_option=lambda name, opt: self.options.update({name: opt}))
        shared = SimpleNamespace(opts=self.opts, OptionInfo=option, hide_dirs={})
        modules = ModuleType("modules")
        modules.paths = SimpleNamespace(script_path=str(ROOT))
        modules.script_callbacks = SimpleNamespace(ImageSaveParams=object, on_image_saved=Mock(), on_ui_settings=Mock())
        modules.shared = shared
        modules.prompt_parser = SimpleNamespace()
        scripts = ModuleType("scripts")
        scripts.__path__ = [str(ROOT / "scripts")]
        self.scope = patch.dict(sys.modules, {"modules": modules, "scripts": scripts})
        self.scope.start()
        self.addCleanup(self.scope.stop)
        spec = importlib.util.spec_from_file_location("eagle_extension_test", ROOT / "scripts/eagle-pnginfo.py")
        extension = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extension)
        return extension

    def test_settings_table_roundtrip(self):
        import gradio as gr
        import json
        extension = self.load_extension()
        extension.on_ui_settings()
        option = self.options["eagle_keyword_tag_rules"]
        table = option.component(value=option.default, label=option.label, **option.component_args)
        rules = [["blue hair", "青髪"], ["outdoors", "屋外"]]
        processed = table.preprocess(table.postprocess(rules))
        self.assertEqual(json.loads(json.dumps(processed)), rules)
        mode = self.options["eagle_keyword_tag_match_mode"]
        radio = mode.component(value=mode.default, label=mode.label, **mode.component_args)
        self.assertEqual(radio.preprocess("token"), "token")

    def test_export_uses_saved_positive_and_preserves_tags(self):
        extension = self.load_extension()
        extension.on_ui_settings()
        for name, option in self.options.items():
            setattr(self.opts, name, option.default)
        self.opts.enable_eagle_integration = True
        self.opts.eagle_keyword_tags_enabled = True
        self.opts.eagle_keyword_tag_rules = [["blue hair", "青髪"], ["red hair", "赤髪"]]
        self.opts.save_positive_prompt_to_eagle_as_tags = True
        self.opts.save_negative_prompt_to_eagle_as = "None"
        params = SimpleNamespace(filename="test.png", image=None,
            pnginfo={"parameters": "blue hair\nNegative prompt: red hair\nSteps: 20, Seed: 1"},
            p=SimpleNamespace(prompt="different batch prompt", negative_prompt="red hair"))
        response = SimpleNamespace(content=b"ok", status_code=200)
        with patch.object(extension.api_util, "find_or_create_folder", return_value=None), patch.object(extension.api_item, "add_from_path", return_value=response) as send:
            extension.on_image_saved(params)
        item = send.call_args.kwargs["item"]
        self.assertIn("青髪", item.tags)
        self.assertNotIn("赤髪", item.tags)
        self.assertIn("different batch prompt", item.tags)
        self.opts.eagle_keyword_tags_enabled = False
        with patch.object(extension.api_util, "find_or_create_folder", return_value=None), patch.object(extension.api_item, "add_from_path", return_value=response) as send:
            extension.on_image_saved(params)
        self.assertNotIn("青髪", send.call_args.kwargs["item"].tags)


if __name__ == "__main__":
    unittest.main()
