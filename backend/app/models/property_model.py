from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from backend.app.core.database import Base

class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True, index=True)
    portal = Column(String(50), nullable=False, index=True) # 'mercadolibre', 'argenprop', 'zonaprop', 'properati'
    external_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    property_type = Column(String(50), nullable=False, index=True) # 'departamento', 'casa', 'ph', 'terreno', 'otro'
    operation_type = Column(String(50), default='venta', index=True)
    
    # Precios
    price_usd = Column(Float, nullable=False, index=True)
    price_currency_orig = Column(String(10), default='USD')
    price_amount_orig = Column(Float, nullable=True)
    expenses = Column(Float, nullable=True)
    
    # Dimensiones
    total_area_m2 = Column(Float, nullable=True, index=True)
    covered_area_m2 = Column(Float, nullable=True)
    price_per_m2 = Column(Float, nullable=True, index=True)
    
    # Ambientes
    rooms = Column(Integer, nullable=True)
    bedrooms = Column(Integer, nullable=True, index=True)
    bathrooms = Column(Integer, nullable=True, index=True)
    garages = Column(Integer, nullable=True)
    
    # Ubicación
    neighborhood = Column(String(100), nullable=False, index=True)
    zone = Column(String(100), nullable=False, index=True) # 'CABA', 'GBA Norte', 'GBA Sur', 'GBA Oeste'
    city = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Detalles
    description = Column(Text, nullable=True)
    images_json = Column(Text, default='[]') # JSON list
    seller_name = Column(String(150), nullable=True)
    seller_type = Column(String(50), nullable=True) # 'inmobiliaria', 'duenio_directo'
    antiquity = Column(String(50), nullable=True) # ej: '55 años', 'A estrenar', '10 años'
    disposition = Column(String(50), nullable=True) # ej: 'Frente', 'Contrafrente', 'Lateral', 'Interno'
    orientation = Column(String(50), nullable=True) # ej: 'Norte', 'Sudeste', etc.
    
    # Metadatos y Gestión
    publication_date = Column(DateTime, nullable=True, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Acciones de Usuario
    is_favorite = Column(Boolean, default=False, index=True)
    is_discarded = Column(Boolean, default=False, index=True)
    user_notes = Column(Text, nullable=True)
    
    # Deduplicación
    cluster_id = Column(String(64), nullable=True, index=True)
    cluster_confidence = Column(Float, nullable=True)

    # Relaciones
    price_history = relationship('PriceHistory', back_populates='property', cascade='all, delete-orphan')

    @property
    def images(self):
        try:
            return json.loads(self.images_json) if self.images_json else []
        except Exception:
            return []

    @images.setter
    def images(self, value):
        self.images_json = json.dumps(value if isinstance(value, list) else [])

    def to_dict(self):
        return {
            'id': self.id,
            'portal': self.portal,
            'external_id': self.external_id,
            'title': self.title,
            'url': self.url,
            'property_type': self.property_type,
            'operation_type': self.operation_type,
            'price_usd': self.price_usd,
            'price_currency_orig': self.price_currency_orig,
            'price_amount_orig': self.price_amount_orig,
            'expenses': self.expenses,
            'total_area_m2': self.total_area_m2,
            'covered_area_m2': self.covered_area_m2,
            'price_per_m2': round(self.price_per_m2, 1) if self.price_per_m2 else None,
            'rooms': self.rooms,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'garages': self.garages,
            'neighborhood': self.neighborhood,
            'zone': self.zone,
            'city': self.city,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'images': self.images,
            'seller_name': self.seller_name,
            'seller_type': self.seller_type,
            'antiquity': self.antiquity,
            'disposition': self.disposition,
            'orientation': self.orientation,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_favorite': self.is_favorite,
            'is_discarded': self.is_discarded,
            'user_notes': self.user_notes,
            'cluster_id': self.cluster_id,
            'cluster_confidence': self.cluster_confidence
        }

class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey('properties.id', ondelete='CASCADE'), nullable=False, index=True)
    price_usd = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    property = relationship('Property', back_populates='price_history')

class ScrapeJob(Base):
    __tablename__ = 'scrape_jobs'

    id = Column(Integer, primary_key=True, index=True)
    portal = Column(String(50), nullable=False)
    status = Column(String(50), default='pending') # 'pending', 'running', 'completed', 'failed'
    zone = Column(String(100), nullable=True)
    property_type = Column(String(50), nullable=True)
    items_found = Column(Integer, default=0)
    items_saved = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'portal': self.portal,
            'status': self.status,
            'zone': self.zone,
            'property_type': self.property_type,
            'items_found': self.items_found,
            'items_saved': self.items_saved,
            'message': self.message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None
        }
