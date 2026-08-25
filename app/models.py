from sqlalchemy import Column, String, Float, Integer, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base

class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(String(20), primary_key=True, index=True)
    merchant_name = Column(String(150), nullable=False)
    merchant_category = Column(String(50), nullable=False, index=True)
    city = Column(String(50), nullable=False, index=True)
    state = Column(String(50), nullable=False)
    onboarding_date = Column(Date, nullable=False)

    transactions = relationship("Transaction", back_populates="merchant")

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(20), primary_key=True, index=True)
    city = Column(String(50), nullable=False)
    device_type = Column(String(20), nullable=False)
    signup_date = Column(Date, nullable=False)

    transactions = relationship("Transaction", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(30), primary_key=True, index=True)
    merchant_id = Column(String(20), ForeignKey("merchants.merchant_id"), nullable=False, index=True)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    transaction_date = Column(DateTime, nullable=False, index=True)
    transaction_amount = Column(Float, nullable=False)
    transaction_status = Column(String(20), nullable=False, index=True)
    payment_type = Column(String(30), nullable=False)
    failure_reason = Column(String(50), nullable=False)

    merchant = relationship("Merchant", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
