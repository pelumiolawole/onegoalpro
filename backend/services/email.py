"""
services/email.py

Email delivery service using Resend.
Handles transactional emails: password reset, welcome, etc.
"""

import structlog
from datetime import datetime, timezone

import resend
from core.config import settings

logger = structlog.get_logger()

class EmailService:
    def __init__(self):
        self.api_key = settings.resend_api_key
        self.from_address = settings.email_from_address
        self.from_name = settings.email_from_name
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            resend.api_key = self.api_key

    async def send_password_reset(self, to_email: str, reset_token: str) -> bool:
        """
        Send password reset email with magic link.
        Returns True if sent successfully, False otherwise.
        """
        if not self.enabled:
            logger.warning("email_disabled", reason="no_api_key", email=to_email)
            # In development, log the token so you can test manually
            if settings.is_development:
                logger.info("dev_reset_token", email=to_email, token=reset_token)
            return False

        reset_url = f"{settings.password_reset_frontend_url}?token={reset_token}"
        
        try:
            response = resend.Emails.send({
                "from": self.from_address,
                "to": to_email,
                "subject": "Reset your OneGoal password",
                "html": f"""
                <div style="font-family: system-ui, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
                    <h2 style="color: #F59E0B; margin-bottom: 24px;">Reset your password</h2>
                    <p style="color: #4A4A4A; line-height: 1.6; margin-bottom: 24px;">
                        You requested a password reset for your OneGoal account. 
                        Click the button below to set a new password. This link expires in 24 hours.
                    </p>
                    <a href="{reset_url}" 
                       style="display: inline-block; background: #F59E0B; color: #0A0908; 
                              padding: 14px 28px; text-decoration: none; border-radius: 8px;
                              font-weight: 600; margin-bottom: 24px;">
                        Reset Password
                    </a>
                    <p style="color: #7A6E65; font-size: 14px; line-height: 1.5;">
                        If you didn't request this, you can safely ignore this email. 
                        Your password won't change until you click the link above.
                    </p>
                    <hr style="border: none; border-top: 1px solid #E8E2DC; margin: 32px 0;">
                    <p style="color: #A09690; font-size: 12px;">
                        One Goal. One identity. One day at a time.
                    </p>
                </div>
                """,
                "text": f"""
Reset your OneGoal password

You requested a password reset. Visit this link to set a new password:
{reset_url}

This link expires in 24 hours.

If you didn't request this, ignore this email.
                """,
            })
            
            logger.info("password_reset_email_sent", 
                       email=to_email, 
                       message_id=response.get('id'))
            return True
            
        except Exception as e:
            logger.error("password_reset_email_failed", 
                        email=to_email, 
                        error=str(e))
            return False

    async def send_welcome_email(self, to_email: str, display_name: str | None) -> bool:
        """Send welcome email after successful signup."""
        if not self.enabled:
            return False
            
        name = display_name or "there"
        
        try:
            response = resend.Emails.send({
                "from": self.from_address,
                "to": to_email,
                "subject": "Welcome to OneGoal — Your transformation starts now",
                "html": f"""
                <div style="font-family: system-ui, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
                    <h2 style="color: #F59E0B; margin-bottom: 24px;">Welcome, {name}</h2>
                    <p style="color: #4A4A4A; line-height: 1.6; margin-bottom: 24px;">
                        You just took the first step toward becoming who you want to be. 
                        One Goal isn't about doing more — it's about becoming more through 
                        consistent, identity-driven action.
                    </p>
                    <p style="color: #4A4A4A; line-height: 1.6; margin-bottom: 24px;">
                        Your first task: Complete your discovery interview. 
                        This 5-minute conversation helps us understand your goals 
                        and design a strategy that fits your life.
                    </p>
                    <a href="https://onegoalpro.vercel.app/interview" 
                       style="display: inline-block; background: #F59E0B; color: #0A0908; 
                              padding: 14px 28px; text-decoration: none; border-radius: 8px;
                              font-weight: 600;">
                        Start Interview
                    </a>
                </div>
                """,
            })
            return True
        except Exception as e:
            logger.error("welcome_email_failed", email=to_email, error=str(e))
            return False

# Singleton instance
email_service = EmailService()