import os
from pathlib import Path

target = Path("backend/app/static/index.html")
target.parent.mkdir(parents=True, exist_ok=True)
p1 = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Busca Inmuebles | Agregador CABA & GBA</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
  <style>
    body { background-color: #ededed; color: #333333; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; }
    ::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 3px; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    const { useState, useEffect, useCallback } = React;
    const API_BASE = '/api';

    function App() {
      const [properties, setProperties] = useState([]);
      const [total, setTotal] = useState(0);
      const [totalPages, setTotalPages] = useState(1);
      const [loading, setLoading] = useState(true);
      const [catalog, setCatalog] = useState({});
      const [stats, setStats] = useState(null);
      const [isScrapeModalOpen, setIsScrapeModalOpen] = useState(false);
      const [isExporting, setIsExporting] = useState(false);

      const [filters, setFilters] = useState({
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

      useEffect(() => {
        axios.get(API_BASE + '/properties/catalog/locations').then(res => setCatalog(res.data)).catch(console.error);
      }, []);

      const fetchStats = useCallback(async () => {
        try {
          const res = await axios.get(API_BASE + '/properties/stats/summary');
          setStats(res.data);
        } catch (err) {
          console.error(err);
        }
      }, []);

      useEffect(() => { fetchStats(); }, [fetchStats]);

      const fetchProperties = useCallback(async () => {
        setLoading(true);
        try {
          const params = new URLSearchParams();
          filters.property_types.forEach(t => params.append('property_types', t));
          filters.neighborhoods.forEach(n => params.append('neighborhoods', n));
          filters.zones.forEach(z => params.append('zones', z));
          filters.portals.forEach(p => params.append('portals', p));
          if (filters.min_price !== undefined) params.append('min_price', filters.min_price);
          if (filters.max_price !== undefined) params.append('max_price', filters.max_price);
          if (filters.min_area !== undefined) params.append('min_area', filters.min_area);
          if (filters.max_area !== undefined) params.append('max_area', filters.max_area);
          if (filters.min_bedrooms !== undefined) params.append('min_bedrooms', filters.min_bedrooms);
          if (filters.min_bathrooms !== undefined) params.append('min_bathrooms', filters.min_bathrooms);
          if (filters.days_ago !== undefined) params.append('days_ago', filters.days_ago);
          if (filters.search_query) params.append('search_query', filters.search_query);
          if (filters.only_favorites) params.append('only_favorites', 'true');
          if (filters.group_duplicates) params.append('group_duplicates', 'true');
          params.append('sort_by', filters.sort_by);
          params.append('page', filters.page);
          params.append('page_size', filters.page_size);

          const res = await axios.get(API_BASE + '/properties?' + params.toString());
          setProperties(res.data.items);
          setTotal(res.data.total);
          setTotalPages(res.data.total_pages);
        } catch (err) {
          console.error(err);
        } finally {
          setLoading(false);
        }
      }, [filters]);

      useEffect(() => { fetchProperties(); }, [fetchProperties]);
"""
p2 = """
      const handleSearchSubmit = () => {
        setFilters(prev => ({ ...prev, search_query: searchInputValue, page: 1 }));
      };

      const handleToggleFavorite = async (id) => {
        try {
          const res = await axios.post(API_BASE + '/properties/' + id + '/favorite');
          setProperties(prev => prev.map(p => p.id === id ? { ...p, is_favorite: res.data.is_favorite } : p));
          fetchStats();
        } catch (err) { console.error(err); }
      };

      const handleToggleDiscard = async (id) => {
        try {
          await axios.post(API_BASE + '/properties/' + id + '/discard');
          setProperties(prev => prev.filter(p => p.id !== id));
          setTotal(prev => Math.max(prev - 1, 0));
          fetchStats();
        } catch (err) { console.error(err); }
      };

      const handleSaveNotes = async (id, notes) => {
        try {
          const res = await axios.post(API_BASE + '/properties/' + id + '/notes', { notes });
          setProperties(prev => prev.map(p => p.id === id ? { ...p, user_notes: res.data.user_notes } : p));
        } catch (err) { console.error(err); }
      };

      const handleExportExcel = async () => {
        setIsExporting(true);
        try {
          const params = new URLSearchParams();
          filters.property_types.forEach(t => params.append('property_types', t));
          filters.neighborhoods.forEach(n => params.append('neighborhoods', n));
          filters.portals.forEach(p => params.append('portals', p));
          if (filters.min_price !== undefined) params.append('min_price', filters.min_price);
          if (filters.max_price !== undefined) params.append('max_price', filters.max_price);
          if (filters.search_query) params.append('search_query', filters.search_query);

          const response = await axios.get(API_BASE + '/export/excel?' + params.toString(), { responseType: 'blob' });
          const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
          const downloadUrl = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = 'inmuebles_exportados_' + new Date().toISOString().slice(0, 10) + '.xlsx';
          document.body.appendChild(link);
          link.click();
          link.remove();
        } catch (err) {
          alert('Error al exportar archivo Excel');
        } finally {
          setIsExporting(false);
        }
      };

      return (
        <div className="min-h-screen bg-[#ededed] flex flex-col font-sans">
          <header className="bg-[#FFE600] border-b border-yellow-300 shadow-sm sticky top-0 z-40">
            <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.location.reload()}>
                <div className="bg-[#2D3277] text-white p-2 rounded-lg font-black text-xl flex items-center gap-1 shadow-sm">
                  <span>🏢 Busca<span className="text-yellow-400">Inmuebles</span></span>
                </div>
                <span className="hidden md:inline-block text-xs font-semibold bg-blue-100 text-blue-900 px-2 py-0.5 rounded-full uppercase">
                  CABA & GBA
                </span>
              </div>

              <div className="flex-1 max-w-2xl flex shadow-sm rounded bg-white border focus-within:ring-2 focus-within:ring-blue-500 overflow-hidden">
                <input
                  type="text"
                  value={searchInputValue}
                  onChange={(e) => setSearchInputValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
                  placeholder="Buscar por barrio, calle, inmobiliaria (ej. Palermo 3 amb, Ramos Mejía)..."
                  className="w-full px-4 py-2 text-sm text-gray-800 focus:outline-none"
                />
                <button onClick={handleSearchSubmit} className="px-4 bg-white hover:bg-gray-50 text-gray-600 border-l font-bold">
                  🔍
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button onClick={() => setIsScrapeModalOpen(true)} className="bg-white hover:bg-gray-50 text-xs font-semibold px-3 py-2 rounded border shadow-sm">
                  🔄 Escanear Portales
                </button>
                <button onClick={handleExportExcel} disabled={isExporting} className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-2 rounded shadow-sm disabled:opacity-50">
                  📊 {isExporting ? 'Exportando...' : 'Exportar Excel'}
                </button>
                <button
                  onClick={() => setFilters(prev => ({ ...prev, only_favorites: !prev.only_favorites, page: 1 }))}
                  className={'text-xs font-semibold px-3 py-2 rounded border shadow-sm ' + (filters.only_favorites ? 'bg-rose-500 text-white' : 'bg-white text-gray-800')}
                >
                  ⭐ Favoritos ({stats?.total_favorites || 0})
                </button>
              </div>
            </div>
            <div className="bg-white/80 border-t px-4 py-1 text-xs text-gray-600 flex justify-between">
              <div>
                <strong>{stats?.total_properties || 0}</strong> inmuebles en base de datos · 
                <span className="text-amber-700 font-semibold ml-1">Mercado Libre ({stats?.by_portal?.mercadolibre || 0})</span>, 
                <span className="text-fuchsia-700 font-semibold ml-1">Zonaprop ({stats?.by_portal?.zonaprop || 0})</span>, 
                <span className="text-blue-700 font-semibold ml-1">Argenprop ({stats?.by_portal?.argenprop || 0})</span>, 
                <span className="text-teal-700 font-semibold ml-1">Properati ({stats?.by_portal?.properati || 0})</span>
              </div>
            </div>
          </header>

          <main className="max-w-7xl mx-auto px-4 py-6 w-full flex-1 flex flex-col lg:flex-row gap-6 items-start">
            <aside className="w-full lg:w-72 bg-white rounded-lg border p-4 space-y-4 flex-shrink-0 text-xs">
              <div className="flex justify-between items-center border-b pb-2">
                <span className="font-bold text-sm text-gray-900">Filtros</span>
                <button onClick={() => setFilters({ property_types: [], neighborhoods: [], zones: [], portals: [], sort_by: 'newest', page: 1, page_size: 20 })} className="text-blue-600 hover:underline">
                  Limpiar
                </button>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded p-2.5">
                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.group_duplicates}
                    onChange={(e) => setFilters(prev => ({ ...prev, group_duplicates: e.target.checked, page: 1 }))}
                    className="mt-0.5 rounded text-blue-600"
                  />
                  <div>
                    <span className="font-bold text-amber-950 block">Detección de Duplicados</span>
                    <span className="text-amber-800 text-[11px] block">Agrupa avisos idénticos y resalta el mejor precio.</span>
                  </div>
                </label>
              </div>

              <div>
                <h4 className="font-bold text-gray-700 uppercase mb-2">Inmueble</h4>
                {['departamento', 'casa', 'ph'].map(t => (
                  <label key={t} className="flex items-center justify-between py-0.5 cursor-pointer hover:text-blue-600">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={filters.property_types.includes(t)}
                        onChange={() => {
                          const curr = filters.property_types;
                          setFilters(prev => ({ ...prev, property_types: curr.includes(t) ? curr.filter(x => x !== t) : [...curr, t], page: 1 }));
                        }}
                      />
                      <span className="capitalize font-medium">{t === 'ph' ? 'PH' : t + 's'}</span>
                    </div>
                    <span className="text-gray-400">({stats?.by_type?.[t] || 0})</span>
                  </label>
                ))}
              </div>

              <hr />

              <NeighborhoodSelector
                catalog={catalog}
                selected={filters.neighborhoods}
                onChange={(neighs) => setFilters(prev => ({ ...prev, neighborhoods: neighs, page: 1 }))}
              />

              <hr />

              <div>
                <h4 className="font-bold text-gray-700 uppercase mb-2">Precio (USD)</h4>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    placeholder="Mín"
                    defaultValue={filters.min_price || ''}
                    onBlur={(e) => setFilters(prev => ({ ...prev, min_price: e.target.value ? parseFloat(e.target.value) : undefined, page: 1 }))}
                    className="w-1/2 p-1 border rounded"
                  />
                  <span>-</span>
                  <input
                    type="number"
                    placeholder="Máx"
                    defaultValue={filters.max_price || ''}
                    onBlur={(e) => setFilters(prev => ({ ...prev, max_price: e.target.value ? parseFloat(e.target.value) : undefined, page: 1 }))}
                    className="w-1/2 p-1 border rounded"
                  />
                </div>
              </div>

              <hr />

              <div>
                <h4 className="font-bold text-gray-700 uppercase mb-2">Superficie Total (m²)</h4>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    placeholder="Mín m²"
                    defaultValue={filters.min_area || ''}
                    onBlur={(e) => setFilters(prev => ({ ...prev, min_area: e.target.value ? parseFloat(e.target.value) : undefined, page: 1 }))}
                    className="w-1/2 p-1 border rounded"
                  />
                  <span>-</span>
                  <input
                    type="number"
                    placeholder="Máx m²"
                    defaultValue={filters.max_area || ''}
                    onBlur={(e) => setFilters(prev => ({ ...prev, max_area: e.target.value ? parseFloat(e.target.value) : undefined, page: 1 }))}
                    className="w-1/2 p-1 border rounded"
                  />
                </div>
              </div>

              <hr />

              <div>
                <h4 className="font-bold text-gray-700 uppercase mb-2">Dormitorios</h4>
                <div className="grid grid-cols-4 gap-1">
                  {[1, 2, 3, 4].map(num => (
                    <button
                      key={num}
                      type="button"
                      onClick={() => setFilters(prev => ({ ...prev, min_bedrooms: prev.min_bedrooms === num ? undefined : num, page: 1 }))}
                      className={'py-1 font-semibold rounded border ' + (filters.min_bedrooms === num ? 'bg-blue-600 text-white' : 'bg-white hover:bg-gray-50')}
                    >
                      {num === 4 ? '4+' : num}
                    </button>
                  ))}
                </div>
              </div>

              <hr />

              <div>
                <h4 className="font-bold text-gray-700 uppercase mb-2">Baños</h4>
                <div className="grid grid-cols-3 gap-1">
                  {[1, 2, 3].map(num => (
                    <button
                      key={num}
                      type="button"
                      onClick={() => setFilters(prev => ({ ...prev, min_bathrooms: prev.min_bathrooms === num ? undefined : num, page: 1 }))}
                      className={'py-1 font-semibold rounded border ' + (filters.min_bathrooms === num ? 'bg-blue-600 text-white' : 'bg-white hover:bg-gray-50')}
                    >
                      {num === 3 ? '3+' : num + '+'}
                    </button>
                  ))}
                </div>
              </div>

              <hr />

              <div>
                <h4 className="font-bold text-gray-700 uppercase mb-2">Portales</h4>
                {['mercadolibre', 'zonaprop', 'argenprop', 'properati'].map(p => (
                  <label key={p} className="flex items-center justify-between py-0.5 cursor-pointer hover:text-blue-600">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={filters.portals.includes(p)}
                        onChange={() => {
                          const curr = filters.portals;
                          setFilters(prev => ({ ...prev, portals: curr.includes(p) ? curr.filter(x => x !== p) : [...curr, p], page: 1 }));
                        }}
                      />
                      <span className="capitalize">{p === 'mercadolibre' ? 'Mercado Libre' : p}</span>
                    </div>
                    <span className="text-gray-400">({stats?.by_portal?.[p] || 0})</span>
                  </label>
                ))}
              </div>

            </aside>

            <div className="flex-1 w-full space-y-4">
              <div className="bg-white p-4 rounded-lg border flex flex-col sm:flex-row justify-between items-center gap-3">
                <div>
                  <h1 className="text-lg font-bold text-gray-900">Inmuebles en Venta</h1>
                  <p className="text-xs text-gray-500"><strong>{total.toLocaleString()}</strong> resultados encontrados</p>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span>Ordenar por:</span>
                  <select
                    value={filters.sort_by}
                    onChange={(e) => setFilters(prev => ({ ...prev, sort_by: e.target.value, page: 1 }))}
                    className="border rounded p-1 font-semibold bg-gray-50"
                  >
                    <option value="newest">Más recientes</option>
                    <option value="price_asc">Menor precio (USD)</option>
                    <option value="price_desc">Mayor precio (USD)</option>
                    <option value="price_m2_asc">Menor valor por m²</option>
                    <option value="price_m2_desc">Mayor valor por m²</option>
                    <option value="area_desc">Mayor superficie (m²)</option>
                  </select>
                </div>
              </div>

              {loading ? (
                <div className="bg-white rounded-lg border p-12 text-center text-gray-500 font-semibold">
                  Cargando inmuebles...
                </div>
              ) : properties.length === 0 ? (
                <div className="bg-white rounded-lg border p-12 text-center text-gray-500 space-y-2">
                  <div className="text-3xl">🏠</div>
                  <h3 className="font-bold">No se encontraron inmuebles con esos filtros</h3>
                </div>
              ) : (
                <div className="space-y-3">
                  {properties.map(p => (
                    <PropertyItem
                      key={p.id}
                      property={p}
                      onToggleFavorite={handleToggleFavorite}
                      onToggleDiscard={handleToggleDiscard}
                      onSaveNotes={handleSaveNotes}
                    />
                  ))}
                </div>
              )}

              {!loading && totalPages > 1 && (
                <div className="bg-white p-3 rounded-lg border flex justify-between items-center text-xs">
                  <div>Página {filters.page} de {totalPages}</div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => setFilters(prev => ({ ...prev, page: Math.max(prev.page - 1, 1) }))}
                      disabled={filters.page <= 1}
                      className="px-3 py-1 border rounded disabled:opacity-40"
                    >
                      Anterior
                    </button>
                    <button
                      onClick={() => setFilters(prev => ({ ...prev, page: Math.min(prev.page + 1, totalPages) }))}
                      disabled={filters.page >= totalPages}
                      className="px-3 py-1 border rounded disabled:opacity-40"
                    >
                      Siguiente
                    </button>
                  </div>
                </div>
              )}
            </div>
          </main>

          {isScrapeModalOpen && (
            <ScrapeModalComponent
              isOpen={isScrapeModalOpen}
              onClose={() => setIsScrapeModalOpen(false)}
              onCompleted={() => { fetchProperties(); fetchStats(); }}
            />
          )}
        </div>
      );
    }
"""
p3 = """
    function NeighborhoodSelector({ catalog, selected, onChange }) {
      const [isOpen, setIsOpen] = useState(false);
      const [search, setSearch] = useState('');
      const [activeZone, setActiveZone] = useState('CABA');
      const zones = Object.keys(catalog);

      const toggleNeigh = (n) => {
        onChange(selected.includes(n) ? selected.filter(x => x !== n) : [...selected, n]);
      };

      return (
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="font-bold text-gray-700 uppercase">Barrios</label>
            {selected.length > 0 && (
              <button onClick={() => onChange([])} className="text-blue-600 hover:underline">
                Limpiar ({selected.length})
              </button>
            )}
          </div>
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="w-full bg-white border rounded p-1.5 text-left flex justify-between items-center"
          >
            <span>{selected.length === 0 ? 'Seleccionar barrios...' : selected.length + ' seleccionados'}</span>
            <span>{isOpen ? '▲' : '▼'}</span>
          </button>
          {selected.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1 max-h-20 overflow-y-auto p-1 bg-gray-50 rounded border">
              {selected.map(n => (
                <span key={n} className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border text-[11px] flex items-center gap-1">
                  {n}
                  <button onClick={() => toggleNeigh(n)} className="font-bold">×</button>
                </span>
              ))}
            </div>
          )}
          {isOpen && (
            <div className="mt-2 p-2 bg-white border rounded shadow-lg">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar barrio..."
                className="w-full p-1 border rounded mb-2"
              />
              {!search && (
                <div className="flex border-b mb-2 overflow-x-auto text-[11px]">
                  {zones.map(z => (
                    <button
                      key={z}
                      onClick={() => setActiveZone(z)}
                      className={'px-2 py-0.5 font-semibold border-b-2 ' + (activeZone === z ? 'border-blue-600 text-blue-600' : 'text-gray-500')}
                    >
                      {z}
                    </button>
                  ))}
                </div>
              )}
              <div className="max-h-36 overflow-y-auto space-y-1">
                {(catalog[activeZone] || []).filter(n => !search || n.toLowerCase().includes(search.toLowerCase())).map(n => (
                  <label key={n} className="flex items-center gap-1.5 p-0.5 hover:bg-gray-50 rounded cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selected.includes(n)}
                      onChange={() => toggleNeigh(n)}
                      className="rounded text-blue-600"
                    />
                    <span>{n}</span>
                  </label>
                ))}
              </div>
              <div className="mt-2 pt-1 border-t flex justify-end">
                <button onClick={() => setIsOpen(false)} className="bg-blue-600 text-white px-2 py-0.5 rounded">Listo</button>
              </div>
            </div>
          )}
        </div>
      );
    }

    function PropertyItem({ property, onToggleFavorite, onToggleDiscard, onSaveNotes }) {
      const [showDups, setShowDups] = useState(false);
      const [isEditingNote, setIsEditingNote] = useState(false);
      const [noteText, setNoteText] = useState(property.user_notes || '');

      const portalBadges = {
        mercadolibre: 'bg-amber-100 text-amber-900 border-amber-300',
        zonaprop: 'bg-fuchsia-100 text-fuchsia-900 border-fuchsia-300',
        argenprop: 'bg-blue-100 text-blue-900 border-blue-300',
        properati: 'bg-teal-100 text-teal-900 border-teal-300'
      };

      const defaultImg = 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80';
      const displayImg = (property.images && property.images.length > 0) ? property.images[0] : defaultImg;
      const dups = property.duplicates || [];

      return (
        <div className="bg-white rounded-lg border shadow-xs overflow-hidden flex flex-col md:flex-row hover:shadow-md transition-shadow">
          <div className="relative md:w-60 h-44 md:h-auto bg-gray-100 flex-shrink-0">
            <img src={displayImg} alt={property.title} className="w-full h-full object-cover" />
            <div className="absolute top-2 left-2 flex flex-col gap-1">
              <span className={'text-[10px] font-bold px-2 py-0.5 rounded border ' + (portalBadges[property.portal] || 'bg-gray-100')}>
                {property.portal === 'mercadolibre' ? 'Mercado Libre' : property.portal}
              </span>
              <span className="text-[10px] font-bold uppercase bg-black/70 text-white px-1.5 py-0.5 rounded">
                {property.property_type}
              </span>
            </div>
            <button
              onClick={() => onToggleFavorite(property.id)}
              className="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full shadow hover:scale-110"
            >
              {property.is_favorite ? '⭐' : '🤍'}
            </button>
            {property.price_per_m2 && (
              <div className="absolute bottom-2 left-2 bg-slate-900/80 text-white text-[11px] font-semibold px-2 py-0.5 rounded">
                USD {Math.round(property.price_per_m2).toLocaleString()}/m²
              </div>
            )}
          </div>

          <div className="p-4 flex-1 flex flex-col justify-between text-xs">
            <div>
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-2xl font-black text-gray-900">
                    USD {property.price_usd?.toLocaleString()}
                  </div>
                  <div className="font-semibold text-gray-700 mt-0.5">
                    📍 {property.neighborhood}, {property.zone} {property.address && '· ' + property.address}
                  </div>
                </div>
              </div>

              <h3 className="font-medium text-gray-800 line-clamp-1 mt-1 text-sm">{property.title}</h3>

              <div className="flex flex-wrap items-center gap-3 mt-3 text-gray-600">
                {property.total_area_m2 && <span className="bg-gray-100 px-2 py-1 rounded">📐 <strong>{Math.round(property.total_area_m2)}</strong> m²</span>}
                {property.bedrooms !== null && <span className="bg-gray-100 px-2 py-1 rounded">🛏️ <strong>{property.bedrooms}</strong> dorm.</span>}
                {property.bathrooms !== null && <span className="bg-gray-100 px-2 py-1 rounded">🚿 <strong>{property.bathrooms}</strong> baños</span>}
                {property.seller_name && <span className="text-gray-500 ml-auto">🏢 {property.seller_name}</span>}
              </div>

              <div className="mt-2">
                {isEditingNote ? (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={noteText}
                      onChange={(e) => setNoteText(e.target.value)}
                      placeholder="Agregar nota..."
                      className="w-full p-1 border rounded text-xs"
                    />
                    <button onClick={() => { onSaveNotes(property.id, noteText); setIsEditingNote(false); }} className="bg-blue-600 text-white px-2 py-0.5 rounded">
                      Guardar
                    </button>
                  </div>
                ) : (
                  <div className="flex justify-between items-center">
                    {property.user_notes ? (
                      <span className="bg-amber-50 text-amber-900 border border-amber-200 px-2 py-0.5 rounded italic">
                        Nota: {property.user_notes}
                      </span>
                    ) : <span />}
                    <button onClick={() => setIsEditingNote(true)} className="text-gray-400 hover:text-blue-600 ml-auto">
                      {property.user_notes ? '✏️ Editar nota' : '+ Agregar nota'}
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-3 pt-2 border-t flex justify-between items-center">
              {dups.length > 1 ? (
                <button
                  onClick={() => setShowDups(!showDups)}
                  className="bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 px-2.5 py-1 rounded font-bold flex items-center gap-1"
                >
                  {dups.length} portales detectados {showDups ? '▲' : '▼'}
                </button>
              ) : (
                <span className="text-gray-400 text-[11px]">Publicación única</span>
              )}

              <div className="flex items-center gap-2">
                <button onClick={() => onToggleDiscard(property.id)} className="p-1 text-gray-400 hover:text-rose-600" title="Descartar">
                  🗑️
                </button>
                <a
                  href={property.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-3 py-1.5 rounded shadow-xs flex items-center gap-1"
                >
                  Ver en portal ↗
                </a>
              </div>
            </div>

            {dups.length > 1 && showDups && (
              <div className="mt-3 p-2 bg-amber-50 rounded border border-amber-200 space-y-1">
                <div className="font-bold text-amber-950">Publicaciones detectadas para este inmueble:</div>
                {dups.map((d, i) => (
                  <div key={i} className="flex justify-between items-center bg-white p-1.5 rounded border border-amber-200">
                    <span className="font-bold uppercase text-[10px]">{d.portal}</span>
                    <span className="font-bold">USD {d.price_usd?.toLocaleString()}</span>
                    <span className="text-gray-500 truncate max-w-[120px]">{d.seller_name}</span>
                    <a href={d.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 font-bold hover:underline">
                      Abrir enlace ↗
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      );
    }

    function ScrapeModalComponent({ isOpen, onClose, onCompleted }) {
      const [portal, setPortal] = useState('all');
      const [jobs, setJobs] = useState([]);
      const [msg, setMsg] = useState(null);

      useEffect(() => {
        axios.get('/api/scrape/jobs').then(res => setJobs(res.data)).catch(console.error);
      }, []);

      const startScrape = async () => {
        setMsg('Iniciando escaneo...');
        try {
          await axios.post('/api/scrape/start', { portal });
          setMsg('Escaneo en ejecución en segundo plano.');
          setTimeout(onCompleted, 2000);
        } catch (err) {
          setMsg('Error al iniciar');
        }
      };

      const runDedup = async () => {
        try {
          const res = await axios.post('/api/scrape/deduplicate');
          setMsg(res.data.message);
          onCompleted();
        } catch (err) {
          setMsg('Error');
        }
      };

      return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-5 space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <h2 className="font-bold text-base text-gray-900">Escanear y Actualizar Portales</h2>
              <button onClick={onClose} className="text-gray-500 font-bold text-lg">×</button>
            </div>
            {msg && <div className="p-2 bg-blue-50 text-blue-800 text-xs rounded border border-blue-200">{msg}</div>}
            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Seleccionar Portal</label>
              <select value={portal} onChange={(e) => setPortal(e.target.value)} className="w-full text-xs border rounded p-2">
                <option value="all">Todos los Portales (Mercado Libre, Zonaprop, Argenprop, Properati)</option>
                <option value="mercadolibre">Mercado Libre</option>
                <option value="zonaprop">Zonaprop</option>
                <option value="argenprop">Argenprop</option>
                <option value="properati">Properati</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button onClick={startScrape} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded text-xs">
                ▶ Iniciar Escaneo
              </button>
              <button onClick={runDedup} className="bg-amber-600 hover:bg-amber-700 text-white font-bold py-2 px-3 rounded text-xs">
                Detectar Duplicados
              </button>
            </div>
            <div className="pt-2 border-t">
              <h4 className="text-xs font-bold text-gray-700 mb-2">Historial de Escaneos</h4>
              <div className="max-h-32 overflow-y-auto space-y-1 text-xs">
                {jobs.map(j => (
                  <div key={j.id} className="p-1.5 bg-gray-50 rounded border flex justify-between">
                    <span className="font-bold capitalize">{j.portal}</span>
                    <span className="text-gray-500">{j.message || j.status}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex justify-end pt-2 border-t">
              <button onClick={onClose} className="bg-gray-200 px-4 py-1.5 rounded text-xs font-semibold">Cerrar</button>
            </div>
          </div>
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""

full_content = p1 + p2 + p3
with open(target, "w", encoding="utf-8") as f:
    f.write(full_content)

print(f"Generated static UI file at {target.resolve()} ({len(full_content)} bytes)")
p3_updated = """
    function NeighborhoodSelector({ catalog, selected, onChange }) {
      const [isOpen, setIsOpen] = useState(false);
      const [search, setSearch] = useState('');
      const [activeZone, setActiveZone] = useState('CABA');
      const zones = Object.keys(catalog);

      const toggleNeigh = (n) => {
        onChange(selected.includes(n) ? selected.filter(x => x !== n) : [...selected, n]);
      };

      return (
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="font-bold text-gray-700 uppercase">Barrios</label>
            {selected.length > 0 && (
              <button onClick={() => onChange([])} className="text-blue-600 hover:underline">
                Limpiar ({selected.length})
              </button>
            )}
          </div>
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="w-full bg-white border rounded p-1.5 text-left flex justify-between items-center"
          >
            <span>{selected.length === 0 ? 'Seleccionar barrios...' : selected.length + ' seleccionados'}</span>
            <span>{isOpen ? '▲' : '▼'}</span>
          </button>
          {selected.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1 max-h-20 overflow-y-auto p-1 bg-gray-50 rounded border">
              {selected.map(n => (
                <span key={n} className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border text-[11px] flex items-center gap-1">
                  {n}
                  <button onClick={() => toggleNeigh(n)} className="font-bold">×</button>
                </span>
              ))}
            </div>
          )}
          {isOpen && (
            <div className="mt-2 p-2 bg-white border rounded shadow-lg">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar barrio..."
                className="w-full p-1 border rounded mb-2"
              />
              {!search && (
                <div className="flex border-b mb-2 overflow-x-auto text-[11px]">
                  {zones.map(z => (
                    <button
                      key={z}
                      onClick={() => setActiveZone(z)}
                      className={'px-2 py-0.5 font-semibold border-b-2 ' + (activeZone === z ? 'border-blue-600 text-blue-600' : 'text-gray-500')}
                    >
                      {z}
                    </button>
                  ))}
                </div>
              )}
              <div className="max-h-36 overflow-y-auto space-y-1">
                {(catalog[activeZone] || []).filter(n => !search || n.toLowerCase().includes(search.toLowerCase())).map(n => (
                  <label key={n} className="flex items-center gap-1.5 p-0.5 hover:bg-gray-50 rounded cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selected.includes(n)}
                      onChange={() => toggleNeigh(n)}
                      className="rounded text-blue-600"
                    />
                    <span>{n}</span>
                  </label>
                ))}
              </div>
              <div className="mt-2 pt-1 border-t flex justify-end">
                <button onClick={() => setIsOpen(false)} className="bg-blue-600 text-white px-2 py-0.5 rounded">Listo</button>
              </div>
            </div>
          )}
        </div>
      );
    }

    function PropertyItem({ property, onToggleFavorite, onToggleDiscard, onSaveNotes }) {
      const [showDups, setShowDups] = useState(false);
      const [isEditingNote, setIsEditingNote] = useState(false);
      const [noteText, setNoteText] = useState(property.user_notes || '');

      const portalBadges = {
        mercadolibre: 'bg-amber-100 text-amber-900 border-amber-300',
        zonaprop: 'bg-fuchsia-100 text-fuchsia-900 border-fuchsia-300',
        argenprop: 'bg-blue-100 text-blue-900 border-blue-300',
        properati: 'bg-teal-100 text-teal-900 border-teal-300'
      };

      const defaultImg = 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80';
      const displayImg = (property.images && property.images.length > 0) ? property.images[0] : defaultImg;
      const dups = property.duplicates || [];

      return (
        <div className="bg-white rounded-lg border shadow-xs overflow-hidden flex flex-col md:flex-row hover:shadow-md transition-shadow">
          <div className="relative md:w-60 h-44 md:h-auto bg-gray-100 flex-shrink-0">
            <img src={displayImg} alt={property.title} className="w-full h-full object-cover" />
            <div className="absolute top-2 left-2 flex flex-col gap-1">
              <span className={'text-[10px] font-bold px-2 py-0.5 rounded border ' + (portalBadges[property.portal] || 'bg-gray-100')}>
                {property.portal === 'mercadolibre' ? 'Mercado Libre' : property.portal}
              </span>
              <span className="text-[10px] font-bold uppercase bg-black/70 text-white px-1.5 py-0.5 rounded">
                {property.property_type}
              </span>
            </div>
            <button
              onClick={() => onToggleFavorite(property.id)}
              className="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full shadow hover:scale-110"
            >
              {property.is_favorite ? '⭐' : '🤍'}
            </button>
            {property.price_per_m2 && (
              <div className="absolute bottom-2 left-2 bg-slate-900/80 text-white text-[11px] font-semibold px-2 py-0.5 rounded">
                USD {Math.round(property.price_per_m2).toLocaleString()}/m²
              </div>
            )}
          </div>

          <div className="p-4 flex-1 flex flex-col justify-between text-xs">
            <div>
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-2xl font-black text-gray-900">
                    USD {property.price_usd?.toLocaleString()}
                  </div>
                  <div className="font-semibold text-gray-700 mt-0.5">
                    📍 {property.neighborhood}, {property.zone} {property.address && '· ' + property.address}
                  </div>
                </div>
              </div>

              <h3 className="font-medium text-gray-800 line-clamp-1 mt-1 text-sm">{property.title}</h3>

              <div className="flex flex-wrap items-center gap-3 mt-3 text-gray-600">
                {property.total_area_m2 && <span className="bg-gray-100 px-2 py-1 rounded">📐 <strong>{Math.round(property.total_area_m2)}</strong> m²</span>}
                {property.bedrooms !== null && <span className="bg-gray-100 px-2 py-1 rounded">🛏️ <strong>{property.bedrooms}</strong> dorm.</span>}
                {property.bathrooms !== null && <span className="bg-gray-100 px-2 py-1 rounded">🚿 <strong>{property.bathrooms}</strong> baños</span>}
                {property.seller_name && <span className="text-gray-500 ml-auto">🏢 {property.seller_name}</span>}
              </div>

              <div className="mt-2">
                {isEditingNote ? (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={noteText}
                      onChange={(e) => setNoteText(e.target.value)}
                      placeholder="Agregar nota..."
                      className="w-full p-1 border rounded text-xs"
                    />
                    <button onClick={() => { onSaveNotes(property.id, noteText); setIsEditingNote(false); }} className="bg-blue-600 text-white px-2 py-0.5 rounded">
                      Guardar
                    </button>
                  </div>
                ) : (
                  <div className="flex justify-between items-center">
                    {property.user_notes ? (
                      <span className="bg-amber-50 text-amber-900 border border-amber-200 px-2 py-0.5 rounded italic">
                        Nota: {property.user_notes}
                      </span>
                    ) : <span />}
                    <button onClick={() => setIsEditingNote(true)} className="text-gray-400 hover:text-blue-600 ml-auto">
                      {property.user_notes ? '✏️ Editar nota' : '+ Agregar nota'}
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-3 pt-2 border-t flex justify-between items-center">
              {dups.length > 1 ? (
                <button
                  onClick={() => setShowDups(!showDups)}
                  className="bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 px-2.5 py-1 rounded font-bold flex items-center gap-1"
                >
                  {dups.length} portales detectados {showDups ? '▲' : '▼'}
                </button>
              ) : (
                <span className="text-gray-400 text-[11px]">Publicación única</span>
              )}

              <div className="flex items-center gap-2">
                <button onClick={() => onToggleDiscard(property.id)} className="p-1 text-gray-400 hover:text-rose-600" title="Descartar">
                  🗑️
                </button>
                <a
                  href={property.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-3 py-1.5 rounded shadow-xs flex items-center gap-1"
                >
                  Ver en portal ↗
                </a>
              </div>
            </div>

            {dups.length > 1 && showDups && (
              <div className="mt-3 p-2 bg-amber-50 rounded border border-amber-200 space-y-1">
                <div className="font-bold text-amber-950">Publicaciones detectadas para este inmueble:</div>
                {dups.map((d, i) => (
                  <div key={i} className="flex justify-between items-center bg-white p-1.5 rounded border border-amber-200">
                    <span className="font-bold uppercase text-[10px]">{d.portal}</span>
                    <span className="font-bold">USD {d.price_usd?.toLocaleString()}</span>
                    <span className="text-gray-500 truncate max-w-[120px]">{d.seller_name}</span>
                    <a href={d.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 font-bold hover:underline">
                      Abrir enlace ↗
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      );
    }

    function ScrapeModalComponent({ isOpen, onClose, onCompleted }) {
      const [portal, setPortal] = useState('all');
      const [jobs, setJobs] = useState([]);
      const [msg, setMsg] = useState(null);
      const [isBusy, setIsBusy] = useState(false);

      const fetchJobs = () => {
        axios.get('/api/scrape/jobs')
          .then(res => setJobs(res.data))
          .catch(console.error);
      };

      useEffect(() => {
        fetchJobs();
        const interval = setInterval(fetchJobs, 2000);
        return () => clearInterval(interval);
      }, []);

      const startScrape = async () => {
        setIsBusy(true);
        setMsg('Iniciando escaneo en segundo plano...');
        try {
          await axios.post('/api/scrape/start', { portal });
          fetchJobs();
          setTimeout(() => {
            fetchJobs();
            onCompleted();
            setIsBusy(false);
          }, 3000);
        } catch (err) {
          setMsg('Error al iniciar escaneo');
          setIsBusy(false);
        }
      };

      const runDedup = async () => {
        try {
          const res = await axios.post('/api/scrape/deduplicate');
          setMsg(res.data.message);
          onCompleted();
        } catch (err) {
          setMsg('Error al ejecutar deduplicación');
        }
      };

      return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-5 space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <h2 className="font-bold text-base text-gray-900">Escanear y Actualizar Portales</h2>
              <button onClick={onClose} className="text-gray-500 font-bold text-lg">×</button>
            </div>

            {msg && <div className="p-2 bg-blue-50 text-blue-800 text-xs rounded border border-blue-200">{msg}</div>}

            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Seleccionar Portal</label>
              <select value={portal} onChange={(e) => setPortal(e.target.value)} className="w-full text-xs border rounded p-2">
                <option value="all">Todos los Portales (Mercado Libre, Zonaprop, Argenprop, Properati)</option>
                <option value="mercadolibre">Mercado Libre</option>
                <option value="zonaprop">Zonaprop</option>
                <option value="argenprop">Argenprop</option>
                <option value="properati">Properati</option>
              </select>
            </div>

            <div className="flex gap-2">
              <button
                onClick={startScrape}
                disabled={isBusy}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded text-xs disabled:opacity-50"
              >
                {isBusy ? '⏳ Escaneando...' : '▶ Iniciar Escaneo'}
              </button>
              <button
                onClick={runDedup}
                className="bg-amber-600 hover:bg-amber-700 text-white font-bold py-2 px-3 rounded text-xs"
              >
                Detectar Duplicados
              </button>
            </div>

            <div className="pt-2 border-t">
              <div className="flex justify-between items-center mb-2">
                <h4 className="text-xs font-bold text-gray-700">Historial de Escaneos</h4>
                <button onClick={fetchJobs} className="text-[11px] text-blue-600 hover:underline">Actualizar</button>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1.5 text-xs">
                {jobs.map(j => (
                  <div key={j.id} className="p-2 bg-gray-50 rounded border flex justify-between items-center">
                    <div>
                      <span className="font-bold capitalize">{j.portal}</span>
                      <div className="text-gray-500 text-[11px]">{j.message || j.status}</div>
                    </div>
                    <span className={'px-2 py-0.5 rounded text-[10px] font-bold ' + (j.status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800 animate-pulse')}>
                      {j.status === 'completed' ? '✓ Listo' : '⏳ ' + j.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t">
              <button onClick={onClose} className="bg-gray-200 px-4 py-1.5 rounded text-xs font-semibold">Cerrar</button>
            </div>
          </div>
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""

full_content = p1 + p2 + p3_updated
with open("backend/app/static/index.html", "w", encoding="utf-8") as f:
    f.write(full_content)
print("Updated static index.html with live polling modal successfully.")
