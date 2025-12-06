"""Email alerting system for scraper monitoring."""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages email alerts for scraper failures and issues."""

    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        from_email: str = None,
        to_email: str = None,
    ):
        """Initialize alert manager with SMTP settings."""
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("ALERT_FROM_EMAIL", self.smtp_user)
        self.to_email = to_email or os.getenv("ALERT_TO_EMAIL", "rohit.trivedi81@gmail.com")

    def is_configured(self) -> bool:
        """Check if email alerts are properly configured."""
        return bool(self.smtp_user and self.smtp_password and self.to_email)

    def send_email(self, subject: str, body: str, html: bool = True) -> bool:
        """Send an email alert."""
        if not self.is_configured():
            logger.warning("Email alerts not configured - missing SMTP credentials")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = self.to_email

            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, self.to_email, msg.as_string())

            logger.info(f"Alert email sent: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False

    def send_scraper_failure_alert(
        self,
        council_code: str,
        error_message: str,
        tier: int = None,
        duration: int = None,
    ) -> bool:
        """Send alert for a scraper failure."""
        subject = f"[Council Scraper] FAILURE: {council_code}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #dc3545;">Scraper Failure Alert</h2>

            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Council:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{council_code}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Tier:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{tier or 'Unknown'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Time:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S AEST')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Duration:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{duration or 0} seconds</td>
                </tr>
            </table>

            <h3 style="color: #333;">Error Details:</h3>
            <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">
{error_message}
            </pre>

            <p style="color: #666; margin-top: 20px;">
                This is an automated alert from Council DA Scraper.
            </p>
        </body>
        </html>
        """

        return self.send_email(subject, body)

    def send_batch_summary_alert(
        self,
        tier: int,
        batch: Optional[int],
        results: list[dict],
    ) -> bool:
        """Send summary alert after a batch completes."""
        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = sum(1 for r in results if r.get("status") == "error")
        total_new = sum(r.get("new", 0) for r in results)
        total_updated = sum(r.get("updated", 0) for r in results)

        # Only send if there are errors
        if error_count == 0:
            logger.info(f"Tier {tier} batch completed successfully - no alert needed")
            return True

        batch_str = f" Batch {batch}" if batch else ""
        subject = f"[Council Scraper] Tier {tier}{batch_str} - {error_count} Failures"

        # Build error details
        error_rows = ""
        for r in results:
            if r.get("status") == "error":
                error_rows += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{r.get('council', 'Unknown')}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #dc3545;">{r.get('error', 'Unknown error')[:100]}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{r.get('duration', 0)}s</td>
                </tr>
                """

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #fd7e14;">Batch Completion Summary</h2>

            <h3>Overview</h3>
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Tier:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{tier}{batch_str}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Time:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S AEST')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Success:</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #28a745;">{success_count} councils</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Failed:</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #dc3545;">{error_count} councils</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">New DAs:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{total_new}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Updated DAs:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{total_updated}</td>
                </tr>
            </table>

            <h3 style="color: #dc3545;">Failed Councils</h3>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background: #f8f9fa;">
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Council</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Error</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Duration</th>
                </tr>
                {error_rows}
            </table>

            <p style="color: #666; margin-top: 20px;">
                This is an automated alert from Council DA Scraper.
            </p>
        </body>
        </html>
        """

        return self.send_email(subject, body)

    def send_daily_digest(
        self,
        stats: dict,
        failed_councils: list[str],
    ) -> bool:
        """Send daily digest email with overall status."""
        subject = f"[Council Scraper] Daily Digest - {datetime.now().strftime('%Y-%m-%d')}"

        failed_list = ""
        if failed_councils:
            failed_list = "<ul>" + "".join(f"<li>{c}</li>" for c in failed_councils) + "</ul>"
        else:
            failed_list = "<p style='color: #28a745;'>All scrapers healthy!</p>"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #007bff;">Daily Scraper Digest</h2>

            <h3>24-Hour Statistics</h3>
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Total Runs:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{stats.get('total_runs', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Successful:</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #28a745;">{stats.get('successful_runs', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Failed:</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #dc3545;">{stats.get('failed_runs', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">New DAs:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{stats.get('total_new', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Updated DAs:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{stats.get('total_updated', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Total DAs in DB:</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{stats.get('total_applications', 0)}</td>
                </tr>
            </table>

            <h3>Councils with Issues (3+ failures in 24h)</h3>
            {failed_list}

            <p style="color: #666; margin-top: 20px;">
                Dashboard: <a href="{os.getenv('API_URL', 'https://your-api.onrender.com')}/docs">API Docs</a>
            </p>
        </body>
        </html>
        """

        return self.send_email(subject, body)
