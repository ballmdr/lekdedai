"""Task 30: รายงาน closed beta ต่อ N งวด (ค่าเริ่มต้น 2) พร้อม feedback/ผู้ใช้/สถานะ.

ใช้ประกอบการตัดสินใจ go/no-go และ Checkpoint E — บันทึกเป็นไฟล์ได้.
"""
import json as json_module
from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from analytics.report import build_report, format_text


class Command(BaseCommand):
    help = "รายงาน beta ต่อ N งวด: activation/completion/result-check/retention + feedback"

    def add_arguments(self, parser):
        parser.add_argument("--draws", type=int, default=2, help="จำนวนงวดล่าสุด")
        parser.add_argument("--days", type=int, default=90, help="ช่วงเวลาที่นับ")
        parser.add_argument("--output", type=str, default="")
        parser.add_argument(
            "--format", choices=["text", "json"], default="text",
        )

    def handle(self, *args, **options):
        report = build_report(days=options["days"], draws=options["draws"])
        report["feedback"] = self._feedback(days=options["days"])
        report["invites"] = self._invites()
        report["system_status"] = self._system_status()
        report["checkpoint_e"] = self._checkpoint_inputs(report)

        if options["output"]:
            path = Path(options["output"])
            path.parent.mkdir(parents=True, exist_ok=True)
            if options["format"] == "json":
                path.write_text(
                    json_module.dumps(report, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            else:
                path.write_text(self._format_text(report), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"เขียนรายงาน beta แล้ว: {path}"))
            return

        self.stdout.write(self._format_text(report))

    def _feedback(self, days):
        from home.models import ContactMessage

        since = timezone.now() - timedelta(days=days)
        rows = ContactMessage.objects.filter(created_at__gte=since)
        by_type = {
            choice: rows.filter(message_type=choice).count()
            for choice, _ in ContactMessage.TYPE_CHOICES
        }
        return {
            "total": rows.count(),
            "by_type": by_type,
            "beta_open": rows.filter(message_type="beta").exclude(status="done").count(),
        }

    def _invites(self):
        from qa.models import BetaInvite

        invites = BetaInvite.objects.all()
        return {
            "count": invites.count(),
            "active": invites.filter(is_active=True).count(),
            "used_total": sum(invites.values_list("used_count", flat=True)),
        }

    def _system_status(self):
        from qa.rollout import get_beta_status

        status = get_beta_status()
        return {
            "state": status["state"],
            "reasons": status["reasons"],
            "stage": status["stage"],
            "kill_switch": status["kill_switch"],
        }

    def _checkpoint_inputs(self, report):
        draws = report["draws"]
        return {
            "draws_with_data": len(draws),
            "has_two_draws": len(draws) >= 2,
            "activation_total": sum(d["activation"] for d in draws),
            "result_checked_total": sum(d["result_checked"] for d in draws),
            "retention_pct": report["retention"]["pct"],
            "decision": "ยังไม่มีข้อมูล 2 งวดพอสรุป Checkpoint E" if len(draws) < 2
            else "พร้อมประชุม go/no-go และประเมิน billing",
        }

    def _format_text(self, report):
        lines = [format_text(report, title="รายงาน closed beta")]
        feedback = report["feedback"]
        invites = report["invites"]
        status = report["system_status"]
        checkpoint = report["checkpoint_e"]

        lines += [
            "",
            "== Feedback (ContactMessage) ==",
            f"  รวม {feedback['total']} ฉบับ, beta ค้างดำเนินการ {feedback['beta_open']} ฉบับ",
            "  แยกประเภท: " + ", ".join(
                f"{k}={v}" for k, v in feedback["by_type"].items()
            ),
            "",
            "== รหัสเชิญ ==",
            f"  ทั้งหมด {invites['count']} รหัส (active {invites['active']}), "
            f"ใช้ไปรวม {invites['used_total']} ครั้ง",
            "",
            "== สถานะระบบ ==",
            f"  state={status['state']} stage={status['stage']} "
            f"kill_switch={status['kill_switch']}",
        ]
        for reason in status["reasons"]:
            lines.append(f"    - {reason}")

        retention = (
            f"{checkpoint['retention_pct']}%"
            if checkpoint["retention_pct"] is not None else "-"
        )
        lines += [
            "",
            "== Checkpoint E (ตัดสินใจรายได้) ==",
            f"  งวดที่มีข้อมูล: {checkpoint['draws_with_data']} "
            f"(ครบ 2 งวด: {'ใช่' if checkpoint['has_two_draws'] else 'ยัง'})",
            f"  activation รวม: {checkpoint['activation_total']}, "
            f"result-check รวม: {checkpoint['result_checked_total']}, "
            f"retention: {retention}",
            f"  ข้อสรุป: {checkpoint['decision']}",
            "  หลักฐาน 'ยอมจ่าย': รวบรวม waitlist/ข้อความจาก /contact/?type=beta "
            "ก่อนตัดสินใจสร้าง billing (ดู docs/CHECKPOINT_E.md)",
        ]
        return "\n".join(lines)
