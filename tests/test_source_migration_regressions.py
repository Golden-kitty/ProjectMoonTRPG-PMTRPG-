"""防止格式迁移再次改写已提交的战技语义；规则更新须同步审核这些基线。"""

from __future__ import annotations

import html
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COURSES = ROOT / "docs" / "资源目录" / "课程"


def read_course(relative: str) -> str:
    return (COURSES / relative).read_text(encoding="utf-8")


def table_rows(source: str, table_id: str) -> list[list[str]]:
    matches = re.findall(
        rf'<table\b[^>]*data-table-id="{re.escape(table_id)}"[^>]*>(.*?)</table>',
        source,
        flags=re.DOTALL,
    )
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one table {table_id}, got {len(matches)}")

    def cell_text(cell: str) -> str:
        cell = re.sub(r"<br\s*/?>", "\n", cell)
        return html.unescape(re.sub(r"<[^>]+>", "", cell)).strip()

    return [
        [cell_text(cell) for cell in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row, re.DOTALL)]
        for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", matches[0], re.DOTALL)
    ]


class SourceMigrationRegressionTests(unittest.TestCase):
    def test_tactical_defense_keeps_action_and_single_effect_row(self) -> None:
        rows = table_rows(read_course("基础战技/标准格斗术.md"), "html-74dd252d21f5")
        self.assertEqual(rows[-3], ["计划", "防御", "招架", "1-6"])
        self.assertEqual(rows[-2], ["计划", "防御", "闪避", "1-8"])
        effect = "【使用时】从这两个骰中选择一个部署。"
        self.assertEqual(rows[-1], [effect])
        self.assertEqual(sum(cell.count(effect) for row in rows for cell in row), 1)

    def test_rat_way_preserves_distinct_defense_and_counter_effects(self) -> None:
        rows = table_rows(read_course("基础战技/街头搏击术.md"), "html-5a2e3ea3936d")
        self.assertEqual(rows[-4], ["计划", "防御", "招架", "2-6"])
        self.assertEqual(
            rows[-3],
            ["【当地地头蛇20+】本骰获得威力+2\n【搏斗20+】本骰获得威力+2"],
        )
        self.assertEqual(rows[-2], ["计划", "反击", "突刺", "1-5"])
        self.assertEqual(rows[-1], ["【命中时】下一幕对目标施加1层流血"])

    def test_caged_dog_is_not_a_copy_of_explosive_strike(self) -> None:
        source = read_course("流派战技/丧家犬.md")
        caged = table_rows(source, "html-bab1acb4c2ff")
        explosive = table_rows(source, "html-a56056f33abf")
        self.assertEqual(caged[0], ["笼中狗斗"])
        self.assertEqual(caged[1], ["传说", "罕见", "丧家犬", "丧家犬声望40+"])
        self.assertEqual(caged[2], ["掌握前提", "将一枚骰子重复投掷四次及以上"])
        self.assertEqual(caged[-2], ["行动", "攻击", "打击", "22-44"])
        self.assertEqual(
            caged[-1],
            ["【使用时】随机选择一个自身战技栏中装备的战技，若其光芒消耗不超过3，"
             "使用其数值替换本战技的数值\n【拼点胜利】对目标再次使用本战技\n"
             "【搏斗60+] 使用时效果改为光芒消耗不超过4。"],
        )
        self.assertEqual(explosive[0], ["爆裂打击"])
        self.assertEqual(explosive[1], ["传说", "史诗", "丧家犬", "丧家犬声望50+"])
        self.assertEqual(explosive[-2], ["行动", "对决", "打击", "6-66"])
        self.assertNotEqual(caged[1:], explosive[1:])
        self.assertIn("#### **笼中狗斗**", source)
        self.assertIn("####   **再来再来**", source)

    def test_name_disagreement_is_not_silently_resolved_by_migration(self) -> None:
        source = read_course("流派战技/臼齿事务所.md")
        rows = table_rows(source, "html-0bb68df01416")
        self.assertIn("#### **铤而走险**", source)
        self.assertEqual(rows[0], ["链而走险"])


if __name__ == "__main__":
    unittest.main()
