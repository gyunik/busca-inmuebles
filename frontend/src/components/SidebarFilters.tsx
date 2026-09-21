import React, { useState } from 'react';
import { Filter, RotateCcw, DollarSign, Maximize2, Bed, Bath, Calendar, Layers, Check, Globe } from 'lucide-react';
import { FilterState, LocationCatalog, StatsSummary } from '../types/property';
import { MultiSelectNeighborhoods } from './MultiSelectNeighborhoods';

interface SidebarFiltersProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  catalog: LocationCatalog;
  stats: StatsSummary | null;
  totalFiltered: number;
}

export const SidebarFilters: React.FC<SidebarFiltersProps> = ({
  filters,
  onChange,
  catalog,
  stats,
  totalFiltered
}) => {
  // Local states for inputs before submitting
  const [minPriceInput, setMinPriceInput] = useState<string>(filters.min_price?.toString() || '');
  const [maxPriceInput, setMaxPriceInput] = useState<string>(filters.max_price?.toString() || '');
  const [minAreaInput, setMinAreaInput] = useState<string>(filters.min_area?.toString() || '');
  const [maxAreaInput, setMaxAreaInput] = useState<string>(filters.max_area?.toString() || '');

  const handlePropertyTypeToggle = (type: string) => {
    const current = filters.property_types;
    if (current.includes(type)) {
      onChange({ ...filters, property_types: current.filter((t) => t !== type), page: 1 });
    } else {
      onChange({ ...filters, property_types: [...current, type], page: 1 });
    }
  };

  const handlePortalToggle = (portal: string) => {
    const current = filters.portals;
    if (current.includes(portal)) {
      onChange({ ...filters, portals: current.filter((p) => p !== portal), page: 1 });
    } else {
      onChange({ ...filters, portals: [...current, portal], page: 1 });
    }
  };

  const handleApplyPrice = (e: React.FormEvent) => {
    e.preventDefault();
    onChange({
      ...filters,
      min_price: minPriceInput ? parseFloat(minPriceInput) : undefined,
      max_price: maxPriceInput ? parseFloat(maxPriceInput) : undefined,
      page: 1
    });
  };

  const handleApplyArea = (e: React.FormEvent) => {
    e.preventDefault();
    onChange({
      ...filters,
      min_area: minAreaInput ? parseFloat(minAreaInput) : undefined,
      max_area: maxAreaInput ? parseFloat(maxAreaInput) : undefined,
      page: 1
    });
  };

  const handleBedroomsClick = (num: number) => {
    if (filters.min_bedrooms === num) {
      // Toggle off
      onChange({ ...filters, min_bedrooms: undefined, page: 1 });
    } else {
      onChange({ ...filters, min_bedrooms: num, page: 1 });
    }
  };

  const handleBathroomsClick = (num: number) => {
    if (filters.min_bathrooms === num) {
      onChange({ ...filters, min_bathrooms: undefined, page: 1 });
    } else {
      onChange({ ...filters, min_bathrooms: num, page: 1 });
    }
  };

  const handleDaysAgoSelect = (days: number | undefined) => {
    onChange({ ...filters, days_ago: days, page: 1 });
  };

  const resetAllFilters = () => {
    setMinPriceInput('');
    setMaxPriceInput('');
    setMinAreaInput('');
    setMaxAreaInput('');
    onChange({
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
      page_size: 30
    });
  };

  const propertyTypeOptions = [
    { key: 'departamento', label: 'Departamentos', count: stats?.by_type?.departamento || 0 },
    { key: 'casa', label: 'Casas', count: stats?.by_type?.casa || 0 },
    { key: 'ph', label: 'PH', count: stats?.by_type?.ph || 0 }
  ];

  const portalOptions = [
    { key: 'mercadolibre', label: 'Mercado Libre', color: 'bg-amber-500', count: stats?.by_portal?.mercadolibre || 0 },
    { key: 'zonaprop', label: 'Zonaprop', color: 'bg-fuchsia-600', count: stats?.by_portal?.zonaprop || 0 },
    { key: 'argenprop', label: 'Argenprop', color: 'bg-blue-600', count: stats?.by_portal?.argenprop || 0 },
    { key: 'properati', label: 'Properati', color: 'bg-teal-600', count: stats?.by_portal?.properati || 0 }
  ];

  return (
    <aside className="w-full lg:w-72 bg-white rounded-lg border border-gray-200 p-4 shadow-xs space-y-5 text-gray-800 flex-shrink-0">
      
      {/* Top Title & Reset */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-200">
        <div className="flex items-center gap-1.5 font-bold text-base text-gray-900">
          <Filter className="w-4 h-4 text-blue-600" />
          <span>Filtros</span>
        </div>
        <button
          onClick={resetAllFilters}
          className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 font-medium hover:underline"
        >
          <RotateCcw className="w-3 h-3" />
          Limpiar
        </button>
      </div>

      {/* Duplicate Grouping Toggle */}
      <div className="bg-amber-50/80 border border-amber-200 rounded-lg p-3">
        <label className="flex items-start gap-2.5 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.group_duplicates}
            onChange={(e) => onChange({ ...filters, group_duplicates: e.target.checked, page: 1 })}
            className="mt-0.5 rounded text-blue-600 focus:ring-0 w-4 h-4"
          />
          <div>
            <span className="text-xs font-bold text-amber-950 block">Detección de Duplicados</span>
            <span className="text-[11px] text-amber-800 leading-tight block mt-0.5">
              Agrupa inmuebles iguales publicados en varios portales y destaca el mejor precio.
            </span>
          </div>
        </label>
      </div>

      {/* 1. Tipo de Inmueble (Departamentos, Casas, PH) */}
      <div>
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2">Inmueble</h3>
        <div className="space-y-1.5">
          {propertyTypeOptions.map((opt) => {
            const isChecked = filters.property_types.includes(opt.key);
            return (
              <label
                key={opt.key}
                className="flex items-center justify-between text-sm hover:text-blue-600 cursor-pointer group"
              >
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => handlePropertyTypeToggle(opt.key)}
                    className="rounded text-blue-600 focus:ring-0 w-4 h-4"
                  />
                  <span className={`${isChecked ? 'font-semibold text-blue-700' : 'text-gray-700'}`}>
                    {opt.label}
                  </span>
                </div>
                <span className="text-xs text-gray-400 group-hover:text-blue-500 font-normal">
                  ({opt.count})
                </span>
              </label>
            );
          })}
        </div>
      </div>

      <hr className="border-gray-200" />

      {/* 2. Multi-Select Barrios */}
      <MultiSelectNeighborhoods
        catalog={catalog}
        selectedNeighborhoods={filters.neighborhoods}
        onChange={(neighs) => onChange({ ...filters, neighborhoods: neighs, page: 1 })}
      />

      <hr className="border-gray-200" />

      {/* 3. Precio en Dólares (USD) */}
      <div>
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2 flex items-center gap-1">
          <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
          Precio (USD)
        </h3>
        
        {/* Quick price presets */}
        <div className="space-y-1 mb-2.5 text-xs">
          <button
            type="button"
            onClick={() => { setMinPriceInput(''); setMaxPriceInput('100000'); onChange({ ...filters, min_price: undefined, max_price: 100000, page: 1 }); }}
            className="block text-gray-600 hover:text-blue-600"
          >
            Hasta USD 100.000
          </button>
          <button
            type="button"
            onClick={() => { setMinPriceInput('100000'); setMaxPriceInput('200000'); onChange({ ...filters, min_price: 100000, max_price: 200000, page: 1 }); }}
            className="block text-gray-600 hover:text-blue-600"
          >
            USD 100.000 a USD 200.000
          </button>
          <button
            type="button"
            onClick={() => { setMinPriceInput('200000'); setMaxPriceInput(''); onChange({ ...filters, min_price: 200000, max_price: undefined, page: 1 }); }}
            className="block text-gray-600 hover:text-blue-600"
          >
            Más de USD 200.000
          </button>
        </div>

        <form onSubmit={handleApplyPrice} className="flex items-center gap-1.5">
          <input
            type="number"
            placeholder="Mínimo"
            value={minPriceInput}
            onChange={(e) => setMinPriceInput(e.target.value)}
            className="w-1/2 px-2.5 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
          <span className="text-gray-400 text-xs">-</span>
          <input
            type="number"
            placeholder="Máximo"
            value={maxPriceInput}
            onChange={(e) => setMaxPriceInput(e.target.value)}
            className="w-1/2 px-2.5 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
          <button
            type="submit"
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold px-2.5 py-1.5 text-xs rounded border border-gray-300 transition-colors"
          >
            →
          </button>
        </form>
      </div>

      <hr className="border-gray-200" />

      {/* 4. Metros Cuadrados (Superficie Total) */}
      <div>
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2 flex items-center gap-1">
          <Maximize2 className="w-3.5 h-3.5 text-blue-600" />
          Superficie Total (m²)
        </h3>
        <form onSubmit={handleApplyArea} className="flex items-center gap-1.5">
          <input
            type="number"
            placeholder="Mínimo"
            value={minAreaInput}
            onChange={(e) => setMinAreaInput(e.target.value)}
            className="w-1/2 px-2.5 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
          <span className="text-gray-400 text-xs">-</span>
          <input
            type="number"
            placeholder="Máximo"
            value={maxAreaInput}
            onChange={(e) => setMaxAreaInput(e.target.value)}
            className="w-1/2 px-2.5 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
          <button
            type="submit"
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold px-2.5 py-1.5 text-xs rounded border border-gray-300 transition-colors"
          >
            →
          </button>
        </form>
      </div>

      <hr className="border-gray-200" />

      {/* 5. Dormitorios */}
      <div>
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2 flex items-center gap-1">
          <Bed className="w-3.5 h-3.5 text-indigo-600" />
          Dormitorios
        </h3>
        <div className="grid grid-cols-4 gap-1.5">
          {[1, 2, 3, 4].map((num) => {
            const isSelected = filters.min_bedrooms === num;
            return (
              <button
                key={num}
                type="button"
                onClick={() => handleBedroomsClick(num)}
                className={`py-1.5 text-xs font-semibold rounded border transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {num === 4 ? '4+' : num}
              </button>
            );
          })}
        </div>
      </div>

      <hr className="border-gray-200" />

      {/* 6. Baños */}
      <div>
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2 flex items-center gap-1">
          <Bath className="w-3.5 h-3.5 text-cyan-600" />
          Baños
        </h3>
        <div className="grid grid-cols-3 gap-1.5">
          {[1, 2, 3].map((num) => {
            const isSelected = filters.min_bathrooms === num;
            return (
              <button
                key={num}
                type="button"
                onClick={() => handleBathroomsClick(num)}
                className={`py-1.5 text-xs font-semibold rounded border transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {num === 3 ? '3+' : `${num}+`}
              </button>
            );
          })}
        </div>
      </div>

      <hr className="border-gray-200" />

      {/* 7. Fecha de Publicación */}
      <div>
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2 flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5 text-rose-500" />
          Publicado
        </h3>
        <div className="space-y-1.5 text-xs">
          {[
            { label: 'Cualquier momento', days: undefined },
            { label: 'Últimas 24 horas', days: 1 },
            { label: 'Últimos 7 días', days: 7 },
            { label: 'Últimos 15 días', days: 15 },
            { label: 'Últimos 30 días', days: 30 }
          ].map((item, idx) => {
            const isSelected = filters.days_ago === item.days;
            return (
              <label
                key={idx}
                className="flex items-center gap-2 cursor-pointer hover:text-blue-600"
              >
                <input
                  type="radio"
                  name="days_ago"
                  checked={isSelected}
                  onChange={() => handleDaysAgoSelect(item.days)}
                  className="text-blue-600 focus:ring-0 w-3.5 h-3.5"
                />
                <span className={isSelected ? 'font-semibold text-blue-700' : 'text-gray-700'}>
                  {item.label}
                </span>
              </label>
            );
          })}
        </div>
      </div>

      <hr className="border-gray-200" />

      {/* 8. Portales de Origen */}
      <div>
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2 flex items-center gap-1">
          <Globe className="w-3.5 h-3.5 text-gray-600" />
          Portales
        </h3>
        <div className="space-y-1.5">
          {portalOptions.map((p) => {
            const isChecked = filters.portals.includes(p.key);
            return (
              <label
                key={p.key}
                className="flex items-center justify-between text-sm hover:text-blue-600 cursor-pointer group"
              >
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => handlePortalToggle(p.key)}
                    className="rounded text-blue-600 focus:ring-0 w-4 h-4"
                  />
                  <span className={`${isChecked ? 'font-semibold text-blue-700' : 'text-gray-700'}`}>
                    {p.label}
                  </span>
                </div>
                <span className="text-xs text-gray-400 group-hover:text-blue-500 font-normal">
                  ({p.count})
                </span>
              </label>
            );
          })}
        </div>
      </div>

    </aside>
  );
};
