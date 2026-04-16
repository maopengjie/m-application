from datetime import datetime
from typing import Optional
from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    main_image: Mapped[Optional[str]] = mapped_column(String(500))

    skus: Mapped[list["ProductSKU"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductSKU(Base, TimestampMixin):
    __tablename__ = "product_skus"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    platform: Mapped[str] = mapped_column(String(50), index=True)  # JD, Taobao, etc.
    platform_sku_id: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    original_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    shop_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)

    product: Mapped["Product"] = relationship(back_populates="skus")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="sku", cascade="all, delete-orphan")
    coupons: Mapped[list["Coupon"]] = relationship(back_populates="sku", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="sku", cascade="all, delete-orphan")
    risk_score: Mapped[Optional["RiskScore"]] = relationship(back_populates="sku", cascade="all, delete-orphan")
    alerts: Mapped[list["PriceAlert"]] = relationship(back_populates="sku", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey("product_skus.id"), index=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, index=True)

    sku: Mapped["ProductSKU"] = relationship(back_populates="price_history")


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey("product_skus.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    desc: Mapped[Optional[str]] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50))  # coupon, discount, etc.
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    condition_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    sku: Mapped["ProductSKU"] = relationship(back_populates="coupons")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey("product_skus.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    sku: Mapped["ProductSKU"] = relationship(back_populates="reviews")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    sku_id: Mapped[int] = mapped_column(ForeignKey("product_skus.id"), primary_key=True)
    score: Mapped[int] = mapped_column(Integer)
    comment_abnormal: Mapped[bool] = mapped_column(Boolean, default=False)
    sales_abnormal: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    sku: Mapped["ProductSKU"] = relationship(back_populates="risk_score")


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey("product_skus.id"), index=True)
    target_price: Mapped[float] = mapped_column(Numeric(10, 2))
    is_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    sku: Mapped["ProductSKU"] = relationship(back_populates="alerts")
