"""Email sending service using SMTP (or console fallback for dev)."""

import asyncio
import logging
import smtplib
import socket
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Raised when email sending fails."""


class EmailService:
    """Send verification codes via SMTP, with console fallback for dev."""

    @staticmethod
    async def send_verification_code(email: str, code: str) -> None:
        """Send a verification code email asynchronously.

        Falls back to console logging when SMTP is not configured.
        Raises EmailSendError on SMTP failure (caught by caller).
        """
        subject = "【股票基金投资论坛】邮箱验证码"
        body = (
            f"您好！\n\n"
            f"您的邮箱验证码为：{code}\n\n"
            f"验证码有效期为5分钟，请勿泄露给他人。\n"
            f"如非本人操作，请忽略此邮件。\n\n"
            f"—— 股票基金投资论坛"
        )

        if not settings.smtp_configured:
            # Dev fallback — same pattern as simulated SMS
            logger.info(
                f"[SIMULATED EMAIL] To: {email}  Code: {code}"
            )
            return

        # Run blocking SMTP call in thread pool with a timeout
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    EmailService._send_smtp, email, subject, body
                ),
                timeout=settings.smtp_timeout + 5,  # slightly longer than SMTP timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"SMTP send timed out for {email}")
            raise EmailSendError("邮件发送超时，请稍后重试")
        except EmailSendError:
            raise
        except Exception as exc:
            logger.error(f"SMTP send failed for {email}: {exc}")
            raise EmailSendError("邮件发送失败，请稍后重试")

    @staticmethod
    def _send_smtp(recipient: str, subject: str, body: str) -> None:
        """Send an email via SMTP (blocking — call via asyncio.to_thread).

        Auto-selects SSL (port 465) vs STARTTLS (port 587/25) based on config.
        Raises EmailSendError with a descriptive message on any failure.
        """
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email
        msg["To"] = recipient

        try:
            if settings.smtp_use_ssl:
                # Port 465 — implicit SSL from the start (163, QQ, etc.)
                server = smtplib.SMTP_SSL(
                    settings.smtp_host,
                    settings.smtp_port,
                    timeout=settings.smtp_timeout,
                )
            else:
                # Port 587 or 25 — plain then upgrade via STARTTLS
                server = smtplib.SMTP(
                    settings.smtp_host,
                    settings.smtp_port,
                    timeout=settings.smtp_timeout,
                )
                server.starttls()

            try:
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
            finally:
                server.quit()
        except smtplib.SMTPAuthenticationError as exc:
            raise EmailSendError(
                "邮箱登录失败：授权码或密码错误，请检查 SMTP_USER / SMTP_PASSWORD"
            ) from exc
        except smtplib.SMTPConnectError as exc:
            raise EmailSendError(
                f"无法连接到邮件服务器 {settings.smtp_host}:{settings.smtp_port}，"
                "请检查 SMTP_HOST / SMTP_PORT 是否正确，以及网络是否允许此端口"
            ) from exc
        except socket.timeout as exc:
            raise EmailSendError(
                f"连接邮件服务器超时（{settings.smtp_timeout}秒），"
                "请检查网络连接或增大 SMTP_TIMEOUT"
            ) from exc
        except (smtplib.SMTPException, socket.error, OSError) as exc:
            raise EmailSendError(str(exc)) from exc
