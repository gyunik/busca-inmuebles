import React from 'react';
import { Search, Heart, RefreshCw, FileSpreadsheet, Home, Building2, Layers } from 'lucide-react';
import { StatsSummary } from '../types/property';

interface NavbarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSearchSubmit: () => void;
  stats: StatsSummary | null;
  onlyFavorites: boolean;
  onToggleFavorites: () => void;
  onOpenScrapeModal: () => void;
  onExportExcel: () => void;
  isExporting: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  searchQuery,
  onSearchChange,
  onSearchSubmit,
  stats,
  onlyFavorites,
  onToggleFavorites,
  onOpenScrapeModal,
  onExportExcel,
  isExporting
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onSearchSubmit();
    }
  };

  return (
    <header className="bg-ml-yellow border-b border-yellow-300 shadow-sm sticky top-0 z-40">
      {/* Main Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between gap-4">
          
          {/* Logo / Brand */}
          <div className="flex items-center gap-2 flex-shrink-0 cursor-pointer" onClick={() => window.location.reload()}>
            <div className="bg-ml-navy text-white p-2 rounded-lg font-black text-xl tracking-tight flex items-center gap-1.5 shadow-sm">
              <Building2 className="w-6 h-6 text-ml-yellow" />
              <span>Busca<span className="text-yellow-400">Inmuebles</span></span>
            </div>
            <span className="hidden md:inline-block text-xs font-semibold bg-blue-100 text-blue-900 px-2 py-0.5 rounded-full uppercase tracking-wider">
              Multicanal CABA & GBA
            </span>
          </div>

          {/* Search Bar */}
          <div className="flex-1 max-w-2xl relative">
            <div className="flex shadow-sm rounded-md overflow-hidden bg-white border border-gray-200 focus-within:ring-2 focus-within:ring-blue-500">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Buscar por barrio, calle, inmobiliaria o características (ej. Palermo 3 ambientes)..."
                className="w-full px-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none"
              />
              <button
                onClick={onSearchSubmit}
                className="bg-white hover:bg-gray-50 text-gray-500 hover:text-blue-600 px-4 flex items-center justify-center border-l border-gray-200 transition-colors"
                title="Buscar"
              >
                <Search className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Scrape Portals Button */}
            <button
              onClick={onOpenScrapeModal}
              className="flex items-center gap-1.5 bg-white hover:bg-gray-50 text-gray-800 text-xs font-semibold px-3 py-2 rounded-md border border-gray-300 shadow-sm transition-all"
              title="Escanear y actualizar portales"
            >
              <RefreshCw className="w-4 h-4 text-blue-600" />
              <span className="hidden sm:inline">Escanear Portales</span>
            </button>

            {/* Export Excel Button */}
            <button
              onClick={onExportExcel}
              disabled={isExporting}
              className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-2 rounded-md shadow-sm transition-all disabled:opacity-50"
              title="Descargar listado en Excel con enlaces"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span className="hidden sm:inline">{isExporting ? 'Exportando...' : 'Exportar Excel'}</span>
            </button>

            {/* Favorites Toggle */}
            <button
              onClick={onToggleFavorites}
              className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-md border shadow-sm transition-all ${
                onlyFavorites
                  ? 'bg-rose-500 text-white border-rose-600'
                  : 'bg-white hover:bg-gray-50 text-gray-800 border-gray-300'
              }`}
            >
              <Heart className={`w-4 h-4 ${onlyFavorites ? 'fill-white' : 'text-rose-500'}`} />
              <span className="hidden sm:inline">Favoritos</span>
              {stats && stats.total_favorites > 0 && (
                <span className={`px-1.5 py-0.2 text-[11px] rounded-full font-bold ${
                  onlyFavorites ? 'bg-white text-rose-600' : 'bg-rose-100 text-rose-700'
                }`}>
                  {stats.total_favorites}
                </span>
              )}
            </button>
          </div>

        </div>
      </div>

      {/* Sub Header - Quick Stats */}
      <div className="bg-white/80 backdrop-blur-xs border-t border-yellow-200/80 px-4 sm:px-6 lg:px-8 py-1.5 text-xs text-gray-600 flex items-center justify-between overflow-x-auto">
        <div className="flex items-center gap-4 flex-nowrap">
          <span className="flex items-center gap-1 font-medium text-gray-700">
            <Home className="w-3.5 h-3.5 text-gray-400" />
            Total: <strong className="text-gray-900">{stats?.total_properties.toLocaleString() || '...'}</strong> inmuebles
          </span>
          <span className="text-gray-300">|</span>
          <span className="text-gray-600">
            Portales: <span className="font-semibold text-amber-700">Mercado Libre ({stats?.by_portal?.mercadolibre || 0})</span>, 
            <span className="font-semibold text-fuchsia-700 ml-1">Zonaprop ({stats?.by_portal?.zonaprop || 0})</span>, 
            <span className="font-semibold text-blue-700 ml-1">Argenprop ({stats?.by_portal?.argenprop || 0})</span>, 
            <span className="font-semibold text-teal-700 ml-1">Properati ({stats?.by_portal?.properati || 0})</span>
          </span>
        </div>
        <div className="text-gray-500 hidden md:block">
          CABA: {stats?.by_zone?.CABA || 0} | GBA: {((stats?.by_zone?.['GBA Norte'] || 0) + (stats?.by_zone?.['GBA Sur'] || 0) + (stats?.by_zone?.['GBA Oeste'] || 0))}
        </div>
      </div>
    </header>
  );
};
