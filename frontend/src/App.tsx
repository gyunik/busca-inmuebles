import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Property, FilterState, LocationCatalog, StatsSummary } from './types/property';
import { Navbar } from './components/Navbar';
import { SidebarFilters } from './components/SidebarFilters';
import { PropertyCard } from './components/PropertyCard';
import { ScrapeModal } from './components/ScrapeModal';
import { ArrowUpDown, AlertCircle, ChevronLeft, ChevronRight, Loader2, Sparkles, SlidersHorizontal } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000/api';

export const App: React.FC = () => {
  const [properties, setProperties] = useState<Property[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [catalog, setCatalog] = useState<LocationCatalog>({});
  const [stats, setStats] = useState<StatsSummary | null>(null);
  
  // UI Modals
  const [isScrapeModalOpen, setIsScrapeModalOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  // Filters State
  const [filters, setFilters] = useState<FilterState>({
    property_types: [],
    neighborhoods: [],
    zones: [],
    portals: [],
    min_price: undefined,
    max_price: undefined,
    min_area: undefined,
    max_area: undefined,
    min_bedrooms: undefined,
    max_bedrooms: undefined,
    min_bathrooms: undefined,
    days_ago: undefined,
    search_query: '',
    only_favorites: false,
    group_duplicates: false,
    sort_by: 'newest',
    page: 1,
    page_size: 20
  });

  const [searchInputValue, setSearchInputValue] = useState('');

  // Fetch Locations Catalog
  useEffect(() => {
    axios.get(`${API_BASE}/properties/catalog/locations`)
      .then(res => setCatalog(res.data))
      .catch(err => console.error('Error fetching catalog:', err));
  }, []);

  // Fetch Stats
  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/properties/stats/summary`);
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  // Fetch Properties based on filters
  const fetchProperties = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      filters.property_types.forEach(t => params.append('property_types', t));
      filters.neighborhoods.forEach(n => params.append('neighborhoods', n));
      filters.zones.forEach(z => params.append('zones', z));
      filters.portals.forEach(p => params.append('portals', p));
      
      if (filters.min_price !== undefined) params.append('min_price', filters.min_price.toString());
      if (filters.max_price !== undefined) params.append('max_price', filters.max_price.toString());
      if (filters.min_area !== undefined) params.append('min_area', filters.min_area.toString());
      if (filters.max_area !== undefined) params.append('max_area', filters.max_area.toString());
      if (filters.min_bedrooms !== undefined) params.append('min_bedrooms', filters.min_bedrooms.toString());
      if (filters.max_bedrooms !== undefined) params.append('max_bedrooms', filters.max_bedrooms.toString());
      if (filters.min_bathrooms !== undefined) params.append('min_bathrooms', filters.min_bathrooms.toString());
      if (filters.days_ago !== undefined) params.append('days_ago', filters.days_ago.toString());
      if (filters.search_query) params.append('search_query', filters.search_query);
      if (filters.only_favorites) params.append('only_favorites', 'true');
      if (filters.group_duplicates) params.append('group_duplicates', 'true');
      
      params.append('sort_by', filters.sort_by);
      params.append('page', filters.page.toString());
      params.append('page_size', filters.page_size.toString());

      const res = await axios.get(`${API_BASE}/properties?${params.toString()}`);
      setProperties(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (err) {
      console.error('Error fetching properties:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchProperties();
  }, [fetchProperties]);

  // Search input handlers
  const handleSearchSubmit = () => {
    setFilters(prev => ({ ...prev, search_query: searchInputValue, page: 1 }));
  };

  // Toggle favorite
  const handleToggleFavorite = async (id: number) => {
    try {
      const res = await axios.post(`${API_BASE}/properties/${id}/favorite`);
      setProperties(prev => prev.map(p => p.id === id ? { ...p, is_favorite: res.data.is_favorite } : p));
      fetchStats();
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  };

  // Toggle discard
  const handleToggleDiscard = async (id: number) => {
    try {
      await axios.post(`${API_BASE}/properties/${id}/discard`);
      setProperties(prev => prev.filter(p => p.id !== id));
      setTotal(prev => Math.max(prev - 1, 0));
      fetchStats();
    } catch (err) {
      console.error('Error discarding property:', err);
    }
  };

  // Save notes
  const handleSaveNotes = async (id: number, notes: string) => {
    try {
      const res = await axios.post(`${API_BASE}/properties/${id}/notes`, { notes });
      setProperties(prev => prev.map(p => p.id === id ? { ...p, user_notes: res.data.user_notes } : p));
    } catch (err) {
      console.error('Error saving notes:', err);
    }
  };

  // Export to Excel
  const handleExportExcel = async () => {
    setIsExporting(true);
    try {
      const params = new URLSearchParams();
      filters.property_types.forEach(t => params.append('property_types', t));
      filters.neighborhoods.forEach(n => params.append('neighborhoods', n));
      filters.zones.forEach(z => params.append('zones', z));
      filters.portals.forEach(p => params.append('portals', p));
      if (filters.min_price !== undefined) params.append('min_price', filters.min_price.toString());
      if (filters.max_price !== undefined) params.append('max_price', filters.max_price.toString());
      if (filters.min_area !== undefined) params.append('min_area', filters.min_area.toString());
      if (filters.max_area !== undefined) params.append('max_area', filters.max_area.toString());
      if (filters.min_bedrooms !== undefined) params.append('min_bedrooms', filters.min_bedrooms.toString());
      if (filters.min_bathrooms !== undefined) params.append('min_bathrooms', filters.min_bathrooms.toString());
      if (filters.days_ago !== undefined) params.append('days_ago', filters.days_ago.toString());
      if (filters.search_query) params.append('search_query', filters.search_query);
      if (filters.only_favorites) params.append('only_favorites', 'true');

      const response = await axios.get(`${API_BASE}/export/excel?${params.toString()}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `inmuebles_exportados_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error exporting excel:', err);
      alert('Hubo un problema al generar el archivo Excel.');
    } finally {
      setIsExporting(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setFilters(prev => ({ ...prev, page: newPage }));
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#ededed] flex flex-col font-sans">
      
      {/* Top Navbar */}
      <Navbar
        searchQuery={searchInputValue}
        onSearchChange={setSearchInputValue}
        onSearchSubmit={handleSearchSubmit}
        stats={stats}
        onlyFavorites={filters.only_favorites}
        onToggleFavorites={() => setFilters(prev => ({ ...prev, only_favorites: !prev.only_favorites, page: 1 }))}
        onOpenScrapeModal={() => setIsScrapeModalOpen(true)}
        onExportExcel={handleExportExcel}
        isExporting={isExporting}
      />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full flex-1">
        
        {/* Mobile Filter Toggle */}
        <div className="lg:hidden mb-4">
          <button
            onClick={() => setShowMobileFilters(!showMobileFilters)}
            className="w-full bg-white border border-gray-300 py-2.5 px-4 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 shadow-xs"
          >
            <SlidersHorizontal className="w-4 h-4 text-blue-600" />
            <span>{showMobileFilters ? 'Ocultar Filtros' : 'Mostrar Filtros y Barrios'}</span>
          </button>
        </div>

        <div className="flex flex-col lg:flex-row gap-6 items-start">
          
          {/* Left Sidebar Filters */}
          <div className={`${showMobileFilters ? 'block' : 'hidden'} lg:block w-full lg:w-72`}>
            <SidebarFilters
              filters={filters}
              onChange={setFilters}
              catalog={catalog}
              stats={stats}
              totalFiltered={total}
            />
          </div>

          {/* Right Content Area: Results */}
          <div className="flex-1 w-full space-y-4">
            
            {/* Results Header & Sorting */}
            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h1 className="text-xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
                  <span>Inmuebles en Venta</span>
                  {filters.group_duplicates && (
                    <span className="text-xs bg-amber-100 text-amber-900 px-2 py-0.5 rounded-full font-semibold border border-amber-300">
                      Duplicados agrupados
                    </span>
                  )}
                </h1>
                <p className="text-xs text-gray-500 mt-0.5">
                  <strong className="text-gray-800">{total.toLocaleString()}</strong> resultados encontrados
                  {filters.neighborhoods.length > 0 && ` en ${filters.neighborhoods.join(', ')}`}
                </p>
              </div>

              {/* Sort Selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 font-medium whitespace-nowrap flex items-center gap-1">
                  <ArrowUpDown className="w-3.5 h-3.5 text-gray-400" />
                  Ordenar por:
                </span>
                <select
                  value={filters.sort_by}
                  onChange={(e) => setFilters(prev => ({ ...prev, sort_by: e.target.value, page: 1 }))}
                  className="bg-gray-50 border border-gray-300 text-gray-800 text-xs rounded-md px-3 py-1.5 focus:ring-1 focus:ring-blue-500 focus:outline-none font-medium"
                >
                  <option value="newest">Más recientes</option>
                  <option value="price_asc">Menor precio (USD)</option>
                  <option value="price_desc">Mayor precio (USD)</option>
                  <option value="price_m2_asc">Menor valor por m² (USD/m²)</option>
                  <option value="price_m2_desc">Mayor valor por m² (USD/m²)</option>
                  <option value="area_desc">Mayor superficie (m²)</option>
                </select>
              </div>
            </div>

            {/* Loading Indicator */}
            {loading ? (
              <div className="bg-white rounded-lg border border-gray-200 p-12 flex flex-col items-center justify-center text-gray-500 shadow-xs">
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin mb-3" />
                <p className="text-sm font-semibold text-gray-700">Buscando inmuebles en la base de datos...</p>
                <p className="text-xs text-gray-400 mt-1">Filtrando portales y deduplicando resultados</p>
              </div>
            ) : properties.length === 0 ? (
              /* Empty State */
              <div className="bg-white rounded-lg border border-gray-200 p-12 text-center shadow-xs space-y-3">
                <div className="w-12 h-12 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center mx-auto">
                  <AlertCircle className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-gray-900">No encontramos inmuebles con esos filtros</h3>
                <p className="text-xs text-gray-500 max-w-md mx-auto">
                  Probá ampliando el rango de precios, seleccionando más barrios o quitando algunos criterios de búsqueda.
                </p>
                <div className="pt-2">
                  <button
                    onClick={() => setFilters(prev => ({
                      ...prev,
                      property_types: [],
                      neighborhoods: [],
                      min_price: undefined,
                      max_price: undefined,
                      min_bedrooms: undefined,
                      search_query: '',
                      only_favorites: false,
                      page: 1
                    }))}
                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-md shadow-xs transition-colors"
                  >
                    Restablecer filtros principales
                  </button>
                </div>
              </div>
            ) : (
              /* Property Cards List */
              <div className="space-y-3">
                {properties.map((property) => (
                  <PropertyCard
                    key={property.id}
                    property={property}
                    onToggleFavorite={handleToggleFavorite}
                    onToggleDiscard={handleToggleDiscard}
                    onSaveNotes={handleSaveNotes}
                  />
                ))}
              </div>
            )}

            {/* Pagination Controls */}
            {!loading && totalPages > 1 && (
              <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-xs flex items-center justify-between mt-6">
                <div className="text-xs text-gray-500">
                  Página <strong>{filters.page}</strong> de <strong>{totalPages}</strong> ({total} inmuebles)
                </div>
                
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handlePageChange(filters.page - 1)}
                    disabled={filters.page <= 1}
                    className="p-1.5 rounded border border-gray-300 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed text-gray-700"
                    title="Página anterior"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    let pageNum = i + 1;
                    if (totalPages > 5 && filters.page > 3) {
                      pageNum = filters.page - 2 + i;
                      if (pageNum > totalPages) pageNum = totalPages - (4 - i);
                    }
                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`w-8 h-8 rounded text-xs font-semibold transition-colors ${
                          filters.page === pageNum
                            ? 'bg-blue-600 text-white'
                            : 'border border-gray-300 hover:bg-gray-100 text-gray-700'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}

                  <button
                    onClick={() => handlePageChange(filters.page + 1)}
                    disabled={filters.page >= totalPages}
                    className="p-1.5 rounded border border-gray-300 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed text-gray-700"
                    title="Página siguiente"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

          </div>

        </div>

      </main>

      {/* Scrape Management Modal */}
      <ScrapeModal
        isOpen={isScrapeModalOpen}
        onClose={() => setIsScrapeModalOpen(false)}
        onScrapeCompleted={() => {
          fetchProperties();
          fetchStats();
        }}
      />

    </div>
  );
};

export default App;
