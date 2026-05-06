from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

db_file = tempfile.NamedTemporaryFile(prefix="data-center-test-", suffix=".db", delete=False)
db_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{db_file.name}"

from api.data_cleaning import retry_anomaly_scrape  # noqa: E402
from api.sku_repository import get_scrape_overview  # noqa: E402
from db.session import Base, SessionLocal, engine, init_db  # noqa: E402
from models import AnomalyAlert, ScrapeTaskRun, SkuProduct  # noqa: E402
from services.anomaly_recovery import resolve_recovered_data_anomalies  # noqa: E402
from services.task_runs import mark_stale_scrape_runs  # noqa: E402


class DataCenterClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        init_db()

    @classmethod
    def tearDownClass(cls) -> None:
        Base.metadata.drop_all(bind=engine)
        try:
            os.unlink(db_file.name)
        except FileNotFoundError:
            pass

    def setUp(self) -> None:
        self.db = SessionLocal()

    def tearDown(self) -> None:
        for model in (ScrapeTaskRun, AnomalyAlert, SkuProduct):
            self.db.query(model).delete()
        self.db.commit()
        self.db.close()

    def test_mark_stale_scrape_runs_closes_old_pending_and_running_runs(self) -> None:
        now = datetime(2026, 5, 6, 10, 0, 0)
        pending = ScrapeTaskRun(
            task_name="scrape_product",
            trigger_source="TEST",
            requested_url="https://example.com/pending.html",
            status="PENDING",
        )
        running = ScrapeTaskRun(
            task_name="scrape_product",
            trigger_source="TEST",
            requested_url="https://example.com/running.html",
            status="RUNNING",
            started_at=now - timedelta(minutes=45),
        )
        fresh = ScrapeTaskRun(
            task_name="scrape_product",
            trigger_source="TEST",
            requested_url="https://example.com/fresh.html",
            status="PENDING",
        )
        self.db.add_all([pending, running, fresh])
        self.db.commit()

        pending.created_at = now - timedelta(minutes=20)
        fresh.created_at = now - timedelta(minutes=2)
        self.db.commit()

        closed_count = mark_stale_scrape_runs(self.db, now=now)
        self.db.commit()

        self.assertEqual(closed_count, 2)
        self.assertEqual(pending.status, "TIMEOUT")
        self.assertEqual(running.status, "TIMEOUT")
        self.assertEqual(fresh.status, "PENDING")
        self.assertGreaterEqual(pending.failure_count, 1)
        self.assertIn("自动关闭", pending.summary_message)

    def test_retry_anomaly_scrape_creates_run_and_enqueues_task(self) -> None:
        product = SkuProduct(
            platform="jd",
            sku_id="SKU-RETRY",
            product_name="Retry product",
            product_url="https://item.jd.com/SKU-RETRY.html",
        )
        self.db.add(product)
        self.db.flush()
        anomaly = AnomalyAlert(
            alert_type="DATA_MISSING",
            platform=product.platform,
            sku_id=product.sku_id,
            product_id=product.id,
            alert_value=product.product_url,
            threshold="quality",
            is_verified=0,
            message="missing data",
        )
        self.db.add(anomaly)
        self.db.commit()

        with patch("api.data_cleaning.enqueue_task", return_value="task-123") as enqueue_task:
            response = retry_anomaly_scrape(anomaly.id, db=self.db)

        data = response["data"]
        run = self.db.query(ScrapeTaskRun).filter(ScrapeTaskRun.id == data["run_id"]).one()
        enqueue_task.assert_called_once_with(
            "tasks.scraping.scrape_product",
            product.product_url,
            run.id,
        )
        self.assertEqual(data["task_id"], "task-123")
        self.assertEqual(run.status, "PENDING")
        self.assertEqual(run.trigger_source, "ANOMALY_RETRY")
        self.assertEqual(run.requested_url, product.product_url)

    def test_scrape_overview_reports_status_counts_and_schedule(self) -> None:
        self.db.add_all(
            [
                ScrapeTaskRun(
                    task_name="scrape_product",
                    trigger_source="TEST",
                    requested_url="https://example.com/success.html",
                    status="SUCCESS",
                    processed_count=1,
                    success_count=1,
                    finished_at=datetime(2026, 5, 6, 9, 0, 0),
                    summary_message="success",
                ),
                ScrapeTaskRun(
                    task_name="scrape_product",
                    trigger_source="TEST",
                    requested_url="https://example.com/failed.html",
                    status="FAILED",
                    processed_count=1,
                    failure_count=1,
                    finished_at=datetime(2026, 5, 6, 9, 5, 0),
                    summary_message="failed",
                ),
                ScrapeTaskRun(
                    task_name="scrape_active_products",
                    trigger_source="TEST",
                    status="RUNNING",
                    started_at=datetime.now(),
                    summary_message="running",
                ),
            ]
        )
        self.db.commit()

        with patch.dict(
            os.environ,
            {
                "ENABLE_PERIODIC_SCRAPE": "true",
                "PERIODIC_SCRAPE_INTERVAL_MINUTES": "15",
                "PERIODIC_SCRAPE_LIMIT": "7",
                "PERIODIC_SCRAPE_PLATFORM": "jd",
                "MAINTENANCE_INTERVAL_MINUTES": "3",
            },
        ):
            response = get_scrape_overview(db=self.db)

        data = response["data"]
        self.assertEqual(data["status_counts"]["SUCCESS"], 1)
        self.assertEqual(data["status_counts"]["FAILED"], 1)
        self.assertEqual(data["open_run_count"], 1)
        self.assertEqual(data["success_rate"], 50.0)
        self.assertEqual(data["schedule"]["periodic_scrape_interval_minutes"], 15)
        self.assertEqual(data["schedule"]["periodic_scrape_limit"], 7)
        self.assertEqual(data["schedule"]["periodic_scrape_platform"], "jd")
        self.assertEqual(data["schedule"]["maintenance_interval_minutes"], 3)
        self.assertEqual(data["latest_problem_run"]["status"], "FAILED")

    def test_resolve_recovered_data_anomalies_marks_matching_open_alerts_verified(self) -> None:
        product = SkuProduct(
            platform="jd",
            sku_id="SKU-RECOVERED",
            product_name="Recovered product",
            product_url="https://item.jd.com/SKU-RECOVERED.html",
        )
        self.db.add(product)
        self.db.flush()
        matching = AnomalyAlert(
            alert_type="SCRAPE_FAILURE",
            platform=product.platform,
            sku_id=product.sku_id,
            product_id=product.id,
            alert_value=product.product_url,
            threshold="worker scrape",
            is_verified=0,
            message="failed before",
        )
        unrelated = AnomalyAlert(
            alert_type="DATA_MISSING",
            platform="jd",
            sku_id="OTHER",
            alert_value="https://item.jd.com/OTHER.html",
            threshold="quality",
            is_verified=0,
            message="should remain open",
        )
        self.db.add_all([matching, unrelated])
        self.db.commit()

        recovered_count = resolve_recovered_data_anomalies(
            self.db,
            platform=product.platform,
            product_id=product.id,
            product_url=product.product_url,
            sku_id=product.sku_id,
        )
        self.db.commit()

        self.assertEqual(recovered_count, 1)
        self.assertEqual(matching.is_verified, 1)
        self.assertEqual(matching.verification_result, "重抓成功，系统自动关闭异常")
        self.assertEqual(unrelated.is_verified, 0)


if __name__ == "__main__":
    unittest.main()
