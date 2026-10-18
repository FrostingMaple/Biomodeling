"""报告结构与完整性校验测试。"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from report_validation import validate_report_content  # noqa: E402
from tools import save_report  # noqa: E402


def complete_report():
    return """## 模型方程

dX/dt = r*X

## 参数

r = 1.0，参数来源：文献。

## 假设

假设环境恒定。

## 模拟结果

模拟得到指数增长，峰值为 2.0。

## 局限

未包含空间异质性。

## 结论

模型可以复现文献中的定性行为。
"""


class ReportValidationTests(unittest.TestCase):
    def test_complete_report_passes(self):
        report = validate_report_content(complete_report())
        self.assertTrue(report["valid"], report)
        self.assertFalse(report["warnings"])

    def test_missing_equation_is_warning(self):
        content = complete_report().replace("## 模型方程\n\ndX/dt = r*X\n\n", "")
        report = validate_report_content(content)
        self.assertTrue(report["valid"])
        self.assertTrue(any("方程" in item for item in report["warnings"]))

    def test_empty_report_is_error(self):
        report = validate_report_content("   ")
        self.assertFalse(report["valid"])
        self.assertTrue(report["errors"])

    def test_strict_mode_rejects_missing_sections(self):
        content = complete_report().replace("## 局限\n\n未包含空间异质性。\n\n", "")
        report = validate_report_content(content, strict=True)
        self.assertFalse(report["valid"])
        self.assertTrue(any("局限" in item for item in report["errors"]))

    def test_placeholder_is_warning(self):
        content = complete_report() + "\nTODO: 补充实验验证。\n"
        report = validate_report_content(content)
        self.assertTrue(any("TODO" in item for item in report["warnings"]))

    def test_soft_save_returns_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                message = save_report("Soft report", "body", filename="soft_report")
                self.assertIn("Report saved to", message)
                self.assertIn("validation warnings", message)
                self.assertTrue((Path(tmp) / "output" / "reports" / "soft_report.md").exists())
            finally:
                os.chdir(old_cwd)

    def test_strict_save_rejects_incomplete_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with self.assertRaises(ValueError):
                    save_report("Strict report", "body", filename="strict_report", strict=True)
                self.assertFalse((Path(tmp) / "output" / "reports" / "strict_report.md").exists())
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
