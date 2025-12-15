import secrets
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, update, and_
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import SecretStr, EmailStr

from app.models.otp import OTP
from app.config.database import AsyncSessionLocal
from app.core.settings import settings

LOG = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 10

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=SecretStr(settings.mail_password),
    MAIL_FROM=settings.mail_from,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=settings.use_credentials,
    VALIDATE_CERTS=settings.validate_certs
)

async def send_otp_email(email: str, otp_code: str):
    """Sends the actual email using SMTP."""
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #2c3e50; text-align: center;">OTP</h2>
                <p>Hello,</p>
                <p>You requested an OTP to verify your Obex Edge account.</p>
                <div style="background-color: #f4f6f7; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
                    <span style="font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #2980b9;">{otp_code}</span>
                </div>
                <p>This code will expire in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.</p>
                <p style="font-size: 12px; color: #7f8c8d; margin-top: 30px;">
                    If you did not request this code, please ignore this email.
                </p>
            </div>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Your Obex Edge Verification Code",
        recipients=[email], # type: ignore
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        LOG.info(f"OTP sent successfully to {email}")
    except Exception as e:
        LOG.error(f"Failed to send email to {email}: {e}")
        raise e

async def generate_otp(email: str) -> str:
    """Generates a 6-digit OTP, saves to DB, and sends via Email."""
    otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    async with AsyncSessionLocal() as session:
        await session.execute(
            update(OTP)
            .where(and_(OTP.email == email, OTP.is_used == False))
            .values(is_used=True)
        )

        new_otp = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            is_used=False
        )
        session.add(new_otp)
        await session.commit()

    await send_otp_email(email, otp_code)
    
    return otp_code

async def verify_otp(email: str, otp_input: str) -> bool:
    """Verifies the OTP code."""
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        
        q = select(OTP).where(
            and_(
                OTP.email == email,
                OTP.otp_code == otp_input,
                OTP.is_used == False,
                OTP.expires_at > now
            )
        )
        result = await session.execute(q)
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            return False

        await session.execute(
            update(OTP)
            .where(
                and_(
                    OTP.email == email,
                    OTP.otp_code == otp_input
                )
            )
            .values(is_used=True)
        )
        await session.commit()
        
        return True