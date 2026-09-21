import React, { useState } from 'react';
import { Heart, ExternalLink, Trash2, MapPin, Maximize2, Bed, Bath, Clock, Building, ChevronDown, ChevronUp, Edit3, Check } from 'lucide-react';
import { Property } from '../types/property';

interface PropertyCardProps {
  property: Property;
  onToggleFavorite: (id: number) => void;
  onToggleDiscard: (id: number) => void;
  onSaveNotes: (id: number, notes: string) => void;
}

export const PropertyCard: React.FC<PropertyCardProps> = ({
  property,
  onToggleFavorite,
  onToggleDiscard,
  onSaveNotes
}) => {
  const [showDuplicates, setShowDuplicates] = useState(false);
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [noteText, setNoteText] = useState(property.user_notes || '');

  const portalConfig: Record<string, { name: string; bg: string; text: string; border: string }> = {
    mercadolibre: { name: 'Mercado Libre', bg: 'bg-amber-100', text: 'text-amber-900', border: 'border-amber-300' },
    zonaprop: { name: 'Zonaprop', bg: 'bg-fuchsia-100', text: 'text-fuchsia-900', border: 'border-fuchsia-300' },
    argenprop: { name: 'Argenprop', bg: 'bg-blue-100', text: 'text-blue-900', border: 'border-blue-300' },
    properati: { name: 'Properati', bg: 'bg-teal-100', text: 'text-teal-900', border: 'border-teal-300' }
  };

  const portalInfo = portalConfig[property.portal] || {
    name: property.portal,
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    border: 'border-gray-300'
  };

  const formattedPrice = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(property.price_usd);

  const formattedExpenses = property.expenses && property.expenses > 0
    ? new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(property.expenses)
    : null;

  const defaultImg = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80";
  const displayImage = (property.images && property.images.length > 0 && property.images[0]) ? property.images[0] : defaultImg;

  // Format publication date
  const getPubText = (dateStr?: string) => {
    if (!dateStr) return 'Reciente';
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'Hoy';
    if (diffDays === 1) return 'Ayer';
    if (diffDays < 30) return `Hace ${diffDays} días`;
    return date.toLocaleDateString('es-AR', { day: '2-digit', month: 'short' });
  };

  const handleSaveNote = () => {
    onSaveNotes(property.id, noteText);
    setIsEditingNotes(false);
  };

  const duplicatesList = property.duplicates || [];
  const hasDuplicates = duplicatesList.length > 1;

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-xs hover:shadow-md transition-shadow overflow-hidden flex flex-col md:flex-row">
      
      {/* Image Thumbnail */}
      <div className="relative md:w-64 h-48 md:h-auto flex-shrink-0 bg-gray-100 overflow-hidden">
        <img
          src={displayImage}
          alt={property.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onError={(e) => { (e.target as HTMLImageElement).src = defaultImg; }}
        />
        
        {/* Portal Badge */}
        <div className="absolute top-2 left-2 flex flex-col gap-1">
          <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md shadow-xs border ${portalInfo.bg} ${portalInfo.text} ${portalInfo.border}`}>
            {portalInfo.name}
          </span>
          <span className="text-[10px] font-bold uppercase bg-black/70 text-white px-2 py-0.5 rounded backdrop-blur-xs">
            {property.property_type}
          </span>
        </div>

        {/* Favorite Button */}
        <button
          onClick={() => onToggleFavorite(property.id)}
          className="absolute top-2 right-2 p-1.5 bg-white/90 hover:bg-white rounded-full shadow-md transition-transform hover:scale-110"
          title={property.is_favorite ? "Quitar de favoritos" : "Guardar como favorito"}
        >
          <Heart className={`w-4 h-4 ${property.is_favorite ? 'fill-rose-500 text-rose-500' : 'text-gray-500'}`} />
        </button>

        {/* Price/m2 Badge */}
        {property.price_per_m2 && (
          <div className="absolute bottom-2 left-2 bg-slate-900/80 text-white text-[11px] font-semibold px-2 py-0.5 rounded backdrop-blur-xs">
            USD {Math.round(property.price_per_m2).toLocaleString()}/m²
          </div>
        )}
      </div>

      {/* Main Details */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          
          {/* Price & Location Header */}
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-gray-900 tracking-tight">
                  {formattedPrice}
                </span>
                {formattedExpenses && (
                  <span className="text-xs text-gray-500 font-medium">
                    + {formattedExpenses} expensas
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1 text-sm font-semibold text-gray-700 mt-0.5">
                <MapPin className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />
                <span>{property.neighborhood}, {property.zone}</span>
                {property.address && <span className="text-gray-400 font-normal">· {property.address}</span>}
              </div>
            </div>

            {/* Publication Date */}
            <div className="flex items-center gap-1 text-[11px] text-gray-500 flex-shrink-0 bg-gray-50 px-2 py-1 rounded border border-gray-100">
              <Clock className="w-3 h-3 text-gray-400" />
              <span>{getPubText(property.publication_date)}</span>
            </div>
          </div>

          {/* Title */}
          <h3 className="text-sm font-medium text-gray-800 line-clamp-1 mt-1.5" title={property.title}>
            {property.title}
          </h3>

          {/* Key Attributes Pills */}
          <div className="flex flex-wrap items-center gap-3 mt-3 text-xs text-gray-600">
            {property.total_area_m2 && (
              <span className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded font-medium text-gray-700">
                <Maximize2 className="w-3.5 h-3.5 text-gray-500" />
                <strong>{Math.round(property.total_area_m2)}</strong> m² totales
              </span>
            )}
            {property.bedrooms !== undefined && property.bedrooms !== null && (
              <span className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded font-medium text-gray-700">
                <Bed className="w-3.5 h-3.5 text-gray-500" />
                <strong>{property.bedrooms}</strong> {property.bedrooms === 1 ? 'dormitorio' : 'dormitorios'}
              </span>
            )}
            {property.bathrooms !== undefined && property.bathrooms !== null && (
              <span className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded font-medium text-gray-700">
                <Bath className="w-3.5 h-3.5 text-gray-500" />
                <strong>{property.bathrooms}</strong> {property.bathrooms === 1 ? 'baño' : 'baños'}
              </span>
            )}
            {property.seller_name && (
              <span className="flex items-center gap-1 text-gray-500 ml-auto truncate max-w-[180px]" title={property.seller_name}>
                <Building className="w-3.5 h-3.5 text-gray-400" />
                <span className="truncate">{property.seller_name}</span>
              </span>
            )}
          </div>

          {/* User Notes Section */}
          <div className="mt-2.5">
            {isEditingNotes ? (
              <div className="flex items-center gap-2 mt-1">
                <input
                  type="text"
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Agregar nota personal (ej. Llamar a inmobiliaria los martes)..."
                  className="w-full text-xs px-2.5 py-1 border border-blue-400 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  autoFocus
                />
                <button
                  onClick={handleSaveNote}
                  className="bg-blue-600 hover:bg-blue-700 text-white p-1 rounded text-xs"
                  title="Guardar nota"
                >
                  <Check className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between text-xs">
                {property.user_notes ? (
                  <p className="text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 italic line-clamp-1">
                    Nota: {property.user_notes}
                  </p>
                ) : (
                  <span />
                )}
                <button
                  onClick={() => setIsEditingNotes(true)}
                  className="text-gray-400 hover:text-blue-600 text-[11px] flex items-center gap-1 ml-auto"
                >
                  <Edit3 className="w-3 h-3" />
                  {property.user_notes ? 'Editar nota' : '+ Agregar nota'}
                </button>
              </div>
            )}
          </div>

        </div>

        {/* Bottom Actions & Duplicates Trigger */}
        <div className="mt-3 pt-2.5 border-t border-gray-100 flex items-center justify-between">
          
          {/* Duplicate Banner / Toggle */}
          {hasDuplicates ? (
            <button
              onClick={() => setShowDuplicates(!showDuplicates)}
              className="text-xs bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 px-2.5 py-1 rounded-md font-semibold flex items-center gap-1.5 transition-colors"
            >
              <span>{duplicatesList.length} publicaciones detectadas</span>
              {showDuplicates ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          ) : (
            <span className="text-[11px] text-gray-400">Publicación única</span>
          )}

          {/* Right Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onToggleDiscard(property.id)}
              className="p-1.5 text-gray-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
              title="Descartar inmueble"
            >
              <Trash2 className="w-4 h-4" />
            </button>

            <a
              href={property.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-1.5 rounded-md shadow-xs transition-colors"
            >
              <span>Ver en {portalInfo.name}</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

        </div>

        {/* Expanded Duplicates Comparison Box */}
        {hasDuplicates && showDuplicates && (
          <div className="mt-3 p-3 bg-amber-50/70 border border-amber-200 rounded-md text-xs space-y-2">
            <div className="font-bold text-amber-950 flex items-center justify-between">
              <span>Comparación entre portales e inmobiliarias:</span>
              <span className="text-[11px] font-normal text-amber-800">
                Mejor precio: <strong>USD {Math.min(...duplicatesList.map(d => d.price_usd)).toLocaleString()}</strong>
              </span>
            </div>
            
            <div className="space-y-1.5">
              {duplicatesList.map((dup, idx) => {
                const dPortal = portalConfig[dup.portal] || { name: dup.portal, bg: 'bg-gray-100', text: 'text-gray-800' };
                return (
                  <div key={idx} className="flex items-center justify-between bg-white p-2 rounded border border-amber-200/60 shadow-2xs">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${dPortal.bg} ${dPortal.text}`}>
                        {dPortal.name}
                      </span>
                      <span className="font-bold text-gray-900">
                        USD {dup.price_usd.toLocaleString()}
                      </span>
                      {dup.seller_name && (
                        <span className="text-gray-500 text-[11px] truncate max-w-[140px]">
                          ({dup.seller_name})
                        </span>
                      )}
                    </div>
                    <a
                      href={dup.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1 text-[11px]"
                    >
                      Abrir enlace <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
